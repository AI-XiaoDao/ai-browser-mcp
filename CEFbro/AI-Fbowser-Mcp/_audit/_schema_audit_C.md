# Schema 与实现一致性审计 — C 组（逆向/插装 · 内核 · 编排 · 事件落库 · HTTP 传输层）

审计人：只读分析子代理（C 组）　产出文件：`_audit/_schema_audit_C.md`　写入时间：本次会话
审计方式：**纯静态**（DSH `read`/`grep` + 两个自写的只读正则核对脚本，脚本落在 `%TEMP%`，未写入工程、未编译、未调用 MCP、未触碰 `E:\HSPC`）。

## 0. 行号口径与复核锚点

| 文件 | 物理行尾 | DSH `read`/`grep` 报的行号 | 本文件采用 |
|---|---|---|---|
| `src/MCP_Server_Reverse.wsv` | **CR CR LF**（实测 LF=2484, CR=4952） | LF 口径（=2484） | **LF 口径（同 DSH）** |
| `src/MCP_Kernel.wsv` | LF（LF=1955, CR=0） | 1955 | 同 |
| `src/MCP_BrowserEvents.wsv` | LF（LF=3535, CR=0） | 3535 | 同 |
| `src/MCP_Server_Workflow.wsv` | CRLF（LF=844, CR=844） | 844 | 同 |
| `src/MCP_Server_HTTP.wsv` | LF（LF=369, CR=0） | 369 | 同 |
| `src/MCP_Server.wsv` | LF（LF=12609, CR=0） | 12609 | 同 |

> 注：本报告全部行号与 DSH `grep`/`read` 输出**逐行一致**（已用 `Select-String` 与字节级 LF/CR 计数交叉验过）；若主代理用 `Select-String`（UTF-16 口径）读 `MCP_Server_Reverse.wsv`，行号会≈×2，请以 LF 口径为准。每条差异都附了**锚点原文**，可直接用锚点重定位，不依赖行号。

schema 生成链（`src/MCP_Server.wsv`）：`添加工具JSON (名称, 描述, schemaJSON)`（:11602-11605，第 3 参缺省为 `"inputSchema":{"type":"object"}`）
→ `单参数Schema文本 (名, 类型, 描述, 必须=真)`（:11763-11782，「必须」缺省为**真**）
→ `多属性Schema文本 (属性列表, 必需列表)`（:11793-11805）→ `属性项JSON (名, 类型, 描述)`（:11807-11819）。
路由：`browser_reverse_` 前缀 → `MCP_逆向分派.分类分派_逆向操作`（:12149-12152）；`browser_kernel_` 前缀 → `MCP_内核分派.分类分派_内核操作`（:12153-12156）；`workflow` 前缀 → `MCP_编排分派.分类分派_编排操作`（:12145-12148）。

## 1. 扫描工具清单（本组共 65 个工具 + 14 个 HTTP 端点分支 + 1 个 WS 处理器）

| 族 | 实现文件 | 工具数 | 工具名 |
|---|---|---|---|
| `browser_reverse_*`（本文件实现 44 个） | `src/MCP_Server_Reverse.wsv`（分支 :12–:2112，出口 :2369） | 44 | profile, dom_breakpoint, cdp_hook, call_fn, preload, websocket, heap, runtime, network_intercept, scan_crypto, string_refs, detect_obfuscator, hook_logs, hook_multi, stack_trace, instrument_script, pause_on_exceptions, blackbox, async_stack, breakpoints_active, skip_pauses, precise_coverage, patch, return_value, set_variable, search_script, get_possible_breakpoints, add_binding, listeners, dom_resolve, query_objects, compile_script, bypass_csp, cache_disable, network_conditions, emulate_focus, cookie_cdp, css_coverage, trace, layer_tree, input_cdp, evaluate_silent, await_promise, detect_traps |
| `browser_kernel_*` | `src/MCP_Kernel.wsv`（分支 :60–:143） | 17 | cert, auth, download, scheme, menu, ipc_queue, ipc_clear, cdp_monitor, reactor, watch, events_all, reverse_probe, reverse_trace, reverse_algo, reverse_functions, reverse_sources, reverse_watch_global |
| `workflow*` | `src/MCP_Server_Workflow.wsv`（分支 :63–:108） | 4 | workflow_list, workflow_get, workflow_run, workflow_stop |
| 事件落库（无工具分支，作为**事件名/族名事实源**被核对） | `src/MCP_BrowserEvents.wsv` | 0 | 记录 64 个字面事件名（脚本正则统计：`记录监控事件 ([^,]+, "X"` 去重后 64 个） |
| HTTP/WS 传输层（无工具分支） | `src/MCP_Server_HTTP.wsv` | 0 | 14 个 HTTP 端点分支 + 1 个 WS 处理器：`OPTIONS`(:53) / `DELETE /mcp`(:59) / `GET /mcp`→405(:83) / `POST /mcp,POST /`(:91) / `/metrics`(:125) / `/health`,`/healthz`(:135) / `/cursor-config`(:185) / `/json/version`(:204) / `/json`,`/json/list`(:214) / `/tools/brief`(:226) / `/tools`,`/tools/list`(:236) / `/api`(:255) / `/docs`(:265) / `/`(:275) |

