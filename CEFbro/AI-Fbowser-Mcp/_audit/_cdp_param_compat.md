# CDP 手拼参数兼容性审计（旧协议参数名 / 新协议参数名）

**范围**：只读静态审计 `src/*.wsv`（活动文件，不含 `*.~vbak.wsv` 备份）。未编译、未运行、未调用任何 MCP 工具、未修改任何源码。
**产出**：本文件 `_audit/_cdp_param_compat.md`（唯一写入）。
**结论摘要**：活动文件共定位 **116 处 CDP 调用点**（其中 34 处是固定空参 `{}`，82 处手拼或字面写了非空 params）。逐条判定结果：**AT RISK 5 条**（A1–A5，名字错就整条功能失效）、**UNKNOWN 6 条**（参数由调用方透传，静态无法判定）、其余 **LIKELY FINE**（参数名跨版本稳定，且多数已有本机实测通过记录）。§1 的清单覆盖全部 116 处（纯 `{}` 调用点按用途成组列出）。
**核心方法论**：本机内核在参数名缺失时会把**它真正想要的字段名**写进错误里（`Failed to deserialize params.<它要的名字> - BINDINGS: mandatory field missing`）。因此"我们发新名 / 内核要旧名"这一类缺陷**可以只用一条原始 CDP 探测就判定**，不需要读内核。

---

## 0. 已确证的本机内核事实（本次审计的证据基线，全部来自仓库内既有记录，非我实测）

| 事实 | 原始证据（仓库内） |
|---|---|
| `Debugger.setInstrumentationBreakpoint` 要 **旧名 `instrumentation`**；发新名 `eventName` 直接 `Invalid parameters` | `MCP工具可用性检测报告.md:5163-5166`：`{"instrumentation":"beforeScriptExecution"}` -> `{"breakpointId":"8:beforeScriptExecution"}`；`{"eventName":"beforeScriptExecution"}` -> `Failed to deserialize params.instrumentation - BINDINGS: mandatory field missing at position 40`（探针脚本 `_audit/probe_cdp_ver.py`） |
| `Debugger.setReturnValue` 要 **旧名 `newValue`（对象）**；发新名 `result` 恒定失败 | `MCP工具可用性检测报告.md:8430-8443`：`{"result":{"value":true}}` -> `Failed to deserialize params.newValue ... position 31`；`{"newValue":{"value":true}}` -> 成功 `{}`；`{"newValue":true}` -> `CBOR: map start expected` |
| 本机**没有** `Debugger.removeInstrumentationBreakpoint` | `MCP工具可用性检测报告.md:5166`：`'Debugger.removeInstrumentationBreakpoint' wasn't found` |
| 本机**接受但插装不实际生效**（`beforeScriptExecution`） | `MCP工具可用性检测报告.md:5177-5189`（三条路径 0 暂停） |
| `Browser.getVersion` 报 **Chrome/135.0.7049.115 / protocolVersion 1.3** | `MCP工具可用性检测报告.md:1169` |
| 台账实测"通过"的 CDP 方法（真实 `cdp_result`，非"已提交"回执） | `_audit/_tool_ledger.md`：`Emulation.setFocusEmulationEnabled`(:180)、`Debugger.getPossibleBreakpoints`(:228)、`Debugger.setBlackboxPatterns`(:389)、`Debugger.setAsyncCallStackDepth`(:390)、`Runtime.addBinding`(:397)、`Runtime.queryObjects`(:411)、`Runtime.awaitPromise`(:412)、`Debugger.setBreakpointsActive`(:391)、`Debugger.setSkipAllPauses`(:392)、`Debugger.setPauseOnExceptions`(:388)、`DOMDebugger.getEventListeners`(:401)、`Page.setBypassCSP`(:406)、`Network.setCacheDisabled`(:407)、`Network.emulateNetworkConditions`(:179)、`Storage.getCookies`(:181)、`CSS.startRuleUsageTracking`(:182)、`Tracing.start`(:183)、`LayerTree.enable`(:184)、`Runtime.compileScript`(:229)、`Runtime.evaluate`(:408)、`Debugger.setVariableValue`(:482)、`Debugger.setReturnValue`(修复后 :480/:483)、`Profiler.startPreciseCoverage+takePreciseCoverage`(:456) |

### 0.1 两条由上面推出的、**必须写进结论**的判断

1. **不能把本机当成"整体旧内核"**。`Runtime.addBinding`(Chrome 66+)、`Emulation.setFocusEmulationEnabled`(Chrome 78+)、`CSS.takeCoverageDelta`(79+)、`Profiler.startPreciseCoverage`(79+)、`Debugger.getPossibleBreakpoints`(66+) 在本机都有**真实结果**返回 —— 这些方法在旧内核里根本不存在。所以本机是"**新方法可用、但部分命令的参数名停留在旧生成代码**"的混合状态（与 `Browser.getVersion` 报 Chrome/135 相矛盾，见 §5 未知项 U-1）。
   → 推论：**风险不能按"域新旧"批量判断，只能逐命令核对**。本报告的逐条判定因此以"该参数名在 CDP 历史上是否改过名"为准。

2. **`执行逆向CDP命令` 会把参数错误吞掉**（这是本报告排序的主要依据）。
   `执行逆向CDP命令`(`MCP_Server.wsv:7980-7993`) → `执行CDP命令_带参数`(`MCP_Server.wsv:1559-1653`) 在发完命令后**立刻返回** `{"id":...,"success":true,"_async":true,"task_id":...}`(`MCP_Server.wsv:1646-1653`)，不等 CDP 响应。
   台账里这类工具的 `pass` 长这样：`{"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:DOMDebugger.setXHRBreakpoint"}`（`_audit/_tool_ledger.md:322`）。
   → **凡是走 `执行逆向CDP命令` 的工具，参数名错了也报"成功"。** 这类工具一旦命中，就是"静默失效"，比报错更糟。反之，走 `执行V8CDP命令`(`MCP_Server_Reverse.wsv:2260`) 或 `执行CDP并同步等待`(`MCP_Server.wsv:3037`) 的工具会同步拿到内核原文错误，风险自曝。

### 0.2 判定口径

- **AT RISK**：我们发的是**新协议名** / **新协议才有的字段** / **任何版本都没有的字段**，或该字段在本机 PDL 里可能不存在 → 一旦名字错，功能整条失效。
- **LIKELY FINE**：参数名自该命令引入以来未改过名，或本机已有**真实 cdp_result** 通过的台账记录。
- **UNKNOWN**：参数由调用方透传（`params` 成员原样转发），静态无法判定。

---

## 1. 完整清单（a）

### 1.1 AT RISK（A1–A5 共 5 条；A6 是并入同一探测的对照项，本身 LIKELY FINE）

