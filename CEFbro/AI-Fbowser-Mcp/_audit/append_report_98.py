# -*- coding: utf-8 -*-
"""追加报告第 98 节(第82轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 98. 第82轮：修掉「插装把页面搞崩」——自递归 + 我自己引入的 var 捕获 bug（判别性 A/B 7/7）"
        "＋ 该类缺陷全库共 6 处（已修默认那 1 处）")

SECTION = """

---

%s

### 98.1 缺陷：`browser_reverse_instrument`（transparent）会把页面搞崩

实测症状（历史轮次已记录，本轮再次复现）：用过该工具后，同页**后续任何 JS** 都可能崩：

```
JS异常:RangeError: Maximum call stack size exceeded
    at __obj.<computed> (<anonymous>:1:544)
    at __obj.<computed> (<anonymous>:1:588)   (同一列反复自递归)
```

这正是用户描述的"连续失败、反复换方法"的一个源头：页面被搞坏后，**所有**后续工具都会连带失败。

**静态根因（只读复核给出，我逐条复核确认）**：注入的包装器在**日志路径**上使用了会被它自己包装的内建方法，
而这三者都在默认目标表里：

| 日志路径里的写法 | 命中的默认目标 |
|---|---|
| `__results.push({...})` | `Array.prototype.push` |
| `Array.prototype.slice.call(arguments)` | `Function.prototype.call` |
| `__orig.apply(this,arguments)` | `Function.prototype.apply` |

于是"记录一次调用 → 进入 push/call 的包装器 → 包装器又要记录 → …"无限递归；
且 `__count++` 写在递归语句**之后**，永远执行不到，`__max=500` 上限也就永不生效。

**附带次生缺陷（静态确定）**：`calls:__count` 是**安装瞬间的值快照**，恒为 0 —— 即使递归修好也永远是 0。

### 98.2 修法：日志路径不再触碰任何可能被包装的原型方法

- 安装前捕获 `String.prototype.split` / `substring` / `Function.prototype.toString`；
- 一律用 **`Reflect.apply`** 调用（它是 `Reflect` 的静态方法，不在 `Function.prototype` 上，故不会被包装）；
- 数组用**索引赋值** `__results[__results.length]=…` 代替 `push`；
- 结构用普通 `for` 循环；
- `calls` 改为 **getter 实时读** `__count`（修掉快照恒 0）；
- 每个包装器挂 `__wrapper.__mcp_orig = __orig` —— 这是后续"卸载/还原"入口的**必要前提**
  （原来原函数只留在不可达的闭包里，只能靠刷新页面恢复）。

### 98.3 我在这条修法上自己踩的两个坑（都靠测量抓出来，如实记录）

**坑 1：把 `forEach` 回调换成普通 `for` 循环 → 引入经典 var 捕获 bug。**
`var __t/__obj/__orig/__method` 都是**函数作用域**，所有包装器闭包共享同一份，循环结束后它们指向
**最后一个目标**的原始函数。实测三个"怪值"由此全部得到解释：

| 调用 | 实际发生 | 观测结果 |
|---|---|---|
| `a.push(1,2,3)` | `charAt.call(a,1,2)` | `len:0`（a 没被改） |
| `Array.prototype.slice.call(a,1)` | `charAt.call(sliceFn,a,1)` → `ToString(sliceFn)` 后取第 0 字符 | `"f"` |
| `f.apply(null,[41])` | `charAt.call(f,null)` | `"f"` |

原实现用 `__targets.forEach(function(__t){…})` —— **回调本身就是一次函数调用，天然每轮独立作用域**，
所以原本没有这个 bug；是我替换它时引入的。
**修法**：循环体改用**显式 IIFE 传参**保证逐轮独立，且不依赖 `forEach`（用户可能把 `forEach` 列为目标）。
> 这个坑特别值得记：它**不崩、只把结果悄悄改错**，比崩栈危险得多。若当时只验"不再崩"，就会把
> 一个"静默改坏页面语义"的版本当成修好了发出去。

**坑 2：改用捕获的 `Function.prototype.call` 去调用 → 在本环境根本不成立。**
最小复现（`_audit/diag_captured_call.py`）：

| 探针 | 结果 |
|---|---|
| `var a=Function.prototype.call; …; return a+'|'+s` | 正常（两个都是 function） |
| `var a=Function.prototype.call; a(fn,null,'V')`（`fn` 是**普通函数**） | `TypeError: a is not a function` |
| `Reflect.apply(s,'a.b.c',['.'])` | 正常返回 `["a","b","c"]` |

即"把 `Function.prototype.call` 存进变量再调用"在这个 CEF 环境里不可用（连普通函数都调不了），
而 `Reflect.apply` 正常。**故最终一律走 `Reflect.apply`**，不再捕获 call/apply。
（顺带纠正了姊妹复核报告里 `__push.call(__results, entry)` 的建议 —— `.call` 本身就是默认目标之一，
等于把递归换个位置；已按"索引赋值"实现。）