**不在本组范围（同前缀但实现在别处，避免重复/漏报）**：`browser_reverse_hook`(`MCP_Server_Core.wsv:7506`)、`_strings`(:7616)、`_verify`(:7681)、`_cookie_sources`(:7721)、`_env`(:7753)、`_instrument`(:7796)、`_search`(:7870)、`_extract`(:7910)、`_initiator`(:8182)、`_setup`(:8297)、`_preset`(:8327) 共 11 个（注册行 `MCP_Server.wsv:11451-11473`），由负责 `MCP_Server_Core.wsv` 的子代理覆盖。

## 2. 差异表（29 条）

> 差异类型：`MISSING_IN_SCHEMA` / `DECLARED_UNUSED` / `ACTION_MISMATCH` / `ENUM_MISMATCH` / `DESC_PROMISE` / `REQUIRED_MISMATCH`

| 工具名 | 差异类型 | 证据（实现 file:line + 关键代码片段） | 描述原文（截断） | 影响 | 建议修法 |
|---|---|---|---|---|---|
| `browser_reverse_instrument_script` | MISSING_IN_SCHEMA | `MCP_Server_Reverse.wsv:1035` `如果 (ivAction == "install" && MCP命令服务器.参数键存在 (参数JSON, "confirm") == 假)` → :1037 `返回 (…"install 需要显式确认"…)`；注册行 `MCP_Server.wsv:11510` 的 properties 只有 `action`/`event`，required 列表为空，且该行全文（1154 字符）**不含 "confirm"** | "…action=install/remove/suppress(插装保留但不再拦截, 本机止血用), event=beforeScriptExecution(默认)/beforeScriptWithSourceMapExecution。需先browser_debugger_enable…" | `install` 是**默认动作**却必须额外传 schema 未声明的 `confirm` → 空参调用与 `{"action":"install"}` **必然失败**，代理只能从报错里反推参数（典型"白试多轮"） | 在 schema 增加 `confirm`(boolean, "install 必填")，或把 required 与描述同步写明 |
| `browser_reverse_instrument_script` | MISSING_IN_SCHEMA | `MCP_Server_Reverse.wsv:1077` `ivVerify = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "verify", 真)` | 描述正文出现 "实测把自检关掉(verify:false)装入后同样卡死"，但 properties 无 `verify` | 自检开关只能靠细读长描述发现，schema 不可发现 | 把 `verify`(boolean, 默认 true) 加入 properties |
| `browser_reverse_websocket` | MISSING_IN_SCHEMA | `MCP_Server_Reverse.wsv:420` `wsReqId = …yyjson取文本 (参数JSON, "request_id")`，:423 再兼容 `"requestId"` | 注册行 `MCP_Server.wsv:11467` 用 `单参数Schema文本 ("action", "text", "enable(默认)/query")`——**只声明 action** | `action=query` 必须传 request_id，schema 里完全看不到，代理无法构造成功调用 | 增加 `request_id`(text, "取自 Network.requestWillBeSent") |
| `browser_reverse_websocket` | ACTION_MISMATCH | `MCP_Server_Reverse.wsv:433` `返回 (执行V8CDP命令 (命令ID, "Network.getResponseBody", wsQueryParams…))`——`query` 实为取 **HTTP 响应体** | "WebSocket消息拦截。Network.enable+webSocketFrameReceived—监听所有WS帧(send/receive),用于分析实时通信协议" | 代理按描述以为能取 WS 帧，实际拿到 HTTP 响应体，且 `enable` 分支（:414）只调 `Network.enable`，从不订阅/读取帧 | 描述改成 "query=Network.getResponseBody(取HTTP响应体)"，或补真正的 WS 帧读取路径 |
| `browser_reverse_scan_crypto` | DECLARED_UNUSED | `MCP_Server.wsv:11506` 声明 `属性项JSON ("script_index","integer","只扫描第N个脚本(默认全部)")`；全文件 `grep "script_index"` 于 `MCP_Server_Reverse.wsv` **0 命中**；:606-615 注入的 JS 恒 `document.querySelectorAll('script')` 全量扫描 | "script_index: 只扫描第N个脚本(默认全部)" | 代理传 `script_index` 被**静默忽略**并收到全量结果，会误判命中来自第 N 个脚本（与已知 `browser_network limit` 同类） | 删除该属性，或在 :606 起的 JS 里按索引过滤 |
| `browser_reverse_detect_obfuscator` | DECLARED_UNUSED | `MCP_Server.wsv:11508` 声明 `单参数Schema文本 ("script_index","integer","只检测第N个脚本(默认全部)", 假)`；`MCP_Server_Reverse.wsv` 内 `script_index` **0 命中**；:725 `total+=(ss[i].textContent||'')+'\n'` 恒拼接全部脚本 | "script_index: integer 只检测第N个脚本(默认全部)" | 同上一行，静默忽略 | 同上 |
| `browser_reverse_dom_breakpoint` | ENUM_MISMATCH | `MCP_Server_Reverse.wsv:146-158`：`dbType=="timer"` 时 `dbTarget=="setTimeout"\|\|=="setInterval"` 取该值，**否则固定 `requestAnimationFrame`**，再发 `DOMDebugger.setInstrumentationBreakpoint` | `MCP_Server.wsv:11464` `属性项JSON ("target","text","URL模式(xhr)或事件名(dom_event)")` | `type=timer` 时 `target` 语义完全未文档化（是定时器名，且默认 rAF），代理只会去填 URL/事件名 | target 描述补 "type=timer 时取 setTimeout/setInterval(其它值=requestAnimationFrame)" |
| `browser_reverse_layer_tree` | DESC_PROMISE | `MCP_Server_Reverse.wsv:1980` `返回 (执行V8CDP命令 (命令ID, "LayerTree.enable", "{}", "合成层上报已开启: 内核将推送 LayerTree.layerTreeDidChange…"))`——本工具**只 return 一句提示**，不回任何层数据 | `MCP_Server.wsv:11534` "开启后内核推送 LayerTree.layerTreeDidChange, 可看到层数量与合成原因(如 transform/opacity 未提升为合成层)" | 描述承诺"可看到"，但数据只在 CDP 事件通道；对比 `browser_reverse_trace` 的描述会明说要先 `browser_kernel_cdp_monitor` 订阅，本工具没说 → 代理拿到"已开启"后以为有数据 | 照 `browser_reverse_trace`（`MCP_Server.wsv:11533`）的写法补订阅前置说明 |
| `browser_reverse_profile` | REQUIRED_MISMATCH | `MCP_Server.wsv:11463` `单参数Schema文本 ("action","text","start/start_precise(精确采样)/stop/query(默认start)")`——**第 4 参缺省=真 ⇒ required:[action]**；实现 `MCP_Server_Reverse.wsv:16-19` `如果 (prAction == "") { prAction = "start" }` | 描述明示 "query(**默认**start)" 与 "action 可省略" 语义 | schema 强制必填、描述与实现都说可省略 → 严格校验的客户端会拒掉合法空参调用 | 第 4 参传 `假` |
| `browser_reverse_websocket` | REQUIRED_MISMATCH | `MCP_Server.wsv:11467` 单参数无第 4 参 ⇒ required:[action]；实现 `MCP_Server_Reverse.wsv:406-409` `如果 (wsAction == "") { wsAction = "enable" }` | "action: enable(**默认**)/query" | 同上一行 | 第 4 参传 `假` |
| `browser_kernel_cdp_monitor` | ENUM_MISMATCH | `MCP_Kernel.wsv:671-697` `// 默认 list` 分支：任何未命中 add/remove/clear/enable/disable 的 action（含拼错值）都落到这里 `返回 (…命令成功_原始JSON…)`；:696 `st.加入文本成员 ("events_json", 查询事件日志 ("cdp_monitor","",0,200))` 是**该工具唯一读取出口** | `MCP_Server.wsv:11350` `属性项JSON ("action","text","add/remove/clear/enable/disable")` | ①`action:"addd"` 会**静默返回 list + success**，代理以为订阅已加；②想读回捕获事件只能猜到未声明的 `list` | 枚举补 `list`；未知 action 一律 `命令失败`（同族 :1188 的做法） |
| `browser_kernel_cdp_monitor` | DESC_PROMISE | `MCP_Kernel.wsv:577` `变量 CDP监控上限 <… 类型 = 整数 值 = 200 …>`，全工程无第二处赋值（`grep CDP监控上限` 仅此定义 + :597 条件赋值）；:595 `如果 (新上限 > 0 && 新上限 <= 5000)` 只有**显式传参**才改 | 描述 "max为缓存上限**默认500**最大5000"；schema "事件缓存上限(**默认500**, 最大5000)" | 省略 `max` 时实际只保留 **200** 条，代理按 500 估算会误判"事件丢了/漏采" | 变量初值改 500，或把描述/schema 改为 200 |
| `browser_kernel_reactor` | ENUM_MISMATCH | `MCP_Kernel.wsv:758` 失败提示原文 `返回 (…命令失败 (命令ID, "event 不能为空 \| 例: load_end / navigate / url_changed / *"))`；而 `load_end` **不在**反应器可命中的事件集合里（反应器只看 `记录监控事件` 的第 2 参，见 `MCP_BrowserEvents.wsv:51` `MCP_内核分派.检查反应器 (事件类型)`；`load_end` 走的是 `MCP命令服务器.记录加载事件 ("load_end", …)`，`MCP_BrowserEvents.wsv:929`，**不经过**该钩子） | `MCP_Server.wsv:11351` 同工具描述："**事件名必须用下面列出的真实值**: 写错(如 load_end)的规则会被接受但**永不触发**且无任何提示" | **实现自己的报错把描述点名的错误值当推荐示例** → 代理照抄报错必然永不触发，且毫无提示 | 把 :758 的示例改为 `navigate / url_changed / *` |
| `browser_kernel_reactor` | ENUM_MISMATCH | 反应器真正比对处 `MCP_Kernel.wsv:832` `如果 (事件模式 == "*" \|\| 事件模式 == 事件类型)`（**仅精确相等 + `*`**）；实际可命中集合 = `MCP_BrowserEvents.wsv` 中 `记录监控事件(…, "X", …)` 的 64 个字面名，例如 `context_menu_opening`(:2852)、`quick_menu_command`(:2920)、`download_start_error`(:687)、`devtools_popup`(:1563)、`ipc_from_renderer`(:2721)、`permission_prompt_show`(:3247)、`drag_enter`(:3081)、`tooltip`(:2986)、`render_view_ready`(:3031)、`cursor_changed`(:3003)、`auto_resize`(:3020)、`open_url_from_tab`(:2950)、`offscreen_paint`(:3429) 等 | `MCP_Server.wsv:11351` 事件名清单只列 21 个：`* / navigate / url_changed / loading_state_change / load_progress / resource_request / resource_response / resource_redirect / popup / popup_failed / download_start / download_progress / fullscreen / favicon / find_result / key_press / status_message / before_unload / browser_created / browser_closing / do_close` | 40+ 个**合法**事件名不可发现；配合上一条"写错永不触发"的警告，代理会以为 `context_menu_opening` 之类是错值，从而退化到 `*` 通配（全事件触发 JS，副作用不可控） | 描述补全族名清单（或指向 `browser_event` 的族名通配写法），并同步反应器支持的动态名 `download_complete/download_canceled` |
| `browser_kernel_reactor` | ENUM_MISMATCH | `MCP_Kernel.wsv:794-811` `// 默认 list` 分支返回规则表 + `命令成功` | `MCP_Server.wsv:11351` `属性项JSON ("action","text","add/clear")` | `action` 拼错 → **静默成功**且规则没加上；`list`（查看已注册规则）不可发现 | 枚举补 `list`；未知 action 返回失败 |
| `browser_kernel_watch` | ENUM_MISMATCH | `MCP_Kernel.wsv:983-1016` `// 默认 list` 分支，其中 :1007 `变更JSON = 查询事件日志 ("watch_changed","",0,200)` + :1015 组装 `changes_json`——**监视到的变更只在此分支返回** | `MCP_Server.wsv:11352` `属性项JSON ("action","text","start/stop/clear")`；描述"周期性求值页面表达式并记录值变化" | 声明的 3 个 action 都拿不到 `changes_json`：代理无法读取"记录到的值变化"，只能靠猜 list（且 dispatcher :110 要求 action 必须存在） | 枚举补 `list`，并在描述里写明"用 action=list 读 changes_json" |
| `browser_kernel_download` | ENUM_MISMATCH | `MCP_Kernel.wsv:362-386` `// 默认 list: 返回待执行队列`；实现自己在 :343 报错里写 `"url 或 download_id 必填其一 \| 先用 action=list 查看进行中的下载"` | `MCP_Server.wsv:11337` `属性项JSON ("action","text","pause/resume/cancel/clear_queue")`（描述亦未列 list） | 队列查询入口不可发现；拼错 action 静默返回队列 + success，代理以为暂停/取消已排队 | 枚举补 `list`；未知 action 返回失败 |
| `browser_kernel_cert` | ENUM_MISMATCH | `MCP_Kernel.wsv:160` `否则 (动作 == "ignore_off" \|\| 动作 == "off")`——实现多接受一个别名 `off`；:180 `// 默认 list`（未识别 action 同样静默退化） | `MCP_Server.wsv:11335` `属性项JSON ("action","text","list/ignore/ignore_off/clear/status")` | 别名 `off` 未文档化（无害）；但未识别 action 静默返回 list + success 会掩盖客户端拼写错误 | 枚举补 `off`（或删别名）；未知 action 返回失败 |
| `browser_kernel_events_all` | ENUM_MISMATCH | `MCP_Kernel.wsv:1257` `如果 (动作 == "get")` → :1257-1407 完整实现 `get`（回 28 项真值 + `enabled_count`/`total`）；且 :1188 实现自己在缺参报错里写 `"查询状态请显式传 action:get"` | `MCP_Server.wsv:11353` `单参数Schema文本 ("action","text","enable 全开 / disable 全关")`——**枚举无 get** | 代理按实现提示传 `action:get`，但该值不在 schema 枚举内；做枚举校验的客户端会直接拒绝 → 状态不可观测 | 枚举补 `get` |
| `browser_kernel_events_all` | ENUM_MISMATCH | 实际开启的 12 个扩展族见 `MCP_Kernel.wsv:1211-1222`，其中 :1221 `是否监控开发者窗口`、:1222 `是否监控自建URL请求` | `MCP_Server.wsv:11353` "12 扩展族: 含菜单/快捷菜单/导航意图/界面细节/插件/启动/渲染/渲染WS/权限/离屏"（只点了 10 个） | 代理不知道 `devtools_popup` / `open_url_from_tab`(urlreq) 两个族也被本工具一并打开，排障时会误判"这些事件不是我开的" | 补齐两项名称（开发者窗口 / 自建URL请求） |
| `browser_kernel_ipc_clear` | DESC_PROMISE | `MCP_Kernel.wsv:544-570` 与 `browser_kernel_ipc_queue` **共用同一实现**：仅 `如果 (动作 == "clear")` 清空，其余任何值（含 `"queue"`）都落到 :555-570 返回队列 + `命令成功`，**无任何校验** | `MCP_Server.wsv:11349` "action 必填且**只能为 clear**。等价于 browser_kernel_ipc_queue action=clear" | 代理若把 action 写成 `queue`，会收到一份 success 负载（内容还是队列），**误以为队列已清空** | 非 `clear` 直接 `命令失败` |
| `browser_kernel_ipc_queue` | REQUIRED_MISMATCH | `MCP_Server.wsv:11348` 单参数无第 4 参 ⇒ required:[action]；实现 `MCP_Kernel.wsv:548-557` 缺 action 时**不拒绝**，当 queue 返回 | "action **必填**: queue 取回队列JSON, clear 清空" | 声明必填而实现宽松（与同族 :62/:74/:94/:102/:110 的"缺参一律拒绝"风格不一致），会掩盖客户端漏参 | 实现补 `参数键存在 (参数JSON,"action")` 校验 |
| `browser_kernel_scheme` | DESC_PROMISE | `MCP_Kernel.wsv:412-415` `body = …取文本 (参数JSON,"data")`；`如果 (body == "" && 文件是否存在 (…"file"))` 才读文件——**文件不存在时不报错**，`body` 保持空串，继续注册并返回 `命令成功(…取文本长度(body) + "字符")` | `MCP_Server.wsv:11338` `属性项JSON ("file","text","响应内容文件路径(与data二选一)")` | 文件路径写错（或既没给 data 也没给可用 file）会**静默注册空内容**，页面访问 `mcp://域名` 得空白，代理反复重试 | `file` 给了但不存在/为空时返回明确失败 |
| `workflow_run` | MISSING_IN_SCHEMA | `MCP_Server_Workflow.wsv:277-280` `如果 (工作流名 == "") { 工作流名 = …yyjson取文本 (参数JSON, "file") }`（`加载工作流定义` 内，被 :720 调用） | `MCP_Server.wsv:11333` `多属性Schema文本 (属性项JSON ("name","text","工作流文件名") + … + 属性项JSON ("on_error","text","stop\|continue"), "\"name\"")`——**无 file** | `file` 是 name 的合法别名（实现报错文本 :723 也写 "需要 name/file…"），但 schema 看不到 | properties 增加 `file` |
| `workflow_run` | MISSING_IN_SCHEMA | 步骤对象真实字段：`skip`(`MCP_Server_Workflow.wsv:524`)、`delay_ms`(:537，上限 30000 于 :542-546)、`tool`(:562)／别名 `name`(:565)、`args`(:573)／别名 `arguments`(:576)、`wait_async`(:589)、`max_ms`(:601，上限 5 min 于 :606-610)、步骤级 `on_error`(:632) | `MCP_Server.wsv:11333` `属性项JSON ("steps","text","内联步骤JSON数组")`——**完全没给步骤对象字段表** | 编排是"一次调用成功"最吃 schema 的工具：步骤键写错（如把参数平铺、用 `params`、用 `wait`）只会得到 `success:false` 的步骤记录，代理必须逐轮试错才能收敛 | 在 `steps` 描述（或工具描述）里给出步骤对象完整字段表 |
| `workflow_run` | REQUIRED_MISMATCH | `MCP_Server.wsv:11333` required=`["name"]`；实现 `MCP_Server_Workflow.wsv:704-747` 允许仅凭 `steps` 运行（:711-716 名字缺省为 `"inline"`），:723 报错文本明示 "需要 name/file、**definition 或 steps** 参数" | "name: 工作流文件名"（required） | 想内联跑 `steps` 的代理被 schema 逼着编一个无意义的 `name`，与"内联步骤"语义冲突 | required 改为空数组，或在描述写清 `name` 与 `steps` 可并存 |
| `workflow_get` | MISSING_IN_SCHEMA | `MCP_Server_Workflow.wsv:75-79` `工作流名 = …取文本 (参数JSON,"name")`；`如果 (工作流名 == "") { 工作流名 = …取文本 (参数JSON, "file") }` | `MCP_Server.wsv:11332` `单参数Schema文本 ("name","text","工作流名(无.json)")` | `file` 别名不可发现 | properties 增加 `file` |