| # | file:line（调用点） | 工具 / 上下文 | CDP 方法 | params（逐字） | 旧/新 | 判定与理由 |
|---|---|---|---|---|---|---|
| A1 | `src/MCP_Server_Reverse.wsv:475` | `browser_reverse_network_intercept` action=enable（默认） | `Network.setRequestInterception` | 由 `:466-473` 构造：<br>`niParams.创建自文本 ("{}")` / `niParams.加入数组成员 ("patterns", niPatArr)`（仅当 `url_pattern` 非空） | 该方法在现行 CDP 中**已移除**（由 Fetch 域取代） | **AT RISK（方法级）**。本机新方法普遍可用（§0.1-1），故该方法**很可能已不存在** → 整条抓包改写功能失效；且走 `执行逆向CDP命令`，**错误被吞，仍报成功** |
| A2 | `src/MCP_Server_Reverse.wsv:475`（同一调用的空参分支） | 同上，**不传 `url_pattern` 时** | `Network.setRequestInterception` | 材质化后就是 `{}`（`niPattern == ""` 时 `:468` 的分支不进入，`niParams` 保持 `"{}"`） | 任何版本都要求 `patterns` | **AT RISK（必失败）**。错误签名与本次缺陷类**完全一致**：`Failed to deserialize params.patterns - BINDINGS: mandatory field missing`。且同样被异步回执吞掉 |
| A3 | `src/MCP_Server_Reverse.wsv:318` | `browser_reverse_preload`（项目自称"拦打包器最稳"的注入主路径） | `Page.addScriptToEvaluateOnNewDocument` | 由 `:314-317` 构造：<br>`plParams.加入文本成员 ("source", plCode)` / `plParams.加入逻辑值成员 ("runImmediately", 真)`<br>→ `{"source":"<code>","runImmediately":true}` | `source` 旧+新；**`runImmediately` 是新协议才加的字段**（旧版只有 `source`/`worldName`/`includeCommandLineAPI`） | **AT RISK**。若本机 PDL 早于该字段且**拒绝未知字段** → `Invalid parameters` → preload 100% 失效；而它走 `执行逆向CDP命令`，**报成功** |
| A4 | `src/MCP_Server_Reverse.wsv:93` | `browser_reverse_dom_breakpoint` type=timer | `DOMDebugger.setInstrumentationBreakpoint` | 由 `:90-92` 构造：<br>`dbTimerParams.加入文本成员 ("eventName", dbTimerEvent)`<br>（`dbTimerEvent` ∈ `setTimeout`/`setInterval`/`requestAnimationFrame`，`:84-89`） | 同名命令家族**已在本机被证明改过名**（`Debugger.setInstrumentationBreakpoint` 要 `instrumentation`） | **AT RISK**。这正是已确证那一类；`DOMDebugger` 侧是否同样用旧名 `instrumentation` 我**无法从静态与公开资料定论**（§5 U-3）。走 `执行逆向CDP命令` → **静默** |
| A5 | `src/MCP_Server_Reverse.wsv:31`（参数构造 `:26-29`） | `browser_reverse_profile` action=start_precise | `Profiler.setSamplingInterval` | `prPreciseParams.创建自文本 ("{}")` / `prPreciseParams.加入整数成员 ("interval", 100)` / `prPreciseParams.加入整数成员 ("maxDepth", 32)`<br>→ `{"interval":100,"maxDepth":32}` | `interval` 稳定；**`maxDepth` 不属于 `Profiler.setSamplingInterval`**（`maxDepth` 是 `HeapProfiler.startSampling` 的字段） | **AT RISK（多字段）**。若本机拒绝未知字段 → `action=start_precise` 必失败；`:32` 的 `是否以 (prPreciseRes, "{\"error\"")` 判据对异步回执**永不成立** → 静默。**同一份代码在 `src/MCP_Server_Core.wsv:7049-7053` 重复一份（该副本为死代码，见 §4）** |
| A6 | `src/MCP_Server_Reverse.wsv:31`（同上，`interval` 的语义） | 同上 | `Profiler.setSamplingInterval` | 同上 | `interval` 在旧协议里是 **`interval`（微秒）**，未改名 | 归入 A5 一并探测；单独看参数名本身 **LIKELY FINE** |

### 1.2 UNKNOWN（6 条：参数由调用方透传，静态不可判定）

`执行CDP命令(命令ID, method, 参数JSON)`(`MCP_Server.wsv:1716-1728`) 只取工具入参里的 `params` 成员原样转发；`browser_cdp_call`(`src/MCP_Server_Core.wsv:4463-4478`) / `browser_cdp`(`:4603-4612`) 同理。这些调用点的 params 内容**取决于调用方**，不是本项目手拼的：

| # | file:line | CDP 方法 | params（逐字） | 判定 |
|---|---|---|---|---|
| U-A | `src/MCP_Server_Core.wsv:4839` | `Debugger.getStackTrace` | `执行CDP命令 (命令ID, "Debugger.getStackTrace", 参数JSON)` —— 只在调用方显式给了 `stack_trace_id` 时才转发（`:4835-4840`）。注释 `:4828-4832` 已记录该 MCP 参数名缺陷（`Failed to deserialize params.stackTraceId: mandatory field missing`） | **UNKNOWN**：`stackTraceId` 在现行 CDP 是**对象** `{id, debuggerId}`；若调用方按旧写法传字符串会被拒 |
| U-B | `src/MCP_Server_Core.wsv:4651` | `Debugger.resume` | `执行CDP命令 (命令ID, "Debugger.resume", 参数JSON)`（工具名 `browser_debugger_resume`） | **UNKNOWN**：`Debugger.resume` 无必填参数，风险仅"多传未知字段" |
| U-C | `src/MCP_Server_Core.wsv:4660/4668/4676` | `Debugger.stepOver` / `stepInto` / `stepOut` | 同上（`参数JSON` 原样转发） | **UNKNOWN**，同上 |
| U-D | `src/MCP_Server_Core.wsv:5213` | `Debugger.enable` | `返回 (MCP命令服务器.执行CDP命令 (命令ID, "Debugger.enable", 参数JSON))` | **UNKNOWN**：`Debugger.enable` 只接受可选 `maxScriptsCacheSize`；多传字段是否被拒未知 |
| U-E | `src/MCP_Server.wsv:8369` | `Debugger.resume` | `执行CDP命令_带参数 ("_autoresume_" + 到文本 (取启动时间 ()), "Debugger.resume", "{}")` —— 实为字面 `{}`，**风险为零**，列此仅为完整性 | 实际 **LIKELY FINE** |
| U-F | 全部 `browser_cdp_call` / `browser_cdp` 调用（`src/MCP_Server_Core.wsv:4475`、`:4609`） | 任意 | 用户 `params` 字符串原样透传 | **UNKNOWN 但极重要**：这是**探针通道本身**，也是"系统性覆盖路径"（`_audit/_classlib_gap_recheck.md:192`） |

### 1.3 LIKELY FINE（其余 50 条）

> 依据列中，"台账"指 `_audit/_tool_ledger.md` 该工具的**真实 cdp_result** 记录。

