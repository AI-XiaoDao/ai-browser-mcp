# -*- coding: utf-8 -*-
"""追加报告第 116 节（第 99 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 116. 第99轮：把"不静默假成功"系统化 —— 台账里 32 个"证据薄弱"的通过项全部定案

### 116.1 起点：台账的 `pass` 有多少只是"命令发出去了"？

判据：回包只含 `{"_async":true,...}` 而无真实结果。**32 个**通过项属此类，分三类：

| 类 | 数量 | 含义 |
|---|---|---|
| A | 26 | 回执里**有 `poll_hint`**（明确写了 `mcp_result {request_id: ...}`）→ 两步但诚实、可行动 |
| **B** | **6** | 回执里**既无结果也无任何提示**，只有 `CDP已提交:<方法>` → 调用方**根本不知道**要再调一次 ★最危险 |
| C | 2 | 待查 |

### 116.2 B 类 6 个 → 改为一次调用即得结果/诚实报错（验收 12/12）

| 工具 | 修复前 | 修复后 |
|---|---|---|
| `browser_cdp` | `CDP已提交:<方法>` | 真实 `cdp_result`（与 `browser_cdp_call` 一致） |
| `browser_reverse_preload` | `CDP已提交:Page.addScriptToEvaluateOnNewDocument` | `{"identifier":"1"}` |
| `browser_reverse_cdp_hook` | `CDP已提交:Debugger.setBreakpointOnFunctionCall` | `{"breakpointId":"7:1"}` |
| `browser_reverse_dom_breakpoint` | `CDP已提交:DOMDebugger.setXHRBreakpoint` | `{}` + 可行动提示 |
| `browser_reverse_websocket` | `CDP已提交:Network.enable` | `{}` + 可行动提示 |
| `browser_reverse_heap` | `CDP已提交:HeapProfiler.takeHeapSnapshot` | `{}` + 可行动提示 |

修法**不重复造轮子**：逆向侧 8 个调用点改用既有的同步出口 `执行V8CDP命令`；
至此 **`MCP_Server_Reverse.wsv` 内走异步入口的调用点为 0**。

**`browser_cdp` 的修法是一行**：它与 `browser_cdp_call` 是**同一件事的两个入口**
（都是通用 CDP 直通，分支体近乎逐字相同），但只有 `cdp_call` 在 `应同步等待` 名单里 ——
于是同一个 `Runtime.evaluate`，走 `cdp_call` 拿得到结果、走 `browser_cdp` 只回"已提交"。
故把 `browser_cdp` 补进 `应同步等待`（`MCP_Server.wsv:5691`）与 `取同步等待毫秒`（`:5787`）两张表，
两者行为从此一致（实测两者都回 `{"result":{"type":"number","value":2,...}}`）。

**验收**（`_audit/verify_receipt_tools_sync.py`，**12/12**），关键臂不是"有返回值"，而是
**"参数错误必须显式暴露"**（这些工具之前对任何输入都回成功）：

| 关键臂 | 结果 |
|---|---|
| `browser_cdp` 无效方法名 | `{"code":-32601,"message":"'NoSuchDomain.noSuchMethod' wasn't found"}` ✔ |
| `browser_reverse_cdp_hook` 不存在的函数 | `Could not find function with given id` ✔ |
| `browser_reverse_dom_breakpoint` 非法 type | `未知type: bogus_type_zz9` ✔ |
| `browser_reverse_heap` 坏 object_id | `Invalid heap snapshot object id` ✔ |
| `browser_cdp` 逃生门 `async_only:true` | 仍回异步回执 ✔（`Debugger.pause` 这类不返回的命令需要它） |

### 116.3 ★去掉假成功，立刻暴露一个潜伏的 100% 失效真缺陷

`browser_reverse_cdp_hook` 改同步后第一次调用就报 `Invalid parameters` ——
**这个错误以前一直被假成功掩盖着**。追下去发现源码注释（`MCP_Server_Reverse.wsv:219`）写着：

> CDP Debugger.setBreakpointOnFunctionCall 要求参数名为 functionObjectId, 非 objectId

**这句话恰好写反了。** A/B 实测（同一个 objectId，只换字段名）：

```
{"objectId": "-6037387049398756694.1.1"}          -> {"breakpointId":"7:1"}                      接受
{"functionObjectId": "-6037387049398756694.1.1"}  -> Failed to deserialize params.objectId
                                                     - BINDINGS: mandatory field missing at position 51
```

即该命令要的就是 **`objectId`**；工具发 `functionObjectId` ⇒ 内核永远拒绝 ⇒
**该工具此前 100% 不可用，而回包一直是 `success:true`**。已改回 `objectId`，
并把注释换成实测证据（防止后人再"照注释改错"）。

**这条是"假成功"危害的最好例证**：它不是"少个提示"，而是让一个彻底坏掉的工具看起来正常工作。

### 116.4 同一工具：重复安装改为**幂等成功**（A/B 实测）

修好参数名后再调用，同一函数**第二次**安装会报
`Breakpoint at specified location already exists.`。A/B 实测：

```
A 全新进程第一次 -> {"breakpointId":"7:1"}                            成功
B 同进程再装一次 -> Breakpoint at specified location already exists.   失败(但目标状态已达成)
```

报失败会让调用方以为"没装上"，转而改用 `browser_reverse_hook` / `hook_multi` / JS 注入等
**别的**方法反复尝试 —— 正是用户抱怨的形态。项目已有同一先例：`browser_debugger_resume`
对"本来就没暂停"返回**幂等成功**（其分支注释：resume 是清场/收尾类工具，目标状态已达成不是错误）。
故按同一规则处理：命中该内核原话时返回 `{"success":true,"already_armed":true,...}`，
**如实说明**"未重复安装、断点本来就在"，并给出撤销路径。修后 A/B **两臂都成功**。

### 116.5 我自己的分类器被台账截断误导（如实更正）

C 类那 2 个（`browser_reverse_cookie_sources` / `browser_permission_spoof`）
被我判成"无 poll_hint"，但**实测完整回包两者都有** `poll_hint`：

```
{"success":true,"_async":true,"task_id":"task_43630250_11184_2","message":"Cookie归因已提交...",
 "estimated_ms":300,"poll_hint":"用 mcp_result 轮询: mcp_result {request_id: \\"task_43630250_11184_2\\", consume: true}"}
```

原因：`tool_ledger.py` 存 note 时按 `[:300]` 截断，而 `poll_hint` 排在 `message` 之后被切掉了。
⇒ **C 类不存在**；A 类实为 26 个。教训：**台账是消费视图，不是原始证据**，
对"回包里有没有 X"这类判定必须拿完整回包实测，不能读台账摘要。

**最终：B 类 = 0** —— 全库再无"数据型工具只回一句回执且不告诉你怎么取"的形态。
其余 26 个 A 类都是有 `poll_hint` 的长耗时操作（清缓存/刷新/打印 PDF/下载等），两步但诚实可行动。

### 116.6 下一步

1. **实现 `browser_context_menu`**（第98轮已实证菜单事件真实触发；34 个菜单方法可达，
   且 `MCP_BrowserEvents.wsv:2662` 的形参 `菜单模式` 已在手未用）。
2. **`browser_intercept` 增 `unmodify`/`unreplace`**（现只能全清不能撤一条）。
3. 按 `_hygiene_r98.md` 删 29 条纯过程性备注（**156 条知识类必须保留**）。
4. 给 `mass_probe` 补"前置调用结果 → 工具入参"能力（`find_by_hwnd`/`network_body`/`mcp_result`
   这类状态依赖工具目前只能另行脚本验证，台账测不到实现）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 有 BOM, 中止')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 含 CR, 中止')
        return 1
    if '## 116. 第99轮' in text:
        print('!! §116 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 116. 第99轮') == 1
    print('已追加 §116; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