### 2.7 HTTP/WS 传输层（端点类）

| 工具名（端点） | 差异类型 | 证据（实现 file:line + 关键代码片段） | 描述原文（截断） | 影响 | 建议修法 |
|---|---|---|---|---|---|
| HTTP 端点清单（服务端自述） | MISSING_IN_SCHEMA | 实际生效的端点分支：`/metrics`(`MCP_Server_HTTP.wsv:125`)、`/healthz`(:135)、`/cursor-config`(:185)、`/json/version`(:204)、`/json`\|`/json/list`(:214)、`/tools/brief`(:226)、`/tools`\|`/tools/list`(:236)、`/api`(:255)、`/docs`(:265)、`/`(:275)、`DELETE /mcp`(:59)、`GET /mcp`→405(:83)、`OPTIONS`任何路径→200(:53) | 服务端自述清单只列 7–8 条：欢迎页 `index.html:589-598`（POST /mcp、POST /、WS、GET /api、/health、/tools/list、/json/list、/json/version＝8 条）与回退页 `MCP_Server_HTTP.wsv:285`（同上去掉 /json/version＝7 条） | ①代码注释 `MCP_Server_HTTP.wsv:223-225` 自称 `/tools/brief` 是"AI 代理上下文友好"入口（72735 字节 → 精简版约 1/5），**两处清单都没列** → 代理不知道可省上下文；②`/metrics`、`/docs`、`/cursor-config`、`/healthz` 同样不可发现 | 两处清单一并补全（至少补 `/tools/brief`、`/metrics`、`/docs`、`/cursor-config`、`/healthz`） |
| HTTP/WS 端点（WS 地址） | DESC_PROMISE | `GET /mcp` 的 405 正文：`MCP_Server_HTTP.wsv:87` `"…元信息见 GET /api, 服务端推送请改用 WebSocket (ws://host:port/mcp) 或 stdio 通道"`；而规范地址 `MCP_Server.wsv:414-417` `返回 ("ws://" + 服务器绑定地址 + ":" + 到文本 (服务器端口))`（**无路径**），欢迎页 WS 行同样无路径（`index.html:592` path:''）；WS 处理器 `MCP_Server_HTTP.wsv:303-317` **只拒 `/devtools/`**，其余任何路径都 `回调.继续()` | 同上（405 正文） | 同一服务对同一通道给出两个不同 URL；因 WS 不校验路径，两者其实都能连，但会误导客户端/排障者，也让"路径白名单"缺失这一事实被掩盖 | 统一写成 `ws://host:port`，或给 WS 也显式列 `/mcp` 并在处理器里校验路径 |