| # | file:line | 工具 / 上下文 | CDP 方法 | params（逐字） | 依据 |
|---|---|---|---|---|---|
| F01 | `src/MCP_Server_Reverse.wsv:22` | `browser_reverse_profile` action=start | `Profiler.enable` | `"{}"` | 无参数 |
| F02 | `:36` / `:40` / `:44` | profile start_precise / stop / query | `Profiler.enable` / `Profiler.stop` / `Profiler.getBestEffortCoverage` | `"{}"` | 无参数 |
| F03 | `:69`（构造 `:60-68`） | `browser_reverse_dom_breakpoint` type=xhr/fetch | `DOMDebugger.setXHRBreakpoint` | `dbXhrParams.加入文本成员 ("url", dbUrl)`（缺省 `"*"`）→ `{"url":"*"}` | `url` 从未改名；台账 `:322` 只有"已提交"回执（非实证，见 §5 U-4） |
| F04 | `:80`（构造 `:77-79`） | type=dom_event | `DOMDebugger.setEventListenerBreakpoint` | `dbDomParams.加入文本成员 ("eventName", dbTarget)` → `{"eventName":"<事件名>"}` | `eventName` 是该方法**自引入起**的名字（旧版另有可选 `targetName`，本项目不发） |
| F05 | `:120` / `:195`（构造 `:110-115` / `:185-190`） | `browser_reverse_cdp_hook` / `browser_reverse_call_fn` | `Runtime.evaluate` | `加入文本成员 ("expression", …)` / `("objectGroup","reverse_cdp_hook"｜"reverse_call_fn")` / `加入逻辑值成员 ("returnByValue", 假)` / `("generatePreview", 假)` | 参数名稳定；台账 `:408` 同类 evaluate 有真实结果 |
| F06 | `:161`（构造 `:150-159`） | `browser_reverse_cdp_hook` | `Debugger.setBreakpointOnFunctionCall` | `chParams.加入文本成员 ("functionObjectId", chObjectId)`（可选 `("condition", chCondition)`） | `functionObjectId` 稳定；源码注释 `:154` 已注明"非 objectId" |
| F07 | `:264`（params 文本 `:263`） | `browser_reverse_call_fn` | `Runtime.callFunctionOn` | `cfParamsText = "{\"objectId\":\"" + JSON转义文本 (cfObjectId) + "\",\"functionDeclaration\":\"" + JSON转义文本 (cfDecl) + "\",\"returnByValue\":true}"` | 三名稳定 |
| F08 | `:331` | `browser_reverse_websocket` action=enable | `Network.enable` | `"{\"maxPostDataSize\":65536}"` | `maxPostDataSize` 稳定 |
| F09 | `:349`（构造 `:346-348`） | `browser_reverse_websocket` action=query | `Network.getResponseBody` | `wsQueryParams.加入文本成员 ("requestId", wsReqId)` | `requestId` 稳定 |
| F10 | `:363` / `:367` / `:371` | `browser_reverse_heap` | `HeapProfiler.takeHeapSnapshot` / `startSampling` / `stopSampling` | `"{\"reportProgress\":false}"` / `"{\"samplingInterval\":32768}"` / `"{}"` | 字段名稳定 |
| F11 | `:385`（构造 `:381-384`） | `browser_reverse_heap` action=get_object | `HeapProfiler.getObjectByHeapObjectId` | `加入文本成员 ("objectId", hpObjId)` / `("objectGroup","reverse_heap")` | 稳定 |
| F12 | `:427`（构造 `:422-426`） | `browser_reverse_runtime` action=properties | `Runtime.getProperties` | `加入文本成员 ("objectId", rtObjId)` / `加入逻辑值成员 ("ownProperties", 真)` / `("generatePreview", 真)` | 稳定 |
| F13 | `:446`（构造 `:441-445`） | action=evaluate | `Runtime.evaluate` | `("expression", rtExpr)` / `("returnByValue", rbvVal)` / `("generatePreview", 真)` | 稳定 |
| F14 | `:450` | action=global | `Runtime.globalLexicalScopeNames` | `"{}"` | 无参数 |
| F15 | `:479` | `browser_reverse_network_intercept` action=disable | `Network.setRequestInterception` | `"{\"patterns\":[]}"` | 参数形状对；**方法是否还存在见 A1** |
| F16 | `:933`（params 文本 `:928-929`） | `browser_reverse_instrument_script` install | `Debugger.setInstrumentationBreakpoint` | `ivParams = "{\"instrumentation\":\"" + ivEvent + "\"}"` | **已按本机实测写成旧名**，注释 `:925-927` 记录依据；这是全仓库的"正确样例" |
| F17 | `:969` | install 自检 | `Runtime.evaluate` | `"{\"expression\":\"(function(){return 0})()\",\"returnByValue\":true}"` | 稳定 |
| F18 | `:973` | install 自检 | `Debugger.resume` | `"{}"` | 无参数 |
| F19 | `:1004` | `browser_reverse_instrument_script` action=suppress | `Debugger.setSkipAllPauses` | `"{\"skip\":true}"` | 台账 `:392` 真实通过 |
| F20 | `:1018` | action=remove | `Debugger.removeInstrumentationBreakpoint` | `ivParams`（同上，含 `instrumentation`） | **不是参数名问题**：本机**无此方法**（`MCP工具可用性检测报告.md:5166`），`:1019-1028` 已做优雅降级，不算 AT RISK |
| F21 | `:1049` / `:1051`（params `:1045-1046`） | `browser_reverse_pause_on_exceptions` | `Debugger.setPauseOnExceptions` | `peParams = "{\"state\":\"" + peState + "\"}"` | 台账 `:388` 真实通过（`caught`/`none`） |
| F22 | `:1079` / `:1081`（params `:1075-1076`） | `browser_reverse_blackbox` | `Debugger.setBlackboxPatterns` | `bbParams = "{\"patterns\":[" + bbItems + "]}"` | 台账 `:389` 真实通过 |
| F23 | `:1105` / `:1107`（params `:1101-1102`） | `browser_reverse_async_stack` | `Debugger.setAsyncCallStackDepth` | `asParams = "{\"maxDepth\":" + 到文本 (asDepth) + "}"` | 台账 `:390` 真实通过 |
| F24 | `:1117`（params `:1115-1116`） | `browser_reverse_breakpoints_active` | `Debugger.setBreakpointsActive` | `baParams = "{\"active\":" + 选择 (baActive, "true", "false") + "}"` | 台账 `:391` 真实通过 |
| F25 | `:1127`（params `:1125-1126`） | `browser_reverse_skip_pauses` | `Debugger.setSkipAllPauses` | `spParams = "{\"skip\":" + 选择 (spSkip, "true", "false") + "}"` | 台账 `:392` 真实通过 |
| F26 | `:1151` / `:1172` | `browser_reverse_precise_coverage` start | `Profiler.startPreciseCoverage` | `"{\"callCount\":true,\"detailed\":true,\"allowTriggeredUpdates\":false}"` | 台账 `:456` 真实通过（自动补前置路径同样发这三个字段，随后 take 取到 `count:1`）；`allowTriggeredUpdates` 在新版被移除 → **这条通过同时是关于"未知字段是否被拒"的关键证据，见 §3 探测 P-0** |
| F27 | `:1161` / `:1173` | take | `Profiler.takePreciseCoverage` | `"{}"` | 台账 `:451/:456` 真实通过 |
| F28 | `:1183` | stop | `Profiler.stopPreciseCoverage` | `"{}"` | 无参数 |
| F29 | `:1222`（params `:1214-1215`） | `browser_reverse_patch` | `Debugger.setScriptSource` | `ptParams = "{\"scriptId\":\"…\",\"scriptSource\":\"…\",\"dryRun\":" + 选择 (ptDry,…) + "}"` | 三名稳定 |
| F30 | `:1249`（params `:1238-1248`） | `browser_reverse_return_value` | `Debugger.setReturnValue` | `rvParams = "{\"newValue\":{\"value\":" + rvValue + "}}"` | **已按本机实测改成旧名**，注释 `:1239-1247` 留了三形状对照；台账修复后 `:480/:483` 真实通过 |
| F31 | `:1304`（params `:1302-1303`） | `browser_reverse_set_variable` | `Debugger.setVariableValue` | `svParams = "{\"scopeNumber\":…,\"variableName\":\"…\",\"newValue\":{\"value\":" + svValue + "},\"callFrameId\":\"…\"}"` | 四名稳定（`newValue` 在 `setVariableValue` 上**从未改名**）；台账 `:482` 真实通过 |
| F32 | `:1404`（params `:1401-1402`） | `browser_reverse_search_script` | `Debugger.searchInContent` | `sscParams = "{\"scriptId\":\"…\",\"query\":\"…\"}"` | 稳定 |
| F33 | `:1536` / `:1538`（params `:1532-1533`） | `browser_reverse_get_possible_breakpoints` | `Debugger.getPossibleBreakpoints` | `gpbParams = "{\"start\":{\"scriptId\":\"…\",\"lineNumber\":…,\"columnNumber\":0},\"end\":{…},\"restrictToFunction\":…}"` | 台账 `:228` 真实通过 |
| F34 | `:1562`（params `:1553-1561`） | `browser_reverse_add_binding` | `Runtime.addBinding` | `abParams = "{\"name\":\"…\"}"`，带 `execution_context_name` 时为 `"{\"name\":\"…\",\"executionContextName\":\"…\"}"` | `name` 形式台账 `:397` 真实通过；**`executionContextName` 是新协议字段（旧版为 `executionContextId`）→ 仅该分支 UNKNOWN，见 §5 U-5** |
| F35 | `:1608`（params `:1606-1607`） | `browser_reverse_listeners` | `DOMDebugger.getEventListeners` | `lsParams = "{\"objectId\":\"…\",\"depth\":…,\"pierce\":…}"` | 台账 `:401` 真实通过 |
| F36 | `:1640` | `browser_reverse_dom_resolve` | `Runtime.getProperties` | `"{\"objectId\":\"" + … + "\",\"ownProperties\":true}"` | 稳定 |
| F37 | `:1675`（params `:1673-1674`） | `browser_reverse_query_objects` | `Runtime.queryObjects` | `qoParams = "{\"prototypeObjectId\":\"…\"}"` | 台账 `:411` 真实通过 |
| F38 | `:1698`（params `:1696-1697`） | `browser_reverse_compile_script` | `Runtime.compileScript` | `csParams = "{\"expression\":\"…\",\"sourceURL\":\"…\",\"persistScript\":…}"` | 台账 `:229` 真实通过（`auto_prepared: Runtime.enable`） |
| F39 | `:1711` / `:1713`（params `:1707-1708`） | `browser_reverse_bypass_csp` | `Page.setBypassCSP` | `bcParams = "{\"enabled\":" + … + "}"` | 台账 `:406` 真实通过 |
| F40 | `:1725` / `:1727`（params `:1721-1722`） | `browser_reverse_cache_disable` | `Network.setCacheDisabled` | `cdParams = "{\"cacheDisabled\":" + … + "}"` | 台账 `:407` 真实通过 |
| F41 | `:1753`（params `:1751-1752`） | `browser_reverse_network_conditions` | `Network.emulateNetworkConditions` | `ncParams = "{\"offline\":…,\"latency\":…,\"downloadThroughput\":…,\"uploadThroughput\":…}"` | 台账 `:179/:227` 真实通过 |
| F42 | `:1764`（params `:1762-1763`） | `browser_reverse_emulate_focus` | `Emulation.setFocusEmulationEnabled` | `efParams = "{\"enabled\":" + … + "}"` | 台账 `:180` 真实通过 |
| F43 | `:1775` | `browser_reverse_cookie_cdp`（无 urls） | `Storage.getCookies` | `"{}"` | 台账 `:181` 真实通过 |
| F44 | `:1798`（params `:1796-1797`） | `browser_reverse_cookie_cdp`（带 urls） | `Network.getCookies` | `ckParams = "{\"urls\":" + ckArray + "}"` | 稳定 |
| F45 | `:1813` / `:1817` / `:1821` | `browser_reverse_css_coverage` | `CSS.startRuleUsageTracking` / `takeCoverageDelta` / `stopRuleUsageTracking` | 三者均 `"{}"` | 台账 `:182` 真实通过（start） |
| F46 | `:1849` / `:1853`（params `:1848`） | `browser_reverse_trace` | `Tracing.start` / `Tracing.end` | `trParams = "{\"categories\":\"" + … + "\"}"` / `"{}"` | 台账 `:183` 真实通过 |
| F47 | `:1866` / `:1868` | `browser_reverse_layer_tree` | `LayerTree.enable` / `LayerTree.disable` | `"{}"` | 台账 `:184` 真实通过 |
| F48 | `:1945`（params `:1939-1944`） | `browser_reverse_input_cdp` kind=key | `Input.dispatchKeyEvent` | 无 text：`"{\"type\":\"…\",\"key\":\"…\",\"windowsVirtualKeyCode\":…}"`；有 text：再加 `,\"text\":\"…\"` | 字段名稳定 |
| F49 | `:1970`（params `:1968-1969`） | `browser_reverse_evaluate_silent` | `Runtime.evaluate` | `esParams = "{\"expression\":\"…\",\"silent\":…,\"userGesture\":…,\"awaitPromise\":…,\"returnByValue\":…}"` | 台账 `:408` 真实通过 |
| F50 | `:1996`（params `:1994-1995`） | `browser_reverse_await_promise` | `Runtime.awaitPromise` | `apParams = "{\"promiseObjectId\":\"…\",\"returnByValue\":…}"` | 台账 `:412` 真实通过 |
| F51 | `:2108`（params `:2104-2105`） | `browser_reverse_detect_traps` | `Debugger.searchInContent` | `dtParams = "{\"scriptId\":\"…\",\"query\":\"…\",\"caseSensitive\":false,\"isRegex\":false}"` | 稳定 |
| F52 | `:2336`（params `:2333-2334`） | `取表达式对象ID`（公共入口） | `Runtime.evaluate` | `eidParams = "{\"expression\":\"…\",\"returnByValue\":false,\"silent\":true,\"userGesture\":true}"` | 稳定 |
| F53 | `src/MCP_Server.wsv:1675` / `:1692` / `:1700` | `确保调试器已暂停` | `Debugger.enable` / `Runtime.evaluate` / `Debugger.pause` | `"{}"` / `"{\"expression\":\"setTimeout(function(){var _mcpPauseLanding=1;},30)\",\"returnByValue\":true}"` / `"{}"` | 稳定 |
| F54 | `src/MCP_Server.wsv:2359` / `:2644` / `:3010` / `:3012` / `:3109` / `:8369` | 脚本注册表/flow 收尾/解卡自救 | `Debugger.enable` / `resume` / `disable` | 均 `"{}"` | 无参数 |
| F55 | `src/MCP_Server.wsv:2847`（构造 `:2837-2844`） | `执行Debugger帧求值并等待` | `Debugger.evaluateOnCallFrame` | `("callFrameId", …)` / `("expression", …)` / 可选 `("returnByValue", 真)` | 稳定 |
| F56 | `src/MCP_Server.wsv:2911`（构造 `:2905-2909`） | `Runtime取对象属性JSON` | `Runtime.getProperties` | `("objectId", …)` / `("ownProperties", 真)` / `("generatePreview", 真)` | 稳定 |
| F57 | `src/MCP_Server.wsv:3082` / `src/MCP_Kernel.wsv:627` | 反应式补域 / CDP 监控自动启用 | `<域>.enable`（动态拼） | `"{}"` | 对无 `enable` 命令的域（如 `DOMDebugger.*`）会得到"method not found"，非致命；见 §5 U-6 |
| F58 | `src/MCP_Server.wsv:3109` | 卡死自救 | `Debugger.resume` | `"{}"` | 无参数 |
| F59 | `src/MCP_Server.wsv:3204-3233`（构造 `:3204-3229`） | `CDP派发鼠标事件` | `Input.dispatchMouseEvent` | `("type",…)` `("x",…)` `("y",…)`；`mouseWheel` → `("deltaX",…)` `("deltaY",…)`；`mousePressed/Released` → `("button",…)` `("clickCount",1)`；`mouseMoved` → `("buttons",0)` | 字段名稳定 |
| F60 | `src/MCP_Server.wsv:3272`（params 文本 `:3259-3268`） | `CDP派发触摸点一次` | `Input.dispatchTouchEvent` | `"{\"type\":\"touchEnd\",\"touchPoints\":[]}"` 或 `"{\"type\":\"<t>\",\"touchPoints\":[{\"x\":…,\"y\":…,\"radiusX\":1,\"radiusY\":1,\"force\":1,\"id\":0}]}"` | 字段名稳定 |
| F61 | `src/MCP_Server.wsv:3295`（构造 `:3290-3293`） | `CDP派发触摸事件`（零前置） | `Emulation.setTouchEmulationEnabled` | `("enabled", 真)` / `("maxTouchPoints", 5)` | 稳定 |
| F62 | `src/MCP_Server.wsv:3431`（构造 `:3424-3430`） | `CDP执行JS并等待` | `Runtime.evaluate` | `("expression", …)` / `("returnByValue", …)` / `("awaitPromise", 假)` / `("includeCommandLineAPI", 假)` | 稳定 |
| F63 | `src/MCP_Server.wsv:3562`（构造 `:3558-3560`） / `:4289`（构造 `:4285-4287`） | `CDP获取脚本源` / debugger 脚本源码 | `Debugger.getScriptSource` | `("scriptId", …)` | 稳定 |
| F64 | `src/MCP_Server.wsv:3880` / `:3891` / `:3924`（构造 `:3898-3922`） | `browser_debugger_flow` | `Debugger.enable` / `Debugger.setBreakpointByUrl` | `"{}"` / `("urlRegex", bpRegex)` + `("lineNumber", …)` + 可选 `("columnNumber", …)` | `urlRegex` 未改名；flow 有真实命中记录（`MCP工具可用性检测报告.md:8373`） |
| F65 | `src/MCP_Server_Core.wsv:4632`（构造 `:4629-4631`） | `browser_network_body` | `Network.getResponseBody` | `("requestId", requestId)` | 稳定 |
| F66 | `src/MCP_Server_Core.wsv:4716`（构造 `:4687-4713`） | `browser_debugger_set_breakpoint` | `Debugger.setBreakpointByUrl` | `("urlRegex", bpUrl)` + `("lineNumber", …)` + 可选 `("columnNumber", …)` | 稳定 |
| F67 | `src/MCP_Server_Core.wsv:4795`（构造 `:4791-4793`） | `browser_debugger_clear_breakpoints` | `Debugger.removeBreakpoint` | `("breakpointId", cbId)` | 稳定 |
| F68 | `src/MCP_Server_Core.wsv:4906`（构造 `:4898-4905`） | `browser_debugger_evaluate` | `Debugger.evaluateOnCallFrame` | `("callFrameId", frameId)` / `("expression", expr)` / 可选 `("returnByValue", 真)` | 稳定；台账 `:458` 真实通过 |
| F69 | `src/MCP_Server_Core.wsv:5085` / `:5100`（构造 `:5092-5097`） | `browser_debugger_auto` | `Debugger.enable` / `Debugger.setBreakpointByUrl` | `"{}"` / `("urlRegex", autoBpUrl)` + `("lineNumber", autoLine)` | 稳定 |
| F70 | `src/MCP_Server_Core.wsv:5445` / `:5470` | `browser_move_window` | `Browser.getWindowForTarget` | `"{}"` | `targetId`/`windowId` 均可选；台账 `:313/:461` 通过且回读到 bounds（`0.33s`） |
| F71 | `src/MCP_Server_Core.wsv:7045` / `:7053` / `:7054` / `:7058` / `:7062` | `browser_reverse_profile`（**死副本**，见 §4） | `Profiler.enable` / `setSamplingInterval` / `stop` / `getBestEffortCoverage` | 与 A5 完全相同的构造（`:7049-7052`） | 与 A5 同风险，但因不可达，实际风险为 0 |

