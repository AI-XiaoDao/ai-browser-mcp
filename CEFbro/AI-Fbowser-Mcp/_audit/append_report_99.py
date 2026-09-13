# -*- coding: utf-8 -*-
"""追加报告第 99 节(第83轮)。写入前断言: 无BOM、无CRLF、无重号节。

注意: 本报告文件本身是 LF; 而 MCP_Server_Reverse.wsv 是 CRLF —— 两者互不影响,
本脚本只管报告文件。
"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 99. 第83轮：清掉常规用法就会触发的另 3 处注入自递归（含唯一的服务端读路径）"
        "＋ 证实 var 捕获缺陷原本就存在")

SECTION = """

---

%s

### 99.1 本轮修的 3 处（同一缺陷类的 B/C 两类）

上一轮修好了 `browser_reverse_instrument`（**默认参数即触发**）。只读复核指出该类共 **6 处**，
本轮清掉其中**常规用法就会触发**的 3 处（累计已修 **4/6**）：

| # | 位置 | 触发条件 | 缺陷 |
|---|---|---|---|
| ① | `browser_reverse_hook_multi`（`hmCode`） | 勾选多个函数即可 | **安装期自递归**：装好 `obj[last]` 包装器后紧接 `found.push(name)` —— 若目标含 `Array.prototype.push` 当场递归；运行期 `lg.push(e)` 同病；`__cap()` 用 `lg.splice` |
| ② | `browser_reverse_hook_logs` 自动读路径 | 读日志即可 | 用 `hit.push` / `arr.slice` / `items.push` —— 而这些方法**此刻很可能已被前面的 hook/instrument 包装**，于是"读日志"这一步自己中招 |
| ③ | 同工具单键读路径 | 同上 | 用 `v.slice` / `safe.push` |

②③ 尤其要紧：它是 `__mcp_instrument_results` 的**唯一服务端读路径**，
也就是说"插装装上了但读不出来"的那条链路。

### 99.2 `hook_multi` 还带着 **var 捕获** 缺陷 —— 证实这个坑原本就在代码里

`hmCode` 的循环体是 `for(var i=...)` + `var name` / `var __orig`，两者都是**函数作用域**，
于是循环里所有包装器闭包**共享同一份**，最终指向**最后一个**目标的名字与原函数。
后果：勾了 A、B 两个函数后，日志里 A、B 的条目都会被记成最后一个名字，而且**调用的是最后一个原函数**。

> 值得记一笔：这与上一轮**我自己**在修插装时踩的坑是**同一个**（我把 `forEach` 回调换成普通
> `for` 循环引入的）。区别是：插装原来用 `forEach` 回调（天然每轮独立作用域）所以没有该缺陷；
> 而 `hook_multi` 原本就写成普通 `for` 循环，所以**这个缺陷在原代码里一直存在**，
> 不是我引入的。这也解释了为什么"勾多个函数"这种常规用法一直不可靠。

修法（统一套路）：索引赋值替 `push`；手写复制循环替 `slice`；`Reflect.apply` 替 `.apply`/`.call`；
索引左移 + 改 `length` 替 `splice`；循环体套 **IIFE 传参**保证每轮独立作用域。

### 99.3 验收 7/7 —— 用日志**内容本身**作为决定性证据

`_audit/verify_hook_multi_recursion.py`：一次调用同时勾 `mcpFnA`、`mcpFnB`、`Array.prototype.push`
（把安装期递归、var 捕获、被包装后的读路径三个缺陷一次性压到同一次测试里）。

| 判据 | 结果 |
|---|---|
| A 勾选成功且 `found=3`（含 `Array.prototype.push`） | `{"found":3,"hooked":["mcpFnA","mcpFnB","Array.prototype.push"]}` |
| B 语义未坏：`mcpFnA(1)=2`、`mcpFnB(2)=4` | `{"a":2,"b":4}` |
| C 包装 `push` 后 `a.push(1,2,3)` 仍得 `len=3, ret=3` | 通过 |
| D 读日志成功（`push` 正被包装时） | `count=3` |
| E **日志里三条条目各自名字/参数/返回值都正确** | 见下表 |

读回的日志内容（这就是 var 捕获修好的决定性证据 —— 修复前三条都会是同一个名字，
且返回值都会是被包装的 `push` 的结果）：

```
{"fn":"mcpFnA",              "args":"[1]",     "ret":"2"}
{"fn":"mcpFnB",              "args":"[2]",     "ret":"4"}
{"fn":"Array.prototype.push","args":"[1,2,3]", "ret":"3"}
```

### 99.4 本轮我自己的测试侧失误（又是"只测到守卫"）

第一次跑验收时，我把参数写成了 `targets`，而该工具的必填参数是 **`functions`**，
且它是 **JSON 数组字符串**（text 型，例 `["sign","utils.md5"]`），不是 JSON 数组。
于是第一版只测到守卫（`functions 需要JSON数组`），**后续各臂全部因"其实没勾上"而连带失败**
（读日志得 `count:0`）。这正是本项目反复出现的模式：**探针只打到守卫，就以为功能坏了**。
已改正并重跑。

### 99.5 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | **271/312** 已测（本轮 269 → 271） |
| 通过 | **231**（本轮 227 → 229；见下注） |
| 把实例卡死 | 0；失败性质 `CAPABILITY` = 0 |
| 本轮修复 | 3 处注入自递归（含唯一的服务端读路径）+ 1 处 var 捕获 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增验证 | `verify_hook_multi_recursion.py`（**7/7**） |

### 99.6 仍未做（下一轮优先级）

- **注入自递归还剩 2 处**（该类共 6 处，已修 4）：`browser_reverse_hook` 的 `function_call` 模式
  （含 `console.log` 自指这条独立通路，且该族连计数器都没有）、`browser_kernel_reverse_trace`
  （另一个 guard-after）。
- **`flow` / `evaluate` 改动清单**（上一轮已收到，未实施）：`flow` 默认等待 45000→12000、
  超时失败体补 `waited_ms`/`reason`/`hint`；`evaluate` 缺帧 ID 时复用 `inspect` 的活帧获取；
  `解析Debugger求值结果` 读错键（`"message"` vs 框架写的 `"error"`/`"result"`）导致失败原因被吞成空串，
  影响 evaluate/flow/inspect/auto 四处。
- 台账还剩 **41** 个未测项。
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