## 3. 小结

- **扫描工具数**：**65 个**（`browser_reverse_*` 44 + `browser_kernel_*` 17 + `workflow*` 4）＋ **14 个 HTTP 端点分支与 1 个 WS 处理器**；另核对 `MCP_BrowserEvents.wsv` 的 **64 个字面事件名**作为事件名事实源。
- **差异条数：29 条**
  - `ENUM_MISMATCH` **10** 条（reactor×3、cdp_monitor×1、watch、download、cert、events_all×2、dom_breakpoint）
  - `MISSING_IN_SCHEMA` **7** 条（instrument_script×2、websocket、workflow_run×2、workflow_get、HTTP 端点清单）
  - `DESC_PROMISE` **5** 条（cdp_monitor 默认上限、ipc_clear、scheme、layer_tree、WS 地址）
  - `REQUIRED_MISMATCH` **4** 条（profile、websocket、ipc_queue、workflow_run）
  - `DECLARED_UNUSED` **2** 条（scan_crypto、detect_obfuscator 的 `script_index`）
  - `ACTION_MISMATCH` **1** 条（websocket query 语义）
- **机械核对结论**：用自写只读脚本对 44 个 reverse 工具逐分支、17 个 kernel 工具逐 `分派_*` 方法、4 个 workflow 工具逐处理函数做了「schema 声明属性集 vs 实际读取参数集」的双向 diff，**除上表所列外无其它** `DECLARED_UNUSED`／`MISSING_IN_SCHEMA`；kernel 17 个工具的声明集与读取集**完全相等**（`MCP_Kernel.wsv` 无多余声明、无未声明读取）。