---

## 2. AT RISK 排序（b，按"名字错时功能坏得多惨"）+ 逐条原始 CDP 探针

**探针总则（先读这一段）**
1. 探针走 `browser_cdp_call`（`src/MCP_Server_Core.wsv:4463-4478` → `执行CDP命令` → 参数取 `params` 成员）。用法：`browser_cdp_call {method:"<域.方法>", params:"<JSON 字符串>"}`。
2. **内核的报错会自己说出它要的字段名**：`Failed to deserialize params.<内核要的名字> - BINDINGS: mandatory field missing`。看到这句就等于问到了答案 —— 这正是 `setReturnValue` 那次破案的方式。
3. 方法**不存在**时报 `'<方法名>' wasn't found`（`MCP工具可用性检测报告.md:5166` 的原文格式）。
4. 每条 AT RISK 都做**两臂对照**：旧名 vs 新名，或"带可疑字段 vs 不带"，只比对内核原文，不比对工具的自述。
5. 探针必须在**已附着 CDP 的那个浏览器**上跑（本项目单观察者架构，`src/MCP_Server.wsv:1617-1620` 明确禁止切换附着）。

### P-0（先做这一条，它是"总闸"）：本机到底拒不拒"未知字段"？
A3/A5 以及 F26/F34 的风险**全部取决于**这一个问题：本机反序列化器遇到 **PDL 里没有的多余字段**是拒绝还是忽略。
```
browser_cdp_call method=Debugger.setSkipAllPauses params={"skip":true,"__mcp_probe_unknown_field":1}
```
- 返回 `{}` → **未知字段被忽略** → A3（`runImmediately`）、A5（`maxDepth`）、F34（`executionContextName`）、F26（`allowTriggeredUpdates`）**全部降级为 LIKELY FINE**，AT RISK 只剩 A1/A2/A4。
- 返回 `Invalid parameters` / `Failed to deserialize ... mandatory field missing` → **未知字段被拒** → A3/A5 立刻升级为"该功能当前 100% 失效"。
- 交叉印证：`Profiler.startPreciseCoverage {"callCount":true,"detailed":true,"allowTriggeredUpdates":false}` 已在本机**通过**（台账 `:456`），若 `allowTriggeredUpdates` 在本机 PDL 中不存在，则该通过本身就是"未知字段被忽略"的证据；若它仍存在，则该证据为零 —— 这一点我无法静态判定（§5 U-2），故必须先做 P-0。