### 98.4 判别性 A/B 验收：7/7

`_audit/verify_instrument_recursion_fix.py` —— **不需要旧二进制**：臂 A 把**旧模板原文**在当前页面
内联求值，直接复现缺陷；两臂之间强制重载清场（臂 A 会把页面搞坏，不清就会污染臂 B）。

| 判据 | 结果 |
|---|---|
| 基线（未插装）该 JS 正常 | `{"len":3,"r":[2,3],"y":42}` |
| **臂 A** 旧模板 → 页面被搞坏 | `RangeError: Maximum call stack size exceeded`（复现缺陷）|
| 清场后基线恢复 | 通过 |
| **臂 B** 新版工具 → 同一段 JS 正常返回 | `{"len":3,"r":[2,3],"y":42}` ✔ |
| 插装**确实在工作**（防"修成啥也不干"） | `instrumented=6, calls=3` |
| `__mcp_orig` 已挂（卸载入口前提） | `typeof Array.prototype.push.__mcp_orig == "function"` |
| 收尾重载后插装清除 | 通过 |

其中"插装确实在工作"这一条是关键对照：**只证明"不再崩"是不够的** ——
第一版（有 var 捕获 bug 时）"不崩"也成立，但那是**因为页面语义被改坏**。

### 98.5 该类缺陷全库共 **6 处**，本轮只修了"默认即触发"的 1 处

只读复核给出全量清单（46 个注入位点，15 个真正安装包装器）：

| 类别 | 位置 | 状态 |
|---|---|---|
| **A. 默认参数即递归**（不开参数就中招） | `Core` `browser_reverse_instrument` transparent | ✅ **本轮已修** |
| **B. 参数门控即递归**（用户列了这些 target 才中招） | `browser_reverse_hook` type=function_call（含 `console.log` 自指这条独立通路，且该族连计数器都没有）／`browser_kernel_reverse_trace`（另一个 guard-after）／`browser_reverse_hook_multi`（**安装期就崩**：装好 push 包装器后紧接 `found.push(name)`） | ❌ 待修 |
| **C. 读路径第二雷区** | `browser_reverse_hook_logs` 的 query 分支（`push`/`slice`）；其中一处是 `__mcp_instrument_results` 的**唯一服务端读路径** | ❌ 待修（注意：clear 分支是**刻意做成安全**的，勿"统一风格"改坏） |
| **D. 跨族 POSSIBLE（约 30 位点）** | transparent 一旦装上，其它族的 `push/apply/call/indexOf/charAt` 全进包装器；Kernel 探针的 `catch(e){}` 会把 `RangeError` **吞成静默无数据** | 随 A 修复后风险大降 |

### 98.6 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | 269/312 已测 |
| 通过 | **227**，把实例卡死 0，失败性质 `CAPABILITY` = 0 |
| 本轮修复 | 1 个**页面级破坏性**缺陷（自递归）+ 1 个次生缺陷（`calls` 恒 0）+ 消除我自引入的语义破坏 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增验证/诊断 | `verify_instrument_recursion_fix.py`（**7/7**，含臂 A 复现）、`diag_instrument_install.py`、`diag_callorig_probe.py`、`diag_captured_call.py`、`diag_wrapper_semantics.py`、`validate_instrument_template.py` |

### 98.7 同时收到 `flow`/`evaluate` 改动清单（只读复核），本轮**未实施**

要点（下一轮做）：`flow` 的实现在 `MCP_Server.wsv` 的 `执行Debugger断点流程JSON`（不是 `DebuggerFlow*`）；
默认等待 45000ms 需压到 12000ms（与 `auto` 一致）；超时失败体应附带 `waited_ms`/`reason`/`hint`；
`evaluate` 缺帧 ID 时应**逐行复用 `inspect` 的活帧获取**（不新增方法）；`解析Debugger求值结果` 读
`"message"` 而框架写的是 `"error"`/`"result"` → **失败原因被吞成空串**（影响 evaluate/flow/inspect/auto 四处）。

复核还纠正了我一个要求：我原想给 `flow` 加"零命中快速失败"，但**这与我在 `auto` 上刻意确立的政策冲突**
（`Core` 注释：0 位置不等于永远不可能命中，提前失败会把合法等待误判为失败）。
故 `flow` 将采用**与 `auto` 一致**的做法（只记录、不提前失败），保持全库行为一致。
""" % HEAD


def main():
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        cur = f.read()
    assert not cur.startswith(u'\ufeff'), "报告带 BOM"
    assert '\r' not in cur, "报告含 CRLF"
    assert HEAD not in cur, "该节已存在, 拒绝重复追加"
    with io.open(REPORT, 'a', encoding='utf-8', newline='') as f:
        f.write(SECTION)
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        new = f.read()
    assert not new.startswith(u'\ufeff') and '\r' not in new, "追加后编码被破坏"
    print("已追加: %s" % HEAD)
    print("行数: %d -> %d" % (cur.count('\n') + 1, new.count('\n') + 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