### Top 15 待修清单（按"代理一次调用成功率"影响排序）

1. **`browser_reverse_instrument_script`** — `confirm` 未声明，而它是默认动作 `install` 的硬前置 → **空参/默认调用 100% 失败**（`MCP_Server_Reverse.wsv:1035`）。
2. **`workflow_run`** — `steps` 步骤对象字段表（skip/delay_ms/tool\|name/args\|arguments/wait_async/max_ms/on_error）全缺（`MCP_Server_Workflow.wsv:524-632`）→ 编排出错只能逐轮试。
3. **`browser_reverse_websocket`** — `action=query` 实际取 HTTP 响应体而非 WS 帧，且必需的 `request_id` 未声明（`MCP_Server_Reverse.wsv:420,433`）。
4. **`browser_kernel_reactor`** — 实现报错推荐 `load_end`，而该事件名**永不触发**，与工具描述自相矛盾（`MCP_Kernel.wsv:758` vs `MCP_Server.wsv:11351`）。
5. **`browser_kernel_events_all`** — `action=get` 实现完整且被实现自己推荐，schema 枚举却没有（`MCP_Kernel.wsv:1188,1257`）。
6. **`browser_kernel_watch`** — 唯一能读到"变化记录"的 `action=list`(changes_json) 未声明（`MCP_Kernel.wsv:983-1016`）。
7. **`browser_kernel_cdp_monitor`** — 未知/拼错 action 静默返回 list+success；`list` 亦未声明（`MCP_Kernel.wsv:671-697`）。
8. **`browser_kernel_cdp_monitor`** — max 默认值实际 200、描述写 500（`MCP_Kernel.wsv:577`）。
9. **`browser_kernel_reactor`** — 64 个合法事件名只声明 21 个，逼代理退化成 `*`（`MCP_BrowserEvents.wsv` 全量 vs `MCP_Server.wsv:11351`）。
10. **`browser_kernel_download`** — `action=list` 未声明（实现报错自己让用 list）（`MCP_Kernel.wsv:343,362`）。
11. **`browser_kernel_scheme`** — `file` 不存在时静默注册空内容 + success（`MCP_Kernel.wsv:412-415`）。
12. **`browser_reverse_scan_crypto`** — `script_index` 声明未用，静默全量扫描（`MCP_Server.wsv:11506` vs `MCP_Server_Reverse.wsv:606-615`）。
13. **`browser_reverse_detect_obfuscator`** — 同上（`MCP_Server.wsv:11508` vs `:725`）。
14. **`workflow_run` / `workflow_get`** — `file` 别名未声明（`MCP_Server_Workflow.wsv:277-280`、`:75-79`）。
15. **`browser_kernel_ipc_clear`** — "只能为 clear" 无校验，传错值返回 success 却不生效（`MCP_Kernel.wsv:548-570`）。