### 排名 1：A1 + A2 —— `Network.setRequestInterception`（`src/MCP_Server_Reverse.wsv:475` / `:479`）
**为什么最惨**：整个 `browser_reverse_network_intercept` 工具（请求拦截改写）**只在 CDP 层存在这一条实现**；A2 那条空参路径是**默认调用**（`action` 缺省即 enable，`url_pattern` 常被省略）→ 必然命中"必填字段缺失"，**错误签名与本次缺陷类一模一样**；而 A1 是"方法可能已被 Fetch 域取代"。两条都走 `执行逆向CDP命令` → **工具仍回 `success:true` 的"已提交"回执**，调用方完全看不到。
**探针**：
```
browser_cdp_call method=Network.setRequestInterception params={"patterns":[{"urlPattern":"*","requestStage":"Request"}]}
browser_cdp_call method=Network.setRequestInterception params={}
browser_cdp_call method=Fetch.enable params={}
```
**判读**：第 2 条若报 `params.patterns - BINDINGS: mandatory field missing` → **A2 确证**（且证实"缺必填字段"与"参数改名"共用同一错误签名）。第 1 条若报 `'Network.setRequestInterception' wasn't found` → **A1 确证**，应迁移到 Fetch 域。第 3 条返回 `{}` → 替代方案可用。

