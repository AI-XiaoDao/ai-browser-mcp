# -*- coding: utf-8 -*-
"""追加报告第 100 节(第84轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 100. 第84轮：注入自递归缺陷类**清零**（6/6）＋ 抓到 5 处\"让你去传一个不存在的参数\"的误导提示")

SECTION = """

---

%s

### 100.1 注入自递归：该类 6 处全部修完

累计四轮：①`instrument(transparent)` ②`hook_multi` ③`hook_logs` 两条读路径
④`hook(function_call)` ⑤`kernel trace` ⑥WS/EVAL/COOKIE 三个 hook 模式（**靠残留检查发现**）。

本轮新修的部分：

| 位置 | 缺陷 | 修法 |
|---|---|---|
| `hook(function_call)` | `Array.prototype.slice.call(arguments)`、`__orig.apply(...)`、`__lg.push`、`__cap` 用 `splice` | 手写参数复制 / `Reflect.apply` / 索引赋值 / 索引左移 |
| 同上，**`console.log` 自指通路** | 包装器内部再引用 `console.log`：若用户勾的**正是** `console.log`，就进自己 -> 无限递归 | 安装前把**原始** `console.log` 存进 `__rawLog`，包装器只调 `__rawLog` |
| `kernel trace` | `T.calls.push` + `if(len>limit)shift()`（guard-after）、`[].slice.call`、`orig.apply` | 同套路 + 索引左移封顶 |
| probe 的 `P()` | `L[k].push(o)` + `shift()`；且外层 `catch(e){}` 会把 `RangeError` **吞成"静默无数据"** | 索引赋值 + 左移封顶 |
| WS/EVAL/COOKIE 三模式 | `__lg.push` ×4、`__cap` 的 `splice` ×3、EVAL 构 `Function` 的 `slice.call` | 统一变换：`__lg.push(x)` -> `__put(x)`（追加器用索引赋值），`splice` -> 左移，`slice.call` -> 手写复制 |
| `instrument(interpreter)` | `__logs.push` | 索引赋值 |

**统一套路**（本轮定型）：索引赋值替 `push`；手写复制/左移替 `slice`/`splice`/`shift`；
`Reflect.apply` 替 `.call`/`.apply`；包装器内部**绝不引用可能出现在目标表里的名字**
（`console.log` 走 `__rawLog`）。

**残留检查立了功**：第一脚本只锚定了 `function_call` 一个模式，写完后残留检查显示
`__lg.push(` 仍有 **4** 处、`__lg.splice` 仍有 **3** 处 —— 于是改用"统一变换"（定义 `__put` 追加器 +
把 `__lg.push(` 全局换成 `__put(`，右括号不动、语法天然合法）一次清干净，最终残留全为 `False`。

### 100.2 顺带抓到的真缺陷：**5 处提示让调用方去传一个不存在的参数**

`MCP_Kernel.wsv` 里 5 处拒绝文案写的是：

```
action 不能省略 | 省略会直接执行 start… 属意外动作 | 查询状态请显式传 action:status
```

而实际合法值只有 **`start/get/clear/stop`** —— 传 `status` 会立刻得到第二次失败：

```
action 须为 start/get/clear/stop
```

**这正是"用户说的连续失败、反复换方法"的教科书成因**：工具主动给出了错误的下一步。
已把 5 处统一改为 `action:get`，并且**验收里专门加了一条**：照提示传 `action:get` 必须真的可用
（不只是文案变了）—— 实测返回 `{"success":true,"trace":"{\\"calls\\":[{\\"p\\":\\"parseI…` 数据。

### 100.3 验收 14/14（含"照提示做能成功"这条）

`_audit/verify_hook_final.py`，一次会话内**不重载**地串起来（重载会清掉 Hook）：

| 判据 | 结果 |
|---|---|
| ① 勾 `console.log` 自身 -> 同页调用它**不崩** | `called`（修复前必崩栈） |
| ② 同页再勾 `Array.prototype.push` -> `a.push` 仍 `len=3` | 通过（语义未坏） |
| ③ 勾 `eval_dynamic` -> 同页 `eval('1+1')` 仍得 2 | `{"v":2}` |
| ④ 读 `hook_logs`：`count=4`，且日志里**同时**看得到 `console.log` 与 `Array.prototype.push` | 通过（记录真的落盘，例如 `console.log` 条目 `args:["mcp-acc-1"]`） |
| ⑤ `trace action=start` 目标含 `parseInt` -> 同页触发后 `T.calls=1` | 通过 |
| ⑥ 省略 action 的拒绝文案不再指向 `status`，改为 `get`；**且照它传 `get` 确实可用** | 通过 |

### 100.4 本轮我自己的三次测试侧自伤（都记下来）

1. **参数值写错**：hook 的 `type` 应为 `eval_dynamic`，我写了 `eval` -> 只测到守卫。
2. **漏传必填的 action**：`kernel_reverse_trace` 拒绝缺省 action（属**故意**的保护，避免意外启动），
   我没传 -> 又一次"只测到守卫"。
3. **在"挂钩"和"触发"之间重载了页面** -> Hook 被清掉，于是"读日志 count=0"被误判为失败。
   **正确顺序：勾上 -> 同页触发 -> 再读日志。**
   这三条是同一个老毛病的三种变体：**测试脚本自身让用例失去判别力**。

### 100.5 明确**不做**的（有理由的推迟）

`kernel` 的 algo / gwatch 两族仍有 `L.calls.push` / `L.hits.push` + `shift()` 与 `[].slice.call`。
**但在 `instrument` 的日志路径修好之后（包装器已用 `Reflect.apply` 且不再自递归），
`push`/`call` 被包装只等于"多记一条日志"，不再构成递归风险** —— 故本轮**不改**，
避免为纯噪音去动两个正常工作的族。已在下方"仍未做"里保留。

### 100.6 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | 271/312 已测 |
| 通过 | **232**（本轮 229 -> 232）；失败 42 -> **39**，其中 `TARGET` 29 -> **26** |
| 把实例卡死 | 0；`CAPABILITY` = 0 |
| 本轮修复 | 注入自递归**收尾**（含 `console.log` 自指）+ 5 处误导提示 + 3 个探针覆盖值 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增验证 | `verify_hook_final.py`（**14/14**）、`diag_hook_params_and_status.py` |

### 100.7 仍未做（下一轮）

- **`flow` / `evaluate` 改动清单**（已收到两轮，仍未实施）：`flow` 默认等待 45000->12000、
  超时体补 `waited_ms`/`reason`/`hint`；`evaluate` 缺帧 ID 时复用 `inspect` 的活帧获取；
  `解析Debugger求值结果` 读错键导致**失败原因被吞成空串**（影响 evaluate/flow/inspect/auto 四处）。
- 台账还剩 **41** 个未测项。
- algo / gwatch 的 `push`/`shift`（噪音，非风险）。
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