紧接其后的 16–19 位：`browser_reverse_layer_tree`（承诺"可看到"却无订阅前置）、`browser_reverse_dom_breakpoint`（timer 模式 target 枚举未文档化）、HTTP 端点自述清单缺 `/tools/brief`/`/metrics`、`browser_kernel_events_all` 扩展族名称少列 2 项。

## 4. 已复核并判定"**非缺陷**"的项（请勿重复修改，避免误报）

1. **`browser_kernel_cdp_monitor` 的 `Network.*` 通配**（任务提示的历史坑）：**当前源码已修复**。`MCP_Kernel.wsv:715` 先做 `模式=="*" || 模式==事件方法名 || 是否以 (事件方法名, 模式)`，随后 :723-732 显式处理尾部 `*`：`如果 (取文本右边 (模式,1)=="*") { 通配前缀 = 取文本左边 (模式, 取文本长度(模式)-1); 如果 (通配前缀!="" && 是否以 (事件方法名, 通配前缀)) { 命中 = 真 } }`，注释 :720-722 已写明原缺陷。工程内其它调用方也依赖该写法：`MCP_Server.wsv:5493` 用 `现有模式 == "Network.*"`、`MCP_Server_Core.wsv:5239` 建议 `browser_kernel_cdp_monitor action=add methods=Network.*`。→ **无需再改匹配规则**。
2. **`browser_reverse_instrument_script` 描述承诺的"未启用会自动启用并上报"**：成立，但由**公共层**完成——中央 `执行CDP并同步等待`（`MCP_Server.wsv:3222-3310`）对 `"agent is not enabled"` 反应式补 `<域>.enable` 并重试一次（:3255-3279），成功则经 `记录自动补域` 上报 `auto_prepared`。故 `:1054` 那句"请先 browser_debugger_enable"只在自动补域也失败时才出现，**不是文实不符**。
3. **公共层参数**：`max_ms`（`MCP_Server.wsv:6137-6152`，上限 300000）、`async_only`(:1584,:5960,:6829)、`sync_wait`(:5964)、`browser_id`/`auto_enable` 等由入口统一读取，**未**按 `MISSING_IN_SCHEMA` 计入（符合"不要误报公共层"要求）；`browser_reverse_*` 的 `max_ms` 统一经 `取同步等待毫秒 (方法名, 参数JSON)` 生效（如 `MCP_Server_Reverse.wsv:617,680,734,819,916,963`）。
4. **`browser_kernel_events_all` 的"与 browser_collect action=event_all_enable 的集合完全一致"**：**成立**。`MCP_Kernel.wsv:1193-1222`（enable 28 项）与 `MCP_Server_Core.wsv:4091-4118`（event_all_enable 28 项）逐项同名同序，`:1227-1254` 与 `:4128-4155` 亦逐项对称；`13 事件族 + 3 日志 + 12 扩展族 = 28` 计数正确（仅扩展族**名称**少列 2 项，见差异表）。
5. **`browser_kernel_cdp_monitor` 描述"配合 browser_cdp_event 读取捕获到的事件"**：成立——`MCP_Server.wsv:2386` 对**每个** CDP 事件无条件 `存储异步结果 ("cdp_event:" + 事件方法名, 参数字段)`，`browser_cdp_event`（`MCP_Server_Core.wsv:5111-5145`）读的正是 `cdp_event:<名>`，与本工具的订阅状态无关。
6. **`browser_reverse_call_fn` 的 `arguments` / `args`**：两者都声明且都真读（`MCP_Server_Reverse.wsv:310` `yyjson取JSON文本 (参数JSON,"arguments")`、:312 `yyjson取文本 (参数JSON,"args")`），**不是** `DECLARED_UNUSED`。
7. **`workflow_run` 的 `definition` / `steps` 顶层键**：都真读，只是读点在辅助方法里（`steps` → `解析步骤数组参数` `MCP_Server_Workflow.wsv:648-682`；`definition` → `加载工作流定义` :294-305 与 :301 `参数JSON.取对象 ("definition")`），**不是** `DECLARED_UNUSED`（按分支体做机械 diff 会误判，已复核）。
8. **`workflow_list` / `workflow_stop` 无 schema**：`MCP_Server.wsv:11331,11334` 只传 2 参 → 落到 `添加工具JSON` 第 3 参缺省 `"inputSchema":{"type":"object"}`（:11605），与"这两个工具无入参"一致，**非缺陷**。
9. **`browser_reverse_*` 中 11 个工具不在本文件实现**（hook/strings/verify/cookie_sources/env/instrument/search/extract/initiator/setup/preset）：前缀路由命中本文件的分派器后返回 `""`（`MCP_Server_Reverse.wsv:2369`），再按回退链落到 `MCP_核心分派`（`MCP_Server.wsv:12167-12169`）→ 已确认它们在 `MCP_Server_Core.wsv` 有实现，**不是**孤儿工具。
10. **`browser_kernel_events_all` 描述里 "28 个开关" 与实现一致**：见第 4 条。
11. **`browser_reverse_input_cdp`**：schema 10 个属性（kind/type/x/y/button/delta_x/delta_y/key/windows_virtual_key_code/text）与实现读取集**完全相等**（`MCP_Server_Reverse.wsv:1990-2052`），无差异。
12. **`browser_reverse_search_script` / `get_possible_breakpoints` / `listeners` / `query_objects` / `patch` / `set_variable` / `detect_traps`** 等：声明集 == 读取集（机械 diff 无差异），且描述承诺的"零前置自动补（`确保脚本注册表就绪`）"在实现里确有（`:1318,1470,1624,2150`）。