### 排名 2：A3 —— `Page.addScriptToEvaluateOnNewDocument {"source":…,"runImmediately":true}`（`src/MCP_Server_Reverse.wsv:318`）
**为什么惨**：`browser_reverse_preload` 是项目自己写进多条降级文案的"最稳注入路径"（`:995`、`MCP工具可用性检测报告.md:5195`）。`runImmediately` 是新协议才加的字段；若本机拒绝未知字段，这条主路径直接失效，且**同样被异步回执掩盖**。台账里该工具只有 `_async` 回执（`_audit/_tool_ledger.md:325`），**不能作为"参数被接受"的证据**。
**探针**：
```
browser_cdp_call method=Page.addScriptToEvaluateOnNewDocument params={"source":"window.__mcp_probe=1","runImmediately":true}
browser_cdp_call method=Page.addScriptToEvaluateOnNewDocument params={"source":"window.__mcp_probe=2"}
```
**判读**：两臂都返回 `{"identifier":"…"}` → 未知字段被忽略，当前写法安全。第一臂报错、第二臂成功 → 必须去掉 `runImmediately`（并另想办法让脚本立即执行）。正确心智模型：`identifier` 是本机确实支持该方法的凭证。

### 排名 3：A4 —— `DOMDebugger.setInstrumentationBreakpoint {"eventName":…}`（`src/MCP_Server_Reverse.wsv:93`）
**为什么惨**：这是**已确证缺陷的同一命令家族**（`Debugger.setInstrumentationBreakpoint` 本机要 `instrumentation`）。若 `DOMDebugger` 侧同样是旧名 → `browser_reverse_dom_breakpoint type=timer` 整条失效；走 `执行逆向CDP命令` → **静默成功**。台账对该工具只记录过 `type=xhr` 的 `_async` 回执（`:322`），timer 分支**从未被验证**。
**探针（两臂，必做）**：
```
browser_cdp_call method=DOMDebugger.setInstrumentationBreakpoint params={"eventName":"setTimeout"}
browser_cdp_call method=DOMDebugger.setInstrumentationBreakpoint params={"instrumentation":"setTimeout"}
```
**判读**：谁的返回不是 `Invalid parameters` 就是本机的真名。若两臂都报 `mandatory field missing params.<同一个名字>`，取那一臂报出的**那个名字**改代码。（注意：本机对 `beforeScriptExecution` 存在"接受但不生效"的先例，`MCP工具可用性检测报告.md:5177-5189` —— 因此"能接受"不等于"能拦到"，timer 类需另做一次真命中验证。）

### 排名 4：A5 —— `Profiler.setSamplingInterval {"interval":100,"maxDepth":32}`（`src/MCP_Server_Reverse.wsv:31`，死副本 `src/MCP_Server_Core.wsv:7053`）
**为什么惨**：`browser_reverse_profile action=start_precise`（"精确采样"）会 100% 失败；`:32` 的本地判据 `是否以 (prPreciseRes, "{\"error\"")` 对异步回执永不成立 → **静默**。`maxDepth` 在任何版本的 `Profiler.setSamplingInterval` 里都**不是它的字段**（`maxDepth` 属于 `HeapProfiler.startSampling`），属"多余字段"而非"改名"，故风险完全取决于 P-0。
**探针**：
```
browser_cdp_call method=Profiler.setSamplingInterval params={"interval":100,"maxDepth":32}
browser_cdp_call method=Profiler.setSamplingInterval params={"interval":100}
```
**判读**：第一臂报错、第二臂 `{}` → 必须删掉 `maxDepth`（这正是"照抄现行文档会写错/照抄 HeapProfiler 会写错"的实例）。

### 排名 5：F34 的 `executionContextName` 分支 —— `Runtime.addBinding`（`src/MCP_Server_Reverse.wsv:1560`）
低危（仅在调用方传 `execution_context_name` 时触发），但同属"新协议字段"类。探针：
```
browser_cdp_call method=Runtime.addBinding params={"name":"__mcp_probe_bind","executionContextName":"x"}
browser_cdp_call method=Runtime.addBinding params={"name":"__mcp_probe_bind","executionContextId":1}
```
旧协议用 `executionContextId`，新协议用 `executionContextName`；哪一臂成功即本机真名。清理：`browser_cdp_call method=Runtime.removeBinding params={"name":"__mcp_probe_bind"}`。

### 排名 6（不进 AT RISK，仅备查）：`Debugger.removeInstrumentationBreakpoint`（`src/MCP_Server_Reverse.wsv:1018`）
已确证本机无此方法（`MCP工具可用性检测报告.md:5166`），代码已优雅降级（`:1019-1028` 给出 suppress / disable 两条可行动路径），**不需要改**。若将来要"单独卸载插装"，应向 `DOMDebugger.removeInstrumentationBreakpoint` 探测。

---

## 3. 建议的"一次性收敛"探测（比逐条猜更快）

若主代理愿意跑 3~5 条探针，建议按此顺序：

1. `browser_cdp_call method=Browser.getVersion params={}` —— 复核 §0 表里那句 `Chrome/135.0.7049.115`（解决 U-1 的矛盾）。
2. `browser_cdp_call method=Schema.getDomains params={}` —— 拿到本机**真实存在的域清单**（一次就能判 A1 的方法是否存在）。
3. P-0（`Debugger.setSkipAllPauses` + 未知字段）—— 一次判定 A3/A5/F26/F34 四条的命运。
4. A4 的两臂探针、A2 的空参探针。
5. 若该浏览器的 DevTools HTTP 端点在本地可达，取 **`/json/protocol`**：它给出本机内核**完整且逐字段的 PDL/JSON 协议**，可一次性终结本报告所有 UNKNOWN（我没能从源码或既有报告确认该端点是否暴露，见 §5 U-7）。

---

## 4. 附带发现（与参数无关，但影响"谁的判断才是真的"）

