# -*- coding: utf-8 -*-
"""把本轮(第20轮)结论追加到 MCP工具可用性检测报告.md (显式UTF-8, 防编码损坏)"""
import io, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u'''
---

## 75. Hook 能力审计（用户要求：参考技能书确保没有问题）

### 75.1 先说结论：Hook 挂载本身完全正常

早期观察到 `browser_reverse_hook_multi {"functions":["window.fetch"]}` 偶发返回
`Hook错误: [无法序列化的值]`，一度怀疑 Hook 功能损坏。**实测证明 Hook 本身没问题**，
一次失败属偶发/状态相关（同参数在干净实例上稳定通过），而"日志查不到"完全是另一个原因（见 75.2）。

页面真值取证（`_audit/diag_hook_log.py`）：

```
mcpHookFnA231723.__mcp_hooked        = true          <- Hook 真的装上了
window.__MCP_HOOK_LOG__ 长度          = 2
  [{"target":"window.mcpHookFnA231723","hook":"mcp_hook_24051515_596586","ts":...,
    "args":"[1,2]","ret":"3","stack":"Error\\n    at __wrapper (<anonymous>:1:1070)..."}]
__MCP_EVAL_LOG__ / __MCP_WS_LOG__ / __MCP_COOKIE_LOG__ 长度 = 0/0/0
```

即：参数、返回值、调用栈**全都正确记录了**，只是记录在 `__MCP_HOOK_LOG__` 里。

### 75.2 缺陷1（最伤体验）：`hook_logs` 缺省读错日志键 → 用户必得空结果

`MCP_Server_Reverse.wsv` 原实现：

```
hlKey = yyjson取文本 (参数JSON, "log_key")
如果 (hlKey == "") { hlKey = "__MCP_EVAL_LOG__" }
```

而函数 Hook 写的是 `__MCP_HOOK_LOG__`（`MCP_Server_Core.wsv` 的 function_call 路径与
`hook_multi` 均如此，`hook_multi` 还主动回传 `log_key:'__MCP_HOOK_LOG__'`）。
**用户按工具描述走"挂 Hook → 调用 → 查日志"，必然拿到 `{"count":0,"items":[]}`，
从而判定 Hook 功能损坏** —— 而日志就躺在另一个键里。更糟的是 schema 的 `log_key`
枚举里根本没列 `__MCP_HOOK_LOG__`，描述却写着"记录到 `__MCP_HOOK_LOG__(hook_logs可查)`"。

**修法**：缺省 = **自动探测全部已知日志键并在单次 JS 求值内合并**，返回
`by_key` 报出各键条数、`keys` 报出命中的键；显式传 `log_key` 时保持原语义（向后兼容）。
另在 `count==0` 时追加 `hint`（列出已检查的键 + "需先触发目标函数"）。

实测（`_audit/verify_v8_hook.py` 段 A）：

```
count=1 by_key={'__MCP_HOOK_LOG__': 1, '__MCP_EVAL_LOG__': 0, '__MCP_WS_LOG__': 0, '__MCP_COOKIE_LOG__': 0}
keys=['__MCP_HOOK_LOG__']
```

### 75.3 缺陷2：`action=clear` 会用重新赋值破坏闭包 → 已安装的 Hook **静默失效**

原实现：`var a=window[k]||[]; window[k]=[];` —— **整体重新赋值**。
但 Hook 包装器在**安装时**就把数组捕获进了闭包（`var __lg=window.__MCP_HOOK_LOG__=...`），
重新赋值后，已安装的 Hook 仍然往**已被丢弃的旧数组**里写 →
**用户清一次日志，所有已装的 Hook 就不再记录了，且毫无提示**。

这一点最初是我自己测试脚本踩到的（`window.__MCP_HOOK_LOG__=[]` 之后 `xhr_fetch` 抓不到东西），
顺着查下去才发现是工具本身同一个问题 —— 属"测试脚本污染环境"与"真实缺陷"双重命中。

**修法**：改为**原地截断** `v.length=0`（对象型 `{results:[...]}` 则 `v.results.length=0`），
保持闭包引用有效；对"既非数组也非 results 对象"的值**不再破坏**，而是回报
`cleared:0, note:'值不是数组, 未改动(避免破坏闭包引用)'`。

实测（段 A2）：`clear` 后再调用被 Hook 函数，日志 `count==1` —— **Hook 仍在记录**。

### 75.4 附带发现：31 个"幽灵注册"（注册表有、实现没有）

`命令注册表`（负责工具名合法性判定）里注册了 **31 个没有实现的命令名**，其中 **23 个是 `reverse_*`**：

```
reverse_async_stack  reverse_await_promise  reverse_blackbox      reverse_breakpoints_active
reverse_bypass_csp   reverse_cache_disable  reverse_compile_script reverse_cookie_cdp
reverse_css_coverage reverse_detect_traps   reverse_dom_resolve    reverse_emulate_focus
reverse_evaluate_silent reverse_input_cdp   reverse_layer_tree     reverse_listeners
reverse_network_conditions reverse_patch    reverse_precise_coverage reverse_query_objects
reverse_search_script reverse_skip_pauses   reverse_trace
```

（注释写着 v2.8 "CDP逆向增强 R5/R6/R7/R8/R9"，即**当初只留了号、没写实现**；
另外 8 个是 `aliases/batch/create_tab/debugger_pause/fingerprint_*/font_randomize/task_runner_post` 等陈旧残留。）

**调用幽灵命令的实测行为是干净的**：0.0s 返回、JSON-RPC error、健康检查不受影响
（`cdp_ready=True`、`latency_max` 不变）—— 不挂死、不假成功。所以它们不构成线上故障，
但**定义了缺失能力的既定命名**，本轮起就按这些预留名实现（见第 76 节）。

核对脚本：`_audit/registry_vs_tools.py`。结果：

```
源码注册表=249  源码添加工具JSON=280  服务实际=280
A) 注册表有/无工具定义(幽灵注册)=31
B) 有工具定义/注册表无=62
C) 服务实际 vs 源码定义 差异=0        <- tools/list 与源码完全一致
```

---

## 76. V8 级 Hook + 插装 + 超复杂混淆逆向能力扩展（用户要求）

### 76.1 结构性根因：拿不到 `scriptId`，V8 级能力根本无从实现

`MCP_Server.wsv` 的 `存储CDPDevTools事件` 有一行关键注释：

```
// CDP 事件高频, 仅保留 async 缓存供 wait/event 查询, 不写 event_log 防膨胀
存储异步结果 ("cdp_event:" + 事件方法名, 参数字段)
```

即事件按**方法名单槽**存储、**后到覆盖先到**。而 `Debugger.scriptParsed` **每个脚本只上报一次**，
于是 N 个脚本最后只剩 1 条 —— `Debugger.searchInContent` / `getPossibleBreakpoints` /
`setScriptSource` 这些**全都需要 scriptId**，全部无法实现。这也解释了为什么既有的
"脚本检索"只能退化成 `browser_reverse_search` 那种**只扫 `<script>` 标签 textContent**
的 JS 级做法（动态脚本 / eval / `blob:` / Worker / 运行时拼装一律搜不到）——正是混淆场景下失效的那类。

**修法**：新增 **V8 脚本注册表**（`MCP_Server.wsv`），只对 `Debugger.scriptParsed` 单独累积，去重 + 上限 500 条淘汰最旧。
采用**三个平行数组**（`脚本ID表` / `脚本URL表` / `脚本注册表(详情JSON)`）而非"单数组存 JSON 对象"：
后者在检索时要么解析对象数组、要么踩 `yyjson取文本` 对非文本节点返回空的坑。
实测立刻拿到全部脚本：

```
browser_reverse_search_script action=list -> count=9 (注入标记脚本后为 20)
[{"scriptId":"51","url":"","length":51,"startLine":0,"endLine":0,"isModule":false}, ...]
```

### 76.2 本轮新增 11 个工具（280 → 291），全部真机验收

统一出口 `执行V8CDP命令`：**一律走 `执行CDP并同步等待`**，让 CDP 侧错误显式暴露，
而不是像 `执行逆向CDP命令` 那样回一句"CDP已提交"就完事（那类异步回执会掩盖失败）。

| 工具 | CDP 能力 | 实测证据 |
|---|---|---|
| `browser_reverse_search_script` | `Debugger.searchInContent` + 注册表 list/clear | **命中动态注入的脚本**：`script_id:58, hit_count:1`, `scanned=9 matched=2` |
| `browser_reverse_precise_coverage` | `Profiler.startPreciseCoverage/take/stop` | `cdp_result` 1037 字节，含 `functionName:"window.mcpV8Fn…", count:1` |
| `browser_reverse_blackbox` | `Debugger.setBlackboxPatterns` | 成功；空数组=清除 |
| `browser_reverse_async_stack` | `Debugger.setAsyncCallStackDepth` | 成功（缺省 32，显式 0=关闭）|
| `browser_reverse_breakpoints_active` | `Debugger.setBreakpointsActive` | 成功 |
| `browser_reverse_skip_pauses` | `Debugger.setSkipAllPauses` | 成功（应急止血开关）|
| `browser_reverse_pause_on_exceptions` | `Debugger.setPauseOnExceptions` | `caught`/`none` 均成功；非法 state 被拒 |
| `browser_reverse_patch` | `Debugger.setScriptSource` | 缺 `source` 时明确拒绝并给指引 |
| `browser_reverse_return_value` | `Debugger.setReturnValue` | 未暂停时明确拒绝（不假成功）|
| `browser_reverse_set_variable` | `Debugger.setVariableValue` | 未暂停时拒绝；`call_frame_id` 缺省自动取最近暂停帧 |
| `browser_reverse_instrument_script` | `Debugger.setInstrumentationBreakpoint` | 见 76.4（含如实自检）|

### 76.3 实测出的 CDP 版本差异（照抄现行协议文档会写错）

本机内嵌 Chromium 的 CDP 比现行协议**旧**，两处必须按实测写（`_audit/probe_cdp_ver.py`）：

```
{"instrumentation":"beforeScriptExecution"}  -> {"breakpointId":"8:beforeScriptExecution"}   <- 正确
{"eventName":"beforeScriptExecution"}        -> Invalid parameters
      "Failed to deserialize params.instrumentation - BINDINGS: mandatory field missing at position 40"
Debugger.removeInstrumentationBreakpoint     -> 'Debugger.removeInstrumentationBreakpoint' wasn't found
重复 install                                  -> "Instrumentation breakpoint is already enabled."
Debugger.disable                             -> {}  (实测可清掉插装, 但会同时清掉全部断点)
Debugger.setPauseOnExceptions                -> {}  可用
```

即：参数名是**旧版的 `instrumentation`**，且**本机根本没有单独卸载插装的方法**。
故 `action=remove` 先尝试原生卸载，不支持时返回**可行动的两条路径**（`action=suppress`
不丢状态立即止血 / `browser_debugger_disable` 彻底清除但会连带清掉全部断点），
**绝不静默去 disable 整个调试器**。

### 76.4 最重要的诚实性修正：`beforeScriptExecution` 在本机"接受但不生效"

`install` 返回 `{"breakpointId":"8:beforeScriptExecution"}` —— CDP 接受了。
但三条路径全部实测**不产生任何暂停**（`_audit/probe_iv_nav.py` / `probe_iv_pause.py`）：

```
1) install                    : success, breakpointId=8:beforeScriptExecution
2) 导航到新页面                : 0.7s 正常完成（未暂停）
3) 导航后 execute_js 1+1       : 0.0s 返回 2      <- 页面没卡住 = 没暂停
4) Debugger.paused 事件        : 未找到
5) eval('1+2')                : 0.0s 返回 3      <- 没有"执行前暂停"
6) 内联 appendChild 注入脚本    : 0.02s 返回       <- 同样不暂停
```

**这正是一直在修的"静默假成功"**：若 `install` 只回报 CDP 接受，用户会以为插装拦住了页面脚本，
实际什么都没拦。故 `install` **装完立刻用一个极小的新脚本做自检**（默认 `verify=true`）：
观察到 `Debugger.paused` → 自动 `resume` 并回报 `verified:"true"`；
未观察到 → 回报 `verified:"false"` + `warning` + `alternative`
（指向本机可用的等效路径：`browser_reverse_preload` 的 `Page.addScriptToEvaluateOnNewDocument`
才是"早于任何页面 JS"的可靠机制 / `browser_debugger_flow` / `set_breakpoint`）。

验收断言也随之改成"**必须如实报告未生效**"，而不是"必须暂停":

```
[PASS] install 被CDP接受(breakpointId)                 {"breakpointId":"8:beforeScriptExecution"}
[PASS] 【诚实性】未生效时如实报告 warning+替代路径(非假成功)  本机实测: CDP接受了该插装, 但不会实际暂停…
[PASS] suppress 止血成功(插装保留但不再拦截)
[PASS] remove 本机不支持时给出可行动指引                 … | 立刻止血: action=suppress | 彻底清除: browser_debugger_disable
```

### 76.5 验收结果与耗时

```
_audit/verify_v8_hook.py  ->  31/31 通过, 约 9-10s
_audit/loop.py            ->  编译 16.6-23.5s (0 警告), 快检 fastcheck 41/41 (约5s)
整轮(编译+快检+验收)         ->  34.7s
工具总数                     ->  280 -> 291
```

`loop.py` 新增 `--syntax` 模式：仅 `/c` 生成 C++ 自检、**不链接**（11.9–14.7s），
故改完代码可以立刻验语法而不必先关程序 —— 本轮 10 个新分支就是靠它快速迭代的。

### 76.6 本轮新增的测试脚本

| 脚本 | 作用 |
|---|---|
| `_audit/verify_v8_hook.py` | Hook 修复 + 11 个 V8/插装工具端到端（31 项）|
| `_audit/diag_hook_log.py` | 页面真值取证：`__mcp_hooked` 标记 + 各日志键实际内容 |
| `_audit/verify_hook_capability.py` | Hook 闭环：注入函数→Hook→调用→查日志（7 项）|
| `_audit/verify_hook_native.py` | 原生函数（fetch/XHR）Hook 可用性 |
| `_audit/registry_vs_tools.py` | 命令注册表 vs 源码工具 vs 服务 tools/list 三方核对 |
| `_audit/probe_ghost_cmd.py` | 幽灵命令调用行为（确认是干净拒绝）|
| `_audit/probe_cdp_ver.py` | CDP 版本差异实测（参数名/方法存在性）|
| `_audit/probe_iv_pause.py` / `probe_iv_nav.py` | 判定插装是否真的暂停页面 |

### 76.7 下一轮待办

1. **剩余 16 个幽灵工具**（已预留号、仍无实现）：`reverse_listeners`(DOMDebugger.getEventListeners)、
   `reverse_query_objects`(Runtime.queryObjects)、`reverse_compile_script`(Runtime.compileScript)、
   `reverse_await_promise`(Runtime.awaitPromise)、`reverse_bypass_csp`(Page.setBypassCSP)、
   `reverse_cache_disable`(Network.setCacheDisabled)、`reverse_trace`(Tracing.start/end)、
   `reverse_input_cdp`(Input.dispatch*)、`reverse_evaluate_silent`(Runtime.evaluate silent)、
   `reverse_css_coverage`、`reverse_layer_tree`、`reverse_dom_resolve`(DOM.resolveNode)、
   `reverse_emulate_focus`、`reverse_cookie_cdp`(Storage.getCookies)、`reverse_network_conditions`、
   `reverse_detect_traps`。
2. `Debugger.getPossibleBreakpoints`（混淆成一行时无法按行下断的解法）与 `Runtime.addBinding`（原生桥接防检测）尚无预留号，需新分配。
3. 脚本注册表目前只在 `Debugger.scriptParsed` 时累积，**跨导航会留下失效 scriptId**（检索时会报
   `No script for id`）：本轮已按 `stale_scripts` 计数容错，后续可在导航事件里主动清表。
4. 内联脚本的 `url` 为空串，可考虑给注册表加 `(inline)` 之类的展示回退，便于 list 时可读。
'''

with io.open(P, 'a', encoding='utf-8') as f:
    f.write(SEC)

print('已追加, 当前行数=%d 大小=%d' % (len(io.open(P, encoding='utf-8').read().splitlines()),
                                    os.path.getsize(P)))