## 5. 静态不可判定 / 建议实测的项（不计入 29 条）

1. **`browser_kernel_download` 的 `download_id` 匹配**：操作侧存的是 `{action,url,id}`（`MCP_Kernel.wsv:345-349`），消费侧 `匹配ID == 下载标识`（:1805）而 `下载标识 = 到文本 (下载.取关联标识符 ())`（`MCP_BrowserEvents.wsv:865`）；事件记录里 `download_id` 是以**整数**成员写入的（`MCP_BrowserEvents.wsv:659`）。若调用方按事件里的数值形态传 `download_id`（schema 声明为 text），`yyjson取文本` 对数字成员是否返回其文本形态将决定匹配成败——纯静态无法判定，建议实测两种形态（`"123"` 与 `123`）。
2. **`browser_kernel_cdp_monitor` 的 `methods` 写裸域名**：`MCP_Kernel.wsv:619-628` 只在模式里存在 `.` 时才自动 `<域>.enable`（`监控点 > 0`）；传 `methods:"Network"`（不带点）既不精确匹配任何事件、也不触发自动补域 → 订阅成功但 events 恒空。描述只给了 `*` 与 `Network.*`，故未计入差异表，但属"静默空结果"风险，建议在描述里点明"通配必须带 `.*`"。
3. **`browser_kernel_reactor action=add` 的隐式副作用**：`MCP_Kernel.wsv:782-785` 会自动调用 `分派_全事件流 (…enable)` 把 **28 个**事件/日志开关全部打开（并经 `记录自动处理` 上报）。描述未提这一副作用（注释 :778-781 解释了原因）。属"实现了但未写入描述"，因六类差异类型无以精确归类，仅在此列出。
4. **`browser_reverse_dom_breakpoint type="fetch"`**：`:121` 与 `xhr` 合并为同一分支（同发 `DOMDebugger.setXHRBreakpoint`，url 缺省 `*`）；Chromium 的 XHR 断点确实同时覆盖 fetch，故未计为差异，但描述"fetch=拦截fetch"给人的"独立 fetch 拦截"印象与实际实现（同一断点）略有落差。
5. **`browser_kernel_watch` 的 `interval_ms` 语义**：描述/schema 写"最小500, 默认2000"，实现 `:913-916` 是 `如果 (间隔 < 500) { 间隔 = 2000 }`（不足 500 时回落成 2000 而非夹到 500），响应里会回显实际值（:946），属可接受的诚实实现，未计为差异。
6. **`MCP_Server_HTTP.wsv` 的方法校验不齐**：`/metrics`、`/health`、`/api`、`/docs`、`/json*`、`/tools*` 等分支位于 POST 分支之后且**不校验 HTTP 方法**，故 `PUT /health` 会 200，而 `POST /health` 会 404（:91-121 先返回）。非 schema 文字差异，仅记录为健壮性观察。