1. **`执行逆向CDP命令` 是"静默失效放大器"**：`src/MCP_Server.wsv:7980-7993` → `:1646-1653` 立即回 `_async` 回执。走这条路的工具共 9 个（`browser_reverse_profile`、`_dom_breakpoint`、`_cdp_hook`、`_call_fn`、`_preload`、`_websocket`、`_heap`、`_runtime`、`_network_intercept`，另加 `MCP_Server_Core.wsv:7035` 死副本）。**这些工具的台账 `pass` 不能作为参数被内核接受的证据**（`_audit/_tool_ledger.md:319/322/325/327/333/337/346/349` 全是 `_async` 回执）。
2. **`browser_reverse_profile` 有两份实现**：`src/MCP_Server_Reverse.wsv:12`（活动）与 `src/MCP_Server_Core.wsv:7035`（不可达）。派发顺序见 `src/MCP_Server.wsv:10572`（`MCP_逆向分派`）先于 `:10585`（`MCP_核心分派`）→ Core 那份是死代码。两份的参数构造**完全相同**，故不影响 A5 的结论，但改动时只改一处会留下"看起来已修"的假象。
3. **`params` JSON 解析失败会静默变空字典**：`src/MCP_Server.wsv:1627-1638` —— `FBrowser_Parser_解析JSON` 失败时只打一行控制台日志，然后**用空字典继续发命令**。于是"参数串拼坏"会产生**与参数改名完全相同**的内核报错（`mandatory field missing`）。排查此类缺陷时，必须先排除这一层（这正是 U-8）。
4. **嵌套数组的转换链路未经验证**：params 经 `FBrowser_Parser_解析JSON` → `类_FBrowser_字典值` → `开发者消息_执行方法`（`src/MCP_Server.wsv:1627-1645`）。项目自己记录过"yyjson 嵌套 `加入数组成员` 会 0xC0000005"（`src/MCP_Server.wsv:3257-3258`、`:2250`）。凡 params 含**数组套对象**的手拼点（`patterns`、`touchPoints`、`urls`、`includeCommandLineAPI` 无影响）都多一层风险：A1 的 `patterns`（`加入数组成员`）、F60 的 `touchPoints`（纯文本拼接，较安全）、F44 的 `urls`（纯文本拼接）。

---

## 5. 我明确**无法确定**的事项（unknowns）

| 编号 | 事项 | 为什么无法确定 / 如何终结 |
|---|---|---|
| U-1 | **本机到底是哪个协议版本**。`Browser.getVersion` 报 `Chrome/135.0.7049.115`（`MCP工具可用性检测报告.md:1169`），但 `Debugger` 域要旧名 `instrumentation`/`newValue`（`:5163-5166`、`:8430-8443`），而 `Runtime.addBinding`/`Emulation.setFocusEmulationEnabled`/`CSS.takeCoverageDelta` 等**新方法**又能真实通过 | 二者逻辑矛盾（详 §0.1-1）。可能是"内核版本被伪装/被定制过"或"FBrowser 的 DevTools 生成代码来自更旧的 PDL"。终结手段：探测 1（`Browser.getVersion`）+ 探测 5（`/json/protocol`）+ `Schema.getDomains` |
| U-2 | **本机拒绝还是忽略"未知字段"** | 决定 A3/A5/F26/F34。终结手段：**P-0 一条探针**。我没有运行任何东西，故只能列出条件分支 |
| U-3 | **`DOMDebugger.setInstrumentationBreakpoint` 的旧参数名到底是不是 `instrumentation`** | 公开资料我只查到"现行 tot 用 `eventName`"，未能检索到该命令在旧版 PDL 中的字段名（同一域中的 `setEventListenerBreakpoint` 用的是 `eventName` + 已移除的 `targetName`，这削弱了"必然同名改名"的推断，但**不能排除**）。叠加本机 `Debugger` 域已确证改名，我按"同类风险"判 AT RISK。终结手段：A4 两臂探针（内核会自报字段名） |
| U-4 | `DOMDebugger.setXHRBreakpoint` 的 `url` 是否真被本机接受 | 台账只有 `_async` 回执（`:322`），无任何真实 cdp_result。`url` 从未改名，故我仍判 LIKELY FINE，但**它是"未验证"而非"已验证"**。终结手段：`browser_cdp_call method=DOMDebugger.setXHRBreakpoint params={"url":"*"}`，看是否 `{}` |
| U-5 | `Runtime.addBinding` 的 `executionContextName`（新）vs `executionContextId`（旧）在本机的真名 | 只有 `name` 形式被实测通过（台账 `:397`）。终结手段：排名 5 的两臂探针 |
| U-6 | `<域>.enable`（`src/MCP_Server.wsv:3082`、`src/MCP_Kernel.wsv:627`）对**没有 enable 命令的域**（如 `DOMDebugger.*`、`Schema.*`）会怎样 | 动态拼接，静态不可判定；预计是 `wasn't found` 类错误，且该调用点**不检查返回**（`:3082`），属静默噪声，非功能缺陷。终结手段：`browser_cdp_call method=DOMDebugger.enable params={}` |
| U-7 | 本机是否暴露 DevTools HTTP 端点（`/json/protocol`） | 项目里 `/json/list`、`/json/version` 是 **MCP 服务自己的**端点（`src/MCP_ResponseBuilders.wsv:319-320`），**不是内核的**；我无法从源码确认内核调试端口是否对外可达。若可达，本报告所有 UNKNOWN 可一次终结 |
| U-8 | `params` 经 `FBrowser_Parser_解析JSON` → 字典 → `开发者消息_执行方法` 时，**字段名/数值类型/嵌套数组是否被改写** | 这是与"参数改名"并行的第二类可能根因；若存在改写，那么**任何**手拼参数都可能莫名报 `mandatory field missing`（而 `setReturnValue` 的破案过程中，两臂用的是同一条通道，故那一例**不可能是**通道改写造成的 —— 反过来说，通道改写仍未被排除在其它调用点之外）。终结手段：对同一命令发"内核已验证可通过的参数"（如 `Debugger.enable {}`）并观察是否稳定；再用同一命令发带未知字段的参数做对照 |

---

## 6. 我搜索了什么（可复核）

**检索工具**：`grep`（ripgrep 正则）+ `glob` + 定点 `read`（带 file:line）。未编译、未运行、未调用任何 MCP 工具、未改任何源码。

**在 `src/*.wsv` 上使用的检索式**（活动文件 15 个；`*.~vbak.wsv` 备份只用于交叉印证，未计入清单）：
- 调用助手：`执行CDP并同步等待|执行V8CDP命令|执行逆向CDP命令|browser_cdp_call|执行CDP命令`
- 字面方法名全集（**这是完整性主检**）：`"(Page|Emulation|Browser|Target|Network|Runtime|Debugger|DOMDebugger|DOM|Input|Profiler|HeapProfiler|Storage|CSS|Tracing|LayerTree|Fetch|Overlay|Log|Accessibility|ServiceWorker|Security|WebAudio|Media|Audits|CacheStorage|IndexedDB|Animation|Database|DeviceOrientation|IO|Memory|Performance|Schema|SystemInfo|WebAuthn)\.[A-Za-z]+"` → 191 命中
- 动态方法名：`\+ "\.enable"|\+ "\.disable"|开发者消息_执行方法` → 仅 `src/MCP_Kernel.wsv:627`、`src/MCP_Server.wsv:3082` 两处动态拼域
- params 成员构造：`加入(文本|整数|逻辑值|数值|浮点|长整数|布尔)成员 \("[a-z]` → 1557 命中（其中绝大多数是 MCP 响应载荷，非 CDP 参数；已逐文件筛除）

**逐文件核对结果**：
- 有 CDP 调用的活动文件（逐点清点，共 116 处）：`MCP_Server_Reverse.wsv` **75 处**、`MCP_Server.wsv` **21 处**、`MCP_Server_Core.wsv` **19 处**（含 `:7035` 那处死副本内的 5 次调用）、`MCP_Kernel.wsv` **1 处**。其中固定空参 `{}` 共 34 处（Reverse 15 / Server 11 / Core 7 / Kernel 1）。
- **零 CDP 调用**（其 `加入文本成员` 是 MCP/CEF 事件载荷，不是 CDP params）：`MCP_Server_VIP.wsv`、`MCP_BrowserEvents.wsv`、`MCP_Callbacks.wsv`、`MCP_Server_Workflow.wsv`、`MCP_Server_HTTP.wsv`、`MCP_ResponseBuilders.wsv`、`MCP_Server_Form.wsv`、`MCP_Server_System.wsv`、`MCP_Stdio.wsv`、`MCP_Server_Utils.wsv`、`main.wsv`、`MCP_Constants.wsv`。
- `browser_cdp_call` 的注册在 `src/MCP_Server.wsv:9822`（schema 仅 `method`/`params`），路由在 `src/MCP_Server_Core.wsv:4463-4478`，别名 `browser_cdp` 在 `:4603-4612`；三者都不构造参数，只透传。

**关于"是否已经有人审计过同一件事"**：仓库内确有相邻记录但我**未发现**覆盖本清单的完整审计 —— `_audit/_triage_param.md` 讲的是 MCP 工具自身参数（`browser_vip_set_*_version` 的 116–135 域），`_audit/_classlib_gap_*.md` 讲类库能力缺口，`MCP工具可用性检测报告.md` §76/§112 只覆盖了 `setInstrumentationBreakpoint` 与 `setReturnValue` **两例**。本文件是对同一缺陷类的**全量盘点**。

---

## 7. 一行结论

本机内核不是"整体旧版本"，而是**新方法可用、部分命令参数名停在旧生成代码**的混合体（§0.1-1）；因此**唯一可靠的判定方式是逐命令问内核**（内核会在报错里自报它要的字段名）。当前最该先跑的是 **P-0（未知字段容忍性）**、**A1/A2（`Network.setRequestInterception` 是否存在 + 空 `patterns`）**、**A4（`DOMDebugger.setInstrumentationBreakpoint` 的 `eventName` 还是 `instrumentation`）** 三组探针；其中 A2 与 A4 一旦命中，会以**与本次已确证缺陷完全相同的错误签名**暴露，且都不会有任何工具层报错（异步回执掩盖）。

---

## 6. 主代理实测更正（同会话真实 MCP 调用；以此节为准）

> 本节由主代理用 `browser_cdp_call`（同步返回内核原始报错）逐条核验 §1.1 的 AT RISK 清单后追加。
> **§1.1 的 A1–A5 中已有 4 条被实测推翻**；§1.1 保留作"当时为何怀疑"的过程记录，不再作为结论。
> 复现脚本：`_audit/probe_cdp_param_names.py`、`_audit/probe_intercept_shape.py`、`_audit/probe_profiler_lifecycle.py`。

### 6.1 总闸结论：本机**忽略未知字段**

探针 `Debugger.setSkipAllPauses {"skip":true,"__mcp_probe_unknown_field":1}` → `{}`

⇒ 凡"多传了一个 PDL 里没有的字段"这一类风险**整体不成立**。
直接后果：A3（`runImmediately`）、A5（`maxDepth`）、`allowTriggeredUpdates`、`executionContextName`
**全部降级为安全**——这正是 §2 建议的 P-0 探针所要的答案。

### 6.2 逐条更正

| 条目 | 静态判定 | **实测结论** | 证据（内核原始返回） |
|---|---|---|---|
| A1/A2 `Network.setRequestInterception` | 方法可能已不存在 / 空参必失败 | **方法存在**，但**两种形状都发错了** → 已修复 | `{}` → `Failed to deserialize params.patterns - BINDINGS: mandatory field missing at position 8`；`{"patterns":["*"]}` → `... patterns - CBOR: map start expected at position 25`；`{"patterns":[{"urlPattern":"*","requestStage":"Request"}]}` → `{}`；`{"patterns":[]}` → `{}` |
| A3 `Page.addScriptToEvaluateOnNewDocument` | `runImmediately` 是新字段，可能被拒 → preload 100% 失效 | **两臂都被接受**，`runImmediately` 安全 | `{"source":"void 0"}` → `{"identifier":"1"}`；`{"source":"void 0","runImmediately":true}` → `{"identifier":"2"}` |
| A4 `DOMDebugger.setInstrumentationBreakpoint` | 疑与 `Debugger.*` 同族改名，应为 `instrumentation` | **恰好相反**：该命令要的就是 `eventName`，旧代码**本来就是对的** | `{"eventName":"setTimeout"}` → `{}`；`{"instrumentation":"setTimeout"}` → `Failed to deserialize params.eventName - BINDINGS: mandatory field missing at position 35` |
| A5 `Profiler.setSamplingInterval` | `maxDepth` 非该命令字段 | 字段名**无误**（未知字段被忽略）；但顺带查出**更严重的真缺陷**：该工具族漏调 `Profiler.start` | `{}` → `Failed to deserialize params.interval - BINDINGS: mandatory field missing at position 8`；`{"interval":100}` → `{}`；`{"interval":100,"maxDepth":32}` → `{}` |
| A6 `executionContextName` | 低危 | 未单独实测（总闸已覆盖该风险类型） | — |
| U-1「内核版本自相矛盾」 | 疑本机是旧内核 | **已定案：内核确为 Chromium 135**。旧参数名是本 CEF 构建的定制，**不是版本差异** | UA-CH 回读基线：`fullVersionList: Chromium 135.0.7049.115`、`platformVersion: 19.0.0` |

### 6.3 本轮由该审计**直接产出**的两个真实缺陷（已修复并验收）

1. **`browser_reverse_network_intercept`**：`enable` **两条路径 100% 失效**（见 6.2 A1/A2），
   且因走 `执行逆向CDP命令` 而**报 success**。已改为纯文本拼接对象数组 + `执行CDP并同步等待`；
   缺 `url_pattern` 时**明确失败**（刻意不默认「拦截全部」：本项目没有放行通道，会把页面挂死）。
   验收 `_audit/verify_network_intercept.py` **4/4**（含"匹配模式确实把导航挂住"的行为臂）。
2. **`browser_reverse_profile`**：`start`/`start_precise` 只调 `Profiler.enable`，**采样从未开始**；
   `stop` 的内核错误被吞、profile 被丢弃。已补 `Profiler.start`、改同步并回传截断标注的 profile。
   验收 `_audit/verify_profiler_lifecycle.py` **4/4**（取回 2992 字符真实 profile）。

### 6.4 仍然成立的结论（请保留）

- **§0.1-2 完全成立**：`执行逆向CDP命令` 吞参数错误 → 走它的工具"参数错也报成功"。
  这正是上面两个缺陷长期不可见的**根因**。台账里这 9 个工具的 `pass` 只是 `_async` 回执，
  **不能**作为"参数被接受"的证据。
- **风险必须逐命令实测**，不能按域、更不能按版本批量推断——本轮 A1/A4 一正一反即为反例。
