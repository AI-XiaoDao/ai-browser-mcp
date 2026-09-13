# 失败项分类与处置 (failure triage)

> 只读静态分析。**未编译、未调用任何 MCP 工具、未改动任何源文件**（本文件是本次唯一的写入）。
> 所有分类都是"读代码 + 读台账"得出的判断；下文所有"建议值"**均未验证**，由主 agent 施加并实测。

## 0. 快照与前提（重要）

- 数据源：`_audit/_tool_ledger.json`（机读）与 `_audit/_tool_ledger.md`（人读）。
- **本次快照**：`_tool_ledger.json` mtime = `09-13 04:51:12`，size = `117141`，`status != pass` 的记录 **41** 条（与任务描述的"约 41"一致）。
- **该文件正在被并发修改**：我开始读时（04:50:45，size 116903）是 **44** 条失败；04:51:12 时变成 41 条 ——
  `browser_fill_form` / `browser_reverse_await_promise` / `browser_reverse_query_objects` 三条已在 04:51 由主 agent 施加覆盖后转通过
  （`mass_probe.py` 同时从 389 行长到 406 行，新增了 `browser_reverse_query_objects: {"prototype_expression": "Array.prototype"}`、
  `browser_reverse_await_promise: {"expression": "Promise.resolve(1)"}`、`browser_fill_form` 的 `#mcpProbeInput` 注入前置）。
  → **下表以 41 条为准**；三条已转通过者不再列出（其分类与本文档提出的方案一致，可视为已完成的样板）。
- 复验（写完本文档后）：`_tool_ledger.json` mtime 已推进到 `09-13 04:55:57`（size 117538），但**失败集合与本文档完全一致（仍是同样 41 个）**，
  且这 41 条的 `args`/`note` 逐字未变（失败项 args 摘要 md5 = `017bbcdf12c0ec02fa01fc780ce02079`，失败项时间戳范围 `09-13 01:26 ~ 04:49`）——
  期间只有 pass 记录被更新。**本文档引用的 41 条失败原文即当前台账原文。**
- `.md` 是只追加的历史，含 85 个曾失败工具；以 `.json` 的**每工具最新一条**为准（例如 `workflow_run`、`browser_dom_select` 在 `.md` 里各有失败行，`.json` 里已是 pass）。
- 派发路径（`src/MCP_Server.wsv:10550-10581` 前缀直投 + 10583-10606 回退链）：
  `browser_fill_*`→`MCP_Server_Form.wsv`；`browser_vip_*`/`browser_fingerprint_*`→`MCP_Server_VIP.wsv`；`workflow*`→`MCP_Server_Workflow.wsv`；
  `browser_reverse_*`→`MCP_Server_Reverse.wsv`（本批 6 个失败项在该文件**都有显式分支**，没有落到 Core）；`browser_kernel_*`→`MCP_Kernel.wsv`；
  `browser_set_window_style`→`MCP_Server_System.wsv`；其余→`MCP_Server_Core.wsv`。
  （`src/MCP_Server.wsv` 是注册表/入口，不是这些工具的实现分支所在。）

### 0.1 一个必须先修的结构性障碍（影响 A 类落地）

`_audit/mass_probe.py:274-279`（`build_args` 的覆盖循环）仍是：

```python
for pname, v in (TOOL_ARG_OVERRIDES.get(tool_name) or {}).items():
    if pname in props:          # ★ 参数不在 schema.properties 里 -> 覆盖被静默丢弃
```

而 `browser_file_dialog` 与 `browser_forward` 的 `inputSchema` **完全没有 properties**（见 `_audit/_tools_list.json`：
`browser_file_dialog` = `{"type":"object"}`；`browser_forward` = `{"type":"object"}`）。
→ 给这两个工具写的 `TOOL_ARG_OVERRIDES` 会被这行静默吞掉（不会报错、不会进 note，台账上看不出).
**必须先把 `if pname in props` 改成无条件赋值**（或在注册表里给这两个工具补上 properties），否则下面 A-4 的第 1 条永远无效。
`TOOL_PRE_CALLS` 不受影响：`tool_ledger.py:92-99` 把 `_pargs` 原样发出，不经过 `build_args`。

### 0.2 分类口径（本文档自用的判定规则，便于复核）

- **A / TEST ARTIFACT**：失败由探针的通用占位值或缺状态造成，**且**能给出一个具体、可静态写死的无害覆盖值/前置序列（写不死的不算 A）。
- **B / 合法且可行动**：失败落在 参数非法 / 目标不存在 两类内，且消息本身已经告诉调用方怎么继续；或"值只能运行时取得""施加覆盖本身有害"而**不应**覆盖。
- **C / 真实缺陷**：调用方无法合理修复，或消息不可行动/误导。

---

## 1. (a) 41 个失败工具逐条分类与证据

> "失败原文"一律照抄台账 `note` 字段（台账 `tool_ledger.py:112` 截断到 300 字符；凡截断处标 `…(台账截断)`）。
> 路由列给出"分派行 / 产出该消息的实现行"。

| # | 工具 | 分类 | 失败原文（逐字） | 证据（file:line） | 处置 |
|---|---|---|---|---|---|
| 1 | `browser_dom_query` | **A** | `元素不存在或取不到值: #mcp-probe-nonexistent \| 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在` | 分派 `src/MCP_Server_Core.wsv:1688`；消息 `.../MCP_Server_Core.wsv:1715` | 覆盖 `selector` 为 `h1`（A-1） |
| 2 | `browser_dom_click` | **A** | `element not found: #mcp-probe-nonexistent \| 该选择器在当前页面上匹配到 0 个元素 \| 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择器, 注意 iframe 内元素需先切换框架, 元素可能在滚动后才加载` | 分派 `MCP_Server_Core.wsv:1755`；消息 `src/MCP_Callbacks.wsv:161` | 覆盖 `selector` 为 `h1`（A-1） |
| 3 | `browser_dom_rect` | **A** | `元素不存在或取不到值: #mcp-probe-nonexistent \| 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在` | 分派 `MCP_Server_Core.wsv:1890`；消息 `:1908` | 覆盖 `selector` 为 `h1`（A-1） |
| 4 | `browser_dom_inner_html` | **A** | 同上（`元素不存在或取不到值: #mcp-probe-nonexistent …`） | 分派 `MCP_Server_Core.wsv:1931`；消息 `:1949` | 覆盖 `selector` 为 `h1`（A-1） |
| 5 | `browser_dom_checked` | **A** | 同上（`元素不存在或取不到值: #mcp-probe-nonexistent …`） | 分派 `MCP_Server_Core.wsv:1972`；消息 `:1990` | example.com **无 checkbox** → 前置注入 `#mcpProbeCheck`（A-2） |
| 6 | `browser_dom_selected` | **A** | 同上（`元素不存在或取不到值: #mcp-probe-nonexistent …`） | 分派 `MCP_Server_Core.wsv:2017`；消息 `:2035` | example.com **无 `<select>`** → 前置注入 `#mcpProbeSelect`（A-2） |
| 7 | `browser_dom_set_value` | **A** | `元素不存在或取不到值: #mcp-probe-nonexistent \| 设置值未执行 \| 建议: 先用 browser_snapshot 或 browser_get_forms 确认元素存在` | 分派 `MCP_Server_Core.wsv:1786`；消息 `:1810` | example.com **无 input** → 注入 `#mcpProbeInput`（A-2） |
| 8 | `browser_fill_set_value` | **A** | `设置值未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent \| 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择器; 注意 iframe 内元素需先切换框架, 元素可能在滚动后才加载` | 分派 `src/MCP_Server_Form.wsv:12`；消息（前置存在校验）`MCP_Server_Form.wsv:581` | 同 #7（A-2） |
| 9 | `browser_fill_click` | **A** | `点击未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent \| …` | 分派 `MCP_Server_Form.wsv:43`；消息 `:581` | 覆盖 `selector`=`h1`（A-1） |
| 10 | `browser_fill_focus` | **A** | `设置焦点未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent \| …` | 分派 `MCP_Server_Form.wsv:72`；消息 `:581` | 覆盖 `selector`=`h1`（A-1） |
| 11 | `browser_fill_scroll` | **A** | `滚动到元素未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent \| …` | 分派 `MCP_Server_Form.wsv:101`；消息 `:581` | 覆盖 `selector`=`h1`（A-1） |
| 12 | `browser_fill_trigger` | **A** | `触发事件未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent \| …` | 分派 `MCP_Server_Form.wsv:276`；消息 `:581` | 覆盖 `selector`=`h1`（`event` 缺省=`click`，`:282-285`）（A-1） |
| 13 | `browser_fill_select` | **A** | `设置select选中项未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent \| …` | 分派 `MCP_Server_Form.wsv:311`；消息 `:581`（另 `value` 空守卫在 `:335-337`） | 注入 `#mcpProbeSelect` + `value`（A-2） |
| 14 | `browser_fill_attr_get` | **A** | `元素不存在或取不到值: #mcp-probe-nonexistent \| 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在` | 分派 `MCP_Server_Form.wsv:206`；消息 `:235`（原值 `attribute=mcp_probe` 即使元素修好也会撞 `:237-240`「属性不存在」） | 覆盖为 `selector:"a", attribute:"href"`（A-3） |
| 15 | `browser_fill_attr_set` | **A** | `attribute 不能为空 \| 如 style / data-* / aria-*` | 分派 `MCP_Server_Form.wsv:158`；消息 `:173`（`attribute` 在 schema 里是**可选**，探针从不填） | 覆盖 `attribute`/`value`（A-3） |
| 16 | `browser_wait` | **A** | `value 不能为空: what=selector 需要指定等待目标值` | 分派 `MCP_Server_Core.wsv:2675`；消息 `:2717` | 覆盖 `what=selector,value=h1`（A-4） |
| 17 | `browser_intercept` | **A** | `参数 url 不能为空` | 分派 `MCP_Server_Core.wsv:2422`；消息 `:2504`（`url` 是可选参数，但规则类分支必需；同文件 `:2428` 的注释自己承认这条消息"与真实原因无关"） | 覆盖 `action=clear`（A-4）；**附带消息改进建议**见 §3.3 |
| 18 | `browser_file_dialog` | **A** | `文件对话框已改为程序化选择(不弹窗口) \| 请传 path 参数指定目标文件路径` | 分派 `MCP_Server_Core.wsv:5779`；消息 `:5790` | 覆盖 `path`（**依赖 §0.1 的 build_args 修复**）（A-4） |
| 19 | `workflow_get` | **A** | `工作流不存在: mcp_probe \| 建议: 先用 workflow_list 列出可用工作流名(不含 .json 后缀)` | 分派 `src/MCP_Server_Workflow.wsv:72`；消息 `MCP_Server_Workflow.wsv:258`（在 `处理_工作流获取`，`:242` 起） | 覆盖 `name=hello`（真实存在，见 A-4 依据） |
| 20 | `browser_cdp_call` | **A** | `非法 CDP 方法名: mcp_probe \| 规范格式为 域.方法, 例: Network.getResponseBody / Runtime.evaluate / Page.navigate / Debugger.enable \| 无点号的方法名不会得到内核响应, 会长时间挂起并阻塞其它请求, 故直接拒绝` | 分派 `MCP_Server_Core.wsv:4459`；消息 `:4468` | 覆盖 `method=Runtime.evaluate`（A-4） |
| 21 | `browser_cdp_event` | **A** | `指定 event_name 或 event 参数，例如 Debugger.paused` | 分派 `MCP_Server_Core.wsv:4549`；消息 `:4596`（缓存命中路径 `:4557-4577`） | 覆盖 `event_name=Debugger.paused` + 前置 `browser_debugger_stack`（A-5） |
| 22 | `browser_kernel_auth` | **A** | `host 不能为空 \| 例: example.com` | 分派 `src/MCP_Kernel.wsv:68` → `分派_认证管理` `:209`；消息 `MCP_Kernel.wsv:221` | 覆盖 `action=list`（文档内枚举，只读；成功分支 `:297-321`）（A-4） |
| 23 | `browser_kernel_scheme` | **A** | `domain 不能为空 \| 访问形式: mcp://域名/任意路径` | 分派 `MCP_Kernel.wsv:80` → `分派_方案管理` `:391`；消息 `:403` | 覆盖 `action=list`（成功分支 `:483-507`）（A-4） |
| 24 | `browser_kernel_reactor` | **A** | `event 不能为空 \| 例: load_end / navigate / url_changed / *` | 分派 `MCP_Kernel.wsv:100` → `分派_反应器` `:746`；消息 `:758`（同分支 `:762-765` 还要求 `code`） | 覆盖 `action=clear`（`clear` 分支 `:788-793`；未注册时是空操作）（A-4） |
| 25 | `browser_kernel_watch` | **A** | `expression 不能为空 \| 例: document.title / window.__token` | 分派 `MCP_Kernel.wsv:108` → `分派_定时监视` `:891`；消息 `:903` | 覆盖 `action=clear`（`:975-982`）（A-4） |
| 26 | `browser_vip_execute_js_context` | **A** | `需要code参数` | 分派 `src/MCP_Server_VIP.wsv:1405`；消息 `:1436` | 覆盖 `code=document.title`（`code` 非空即走实现并回异步 task_id，`:1409-1432`）（A-4） |
| 27 | `browser_vip_dom_search` | **A** | `需要query或search_id参数` | 分派 `MCP_Server_VIP.wsv:1466`；消息 `:1501` | 覆盖 `query="Example Domain"`（A-4） |
| 28 | `browser_forward` | **A（带条件）** | `无法前进 — 无导航历史 \| 当前页面没有可前进的历史记录` | 分派 `MCP_Server_Core.wsv:208`；消息 `:221`（判据 `browser.可否前进()` 于 `:212`） | 前置构造前进历史（A-5）；**若实测 `可否前进` 仍为假 → 升级为 C**，见 §4-1 |
| 29 | `browser_reverse_return_value` | **A（带条件）** | `页面未处于暂停态 \| 该工具只在 Debugger.paused 时有效: 先设断点/插装并触发暂停, 再用 browser_debugger_wait_paused 确认` | 分派 `src/MCP_Server_Reverse.wsv:1200`；消息 `:1212`（判据 `取CDP事件数据JSON("Debugger.paused")==""`） | 前置 `browser_debugger_stack`（A-5）；残留不确定见 §4-2 |
| 30 | `browser_reverse_set_variable` | **A（带条件）** | `页面未处于暂停态且未提供 call_frame_id \| 先在断点处暂停, 或用 browser_debugger_get_stack 取 call_frame_id` | 分派 `MCP_Server_Reverse.wsv:1218`；消息 `:1243` | 前置 `browser_debugger_stack`（A-5）；`variable_name` 仍需真值，见 §4-2 |
| 31 | `browser_find_by_tag` | **C** | `未找到标识为: mcp_probe 的浏览器 \| 可能原因: 该标识未被 browser_user_tags 设置过, 或浏览器已关闭 \| 建议: 先用 browser_list 查看现有浏览器及其 id` | 分派 `MCP_Server_Core.wsv:5577`；消息 `:5605`；`browser_user_tags` 只读（`MCP_Server_Core.wsv:5947-5965`，工具描述就是"列出用户标识"），`browser_create` 的 schema 只有 `url`/`background`（`_tools_list.json`） | 见 §3-1 |
| 32 | `browser_find_by_hwnd` | **C** | `未找到窗口句柄为 1 的浏览器` | 分派 `MCP_Server_Core.wsv:5918`；消息 `:5945` | 见 §3-2 |
| 33 | `browser_reverse_precise_coverage` | **C** | `Profiler.takePreciseCoverage 失败: Precise coverage has not been started.` | 分派 `src/MCP_Server_Reverse.wsv:1129`；默认动作 `take` 于 `:1136-1139`；CDP 调用 `:1155`；原始错误透传点 `MCP_Server_Reverse.wsv:2249`（`执行V8CDP命令`） | 见 §3-3 |
| 34 | `browser_network_body` | **B** | `非法 CDP request_id: mcp_probe \| CDP 请求标识为数字串(形如 1000012345.5) \| 如何取得有效值: ① browser_kernel_cdp_monitor action=add methods=Network.* 订阅 ② browser_cdp_event event_name=Network.requestWillBeSent 取其中的 requestId ③ 再调用本工具 \| 注意: …(台账截断)` | 分派 `MCP_Server_Core.wsv:4610`；消息 `:4623` | 参数非法 + 三步取值的可行动说明；值只能运行时取得 → 不做覆盖 |
| 35 | `mcp_result` | **B** | `未找到任务结果: mcp_probe \| 可能原因: ①任务仍在执行(2-5秒后重试) ②request_id拼写错误 ③任务已过期被清理 \| 💡大多数工具已默认sync-wait(直接返回结果), 无需手动mcp_result轮询` | 分派 `MCP_Server_Core.wsv:3773`；消息 `:4363` | 目标不存在 + 三条原因 + 替代做法；task_id 是运行时值 → 不做覆盖 |
| 36 | `browser_debugger_flow` | **B** | `debugger_flow 失败: {"ok":false,"step":"wait_paused","error":"timeout","breakpoint":"mcp_probe","waited_ms":12000,"reason":"等待 Debugger.paused 超时(12000ms) \| 未传 url: 本工具不会导航, 只有当前页面自己执行到断点位置才可能命中","hint":"可行动: ①用 browser_re…(台账截断)` | 分派 `MCP_Server_Core.wsv:4999`；消息 `:5013`（内层 JSON 由 `执行Debugger断点流程JSON` 产出） | 目标不存在（无脚本匹配该正则）+ hint 已给替代路径；本机无法静态构造通过（见 §5-①） |
| 37 | `browser_debugger_auto` | **B** | `未捕获到任何断点命中(0 hits) \| 停止原因: 等待 Debugger.paused 超时(12000ms): 该窗口内页面未执行到断点位置 \| 注: 下断当时该 urlRegex 匹配到 0 个脚本位置(locations 为空) —— 若之后有带真实 URL 的脚本加载仍可能命中, 可传 url 让本工具导航触发, 或显式传更大的 max_ms 继续等 \| 常见原因: ①…(台账截断)` | 分派 `MCP_Server_Core.wsv:5042`；消息 `:5192` | 同上；`urlRegex` 是 URL 正则占位值，但本机页面无脚本（`browser_reverse_search_script` 台账 `count:0`）→ 无法静态构造通过 |
| 38 | `browser_set_window_style` | **B** | `非法窗口属性类型(1) \| 支持: -16(GWL_STYLE) / -20(GWL_EXSTYLE) / -12(GWL_ID)` | 分派 `src/MCP_Server_System.wsv:71`；消息 `:82` | 参数非法 + 明确列出合法域；`mass_probe.py:165-169` **已明确决定不覆盖**（改宿主窗口样式有真实副作用），保持一致 |
| 39 | `browser_vip_enable_js_env` | **B** | `启用 JS 执行环境需显式确认 \| ⚠ 实测启用后会破坏本会话的 JS 通道: CDP 优先工具(browser_dom_query / browser_dom_rect / browser_get_text 等)会退化为 null, browser_execute_js 也会超时, 且注销/重注册监管者与重新导航均无法恢复, 只有重启进程才能恢复。确认要继续请传 confirm:true` | 分派 `src/MCP_Server_VIP.wsv:250`；消息 `:269`（缺 `enable` 的守卫在 `:261-264`） | 显式确认闸门（防"缺省=破坏"）+ 完整后果与确认方式；**不应**覆盖 |
| 40 | `browser_reverse_instrument_script` | **B** | `install 需要显式确认 \| 实测: 装上后本会话的 **JS 通道即被阻塞**(browser_execute_js / browser_debugger_last_paused 等 30s 超时; browser_status 仍正常, 它走原生不经 CDP), 且 browser_debugger_resume 与 action=suppress **都无法恢复**, 只有重启进程才能恢复 \| 若确实要用(在脚本执行前拦截原始源码), 请传 confirm:true, 并**准备好随后重启进程** \| 只是想读源码/定位脚本, 可改用 browser_reverse_search_script / …(台账截断)` | 分派 `src/MCP_Server_Reverse.wsv:886`；消息 `:923`（默认动作 `install` 于 `:897-900`） | 同上：默认动作具破坏性 → 显式确认闸门；**不应**覆盖 |
| 41 | `browser_vip_mouse_wheel` | **B** | `必须提供 delta_y 或 delta_x (滚动量, 正值向下/向右) \| 省略会造成滚动 0 像素却报成功` | 分派 `src/MCP_Server_VIP.wsv:826`；消息 `:843`（同为 Core 的 `browser_mouse_wheel` 走 `MCP_Server_Core.wsv:1308`，文案是"正**数**"，台账原文是"正**值**"→ 确系 VIP 分支产出） | 参数非法 + 可行动。**建议不做覆盖**：该工具只有内核注入一条路（`vip_ctrl.高级鼠标_滚轮滚动`，无 CDP 选项），其自身描述与台账都记载"每次调用都会让 CDP 通道在本会话内失效"，施加覆盖会污染同批其它 CDP 工具的测量 |

合计：**A = 30，B = 8，C = 3**（41）。

---

## 2. (b) A 类：建议施加的 TOOL_ARG_OVERRIDES / TOOL_PRE_CALLS

> 全部**未验证**。所有"页面真实存在"的依据都来自台账自身已通过的记录（不是猜测）：
> - `browser_highlight {selector:"h1", action:"show", duration_ms:100}` → `{"highlighted":1,…}`（台账 04:43，round 111，**已通过**）
> - `browser_reverse_dom_resolve {selector:"h1"}` → `object_id` 非空（台账 04:49，round 116，**已通过**）
> - `browser_get_text` 全文含 `Example Domain` … `Learn more`（台账 03:37）
> - `browser_snapshot` elements[0] = `{"i":0,"tag":"a","text":"Learn more",…}`（台账 04:43）
> - `browser_fill_form` 用 `#mcpProbeInput`（`browser_execute_js` 注入）已实测转通过（台账 04:51）→ **注入式前置这条路线在本机已被证明可行**
> ⇒ 当前测试页是 example.com 现行版本：`<h1>Example Domain</h1>` + 两段 `<p>` + `<a href="…">Learn more</a>`；**没有** input / checkbox / select / form。

### A-1 读/交互类：`selector = "h1"`

```python
TOOL_ARG_OVERRIDES.update({
    "browser_dom_query":      {"selector": "h1"},
    "browser_dom_rect":       {"selector": "h1"},
    "browser_dom_inner_html": {"selector": "h1"},
    "browser_dom_click":      {"selector": "h1"},
    "browser_fill_click":     {"selector": "h1"},
    "browser_fill_focus":     {"selector": "h1"},
    "browser_fill_scroll":    {"selector": "h1"},
    "browser_fill_trigger":   {"selector": "h1"},
})
```
理由：`h1` 被两次独立实测证明存在（见上）。点击/触发 `h1` 上没有任何事件处理器，不会导航、不会改页面（对比：点 `a` 会跳到 iana.org，污染后续测量，**不要**用 `a` 做点击类）。`browser_dom_click` 的存在性回调成功后一律回 `已点击(原生)`（`MCP_Callbacks.wsv:143-153`），不要求元素可交互。

### A-2 需要"真实可写控件"的 5 个：注入一次，再指向注入的元素

example.com 上**不存在** input/checkbox/select，因此这几个工具**无论给什么 `selector` 都无法打到实现**（给 `h1` 只能测出"不是 checkbox/不是 select"的次级守卫，见 `MCP_Server_Core.wsv:1992-1995`、`:2037-2040`）。用与 `browser_fill_form` 相同的注入式前置（延续主 agent 已用的 `mcpProbe*` 命名，避免与页面元素冲突）：

```python
_TOUCH_PROBE_JS = (
    "(function(){"
    "if(document.getElementById('mcpProbeSelect'))return 'exists';"
    "var i=document.createElement('input');i.id='mcpProbeInput';i.type='text';document.body.appendChild(i);"
    "var c=document.createElement('input');c.id='mcpProbeCheck';c.type='checkbox';document.body.appendChild(c);"
    "var s=document.createElement('select');s.id='mcpProbeSelect';"
    "var o1=document.createElement('option');o1.value='mcpA';o1.text='A';s.appendChild(o1);"
    "var o2=document.createElement('option');o2.value='mcpB';o2.text='B';s.appendChild(o2);"
    "document.body.appendChild(s);return 'made';})()"
)
_TOUCH_PRE = ("browser_execute_js", {"code": _TOUCH_PROBE_JS})

TOOL_PRE_CALLS.update({
    "browser_dom_checked":   [_TOUCH_PRE],
    "browser_dom_selected":  [_TOUCH_PRE],
    "browser_dom_set_value": [_TOUCH_PRE],
    "browser_fill_set_value":[_TOUCH_PRE],
    "browser_fill_select":   [_TOUCH_PRE],
})
TOOL_ARG_OVERRIDES.update({
    "browser_dom_checked":    {"selector": "#mcpProbeCheck"},
    "browser_dom_selected":   {"selector": "#mcpProbeSelect"},
    "browser_dom_set_value":  {"selector": "#mcpProbeInput", "value": "mcp-test"},
    "browser_fill_set_value": {"selector": "#mcpProbeInput", "value": "mcp-test"},
    "browser_fill_select":    {"selector": "#mcpProbeSelect", "value": "mcpA"},
})
```
理由链：
- `browser_dom_checked`：CDP 路径要求 `'checked' in e`（`MCP_Server_Core.wsv:1983`）→ 只有 checkbox/radio 能过；注入的 `#mcpProbeCheck` 就是 checkbox。
- `browser_dom_selected`：要求 `e.tagName === 'SELECT'`（`:2028`）→ 注入的 `#mcpProbeSelect`。
- `browser_dom_set_value`：走原型 setter + 回读比对（`:1805-1821`），`<input>` 上回读等于写入值 → `{"success":true,"verified":true}`。
- `browser_fill_set_value`：原生 `置元素内容`（`MCP_Server_Form.wsv:36`），先把守卫 `前置存在校验` 过掉即可。
- `browser_fill_select`：`value` 必须非空（`MCP_Server_Form.wsv:335-337`），且选项值 `mcpA` 是刚注入的 option 的 value；主框架有效时走 JS setter + input/change 事件链（`:341-351`）。
- 注入的 JS 只用单引号，可安全放进 JSON/Python 双引号字符串；幂等（已存在则直接返回 `exists`）。

### A-3 需要真实 HTML 属性的 2 个

```python
TOOL_ARG_OVERRIDES.update({
    "browser_fill_attr_get": {"selector": "a", "attribute": "href"},
    "browser_fill_attr_set": {"selector": "a", "attribute": "data-mcp-probe", "value": "1"},
})
```
理由：页面上的 `<a href="…">Learn more</a>` 必然带 `href`（`browser_snapshot` 与 `browser_get_text` 双重佐证），所以 `getAttribute('href')` 返回真值而不是 `__MCP_NO_ATTR__`（`MCP_Server_Form.wsv:237-240`）。
`attribute` 在 schema 里是可选（`_tools_list.json`：`browser_fill_attr_set.required=["selector"]`）→ 探针从不填，撞 `:170-174` 的守卫；`data-mcp-probe` 不在禁用名单（禁用 `href/src/action/formaction/on*`，`:177-184`）。

### A-4 缺"语义必填"入参的守卫类

```python
TOOL_ARG_OVERRIDES.update({
    "browser_wait":            {"what": "selector", "value": "h1"},
    "browser_intercept":       {"action": "clear"},
    "browser_file_dialog":     {"path": r"C:\Windows\win.ini"},          # ★ 需先修 §0.1
    "workflow_get":            {"name": "hello"},
    "browser_cdp_call":        {"method": "Runtime.evaluate",
                                "params": "{\"expression\":\"1\",\"returnByValue\":true}"},
    "browser_kernel_auth":     {"action": "list"},
    "browser_kernel_scheme":   {"action": "list"},
    "browser_kernel_reactor":  {"action": "clear"},
    "browser_kernel_watch":    {"action": "clear"},
    "browser_vip_execute_js_context": {"code": "document.title"},
    "browser_vip_dom_search":  {"query": "Example Domain"},
})
```
逐条理由：
- `browser_wait`：`value` 可选但 `what=selector` 必需（`MCP_Server_Core.wsv:2715-2717`）；`h1` 存在，所以等到的条件是真的（该工具是异步提交型，守卫一过即回 task_id）。
- `browser_intercept`：`action` 已由枚举抽取给了 `modify`，`url` 却缺失 → 落到规则分支报"参数 url 不能为空"（`:2500-2504`）。取**只读无副作用**的 `clear`（`:2430-2445`，当前无规则时是空操作，可逆）；若更想测真实替换链路，可用
  `{"action": "replace_data", "url": "example.com", "replace_text": "<html>mcp-probe</html>"}` —— 但那会真的改写响应体，**不推荐**。
- `browser_file_dialog`：schema 无 properties → 探针一个参数都不发。`C:\Windows\win.ini` 必然存在，且读操作路径校验 `验证安全路径(路径, 假)` 只拒绝路径穿越（`MCP_Server.wsv:8160-8187`）→ 会走到 `:5800-5804` 回 `{"success":true,"selected":…}`。
- `workflow_get`：依赖 §0.1 之外的另一个前提 —— 只是名字必须是真实工作流。`workflow_list` 台账（round 13）返回 `["automation_form","debugger_breakpoint","debugger_full","hello","ping_navigate","reverse_analyze"]`（**已通过**），取最小的 `hello`。
- `browser_cdp_call`：守卫只要求"含点号"（`MCP_Server_Core.wsv:4466-4468`）。`Runtime.evaluate` 在本机已被 `browser_reverse_runtime` 实测可用（台账 pass），且项目已有"域未启用时反应式自动补齐并重试一次"的机制（`MCP_Server_Reverse.wsv:2237-2240` 注释 + `MCP_Server.wsv:1556+`）；`expression:1` 无副作用。备选（更轻但 CEF 覆盖度不确定）：`{"method": "Browser.getVersion"}`。
- `browser_kernel_auth` / `browser_kernel_scheme`：`list` 就在各自 `action` 描述里（`set/clear/list`、`register/unregister/clear/list`），成功分支分别 `MCP_Kernel.wsv:297-321`（回 `credentials`）与 `:483-507`（回 `schemes`）。比 `set`/`register` 少一大截副作用（不写凭据表、不注册资源处理器）。
- `browser_kernel_reactor` / `browser_kernel_watch`：`add` 还要 `code`（`MCP_Kernel.wsv:760-765`），`start` 还要 `expression`（`:899-904`），而 `add` 会**自动打开全部事件族**（`:778-786`，会改变本会话的事件日志量），`start` 会留一个常驻 2s 轮询器。→ 取文档内的 `clear`（`:788-793` / `:975-982`，无注册时是空操作）。
  补充：这两个实现都**已支持未写入文档的 `list` 只读分支**（`:794-799` / `:983-1016`，含 `changes_json`）。用 `{"action": "list"}` 副作用更小、信息更多；但因为它不在 `action` 描述里，建议**同时把 `list` 补进工具描述**（属小幅文档缺陷，见 §4-3）。
- `browser_vip_execute_js_context`：`code` 非空即走实现（`MCP_Server_VIP.wsv:1409-1432`），无 `context_id`/`frame_id` 时用 `ctxID=0`；给只读的 `document.title`，与 `browser_execute_js`/`browser_evaluate` 的既有覆盖同款。
- `browser_vip_dom_search`：`query` 非空即走 `预查找文本` 异步提交（`:1470-1497`）；"Example Domain" 在页面上真实出现（标题与 h1），即便查不到也不会报错，纯粹无害。

### A-5 需要"先造状态"的 4 个（TOOL_PRE_CALLS）

```python
TOOL_ARG_OVERRIDES.update({
    "browser_cdp_event": {"event_name": "Debugger.paused"},
})
TOOL_PRE_CALLS.update({
    # 与已有的 browser_debugger_wait_paused 完全同款手法: stack 会触发零前置自动暂停,
    # 之后 Debugger.paused 会被写入 cdp_event:Debugger.paused 异步缓存。
    "browser_cdp_event": [("browser_debugger_stack", {})],
    # 这两个工具只在 Debugger.paused 时有效; 同样先自动暂停。
    "browser_reverse_return_value":  [("browser_debugger_stack", {})],
    "browser_reverse_set_variable":  [("browser_debugger_stack", {})],
    # 前进历史: 连续两次导航后再后退, 从而产生 forward 栈。
    "browser_forward": [
        ("browser_navigate", {"url": "https://example.com", "wait_for_load": False}),
        ("browser_navigate", {"url": "https://example.com/?mcpForwardProbe=1", "wait_for_load": False}),
        ("browser_back", {}),
    ],
})
```
理由：
- `browser_cdp_event`：实现先查 `查询异步结果("cdp_event:"+event_name)`（`MCP_Server_Core.wsv:4561-4577`），而回调 `MCP_Callbacks.wsv:543` → `存储CDPDevTools事件`（`MCP_Server.wsv:2217-2232`）把**每个收到的 CDP 事件**都按该键写入。`Debugger.paused` 会被写入这一点已有强证据：
  `browser_debugger_wait_paused` 用 `[前置] browser_debugger_stack -> OK` 后一次就拿到暂停摘要（台账 round 51，**已通过**），它读的正是同一个 `取CDP事件数据JSON("Debugger.paused")` → `查询任务结果("cdp_event:Debugger.paused")`（`MCP_Server.wsv:2431-2447`）。
- `browser_reverse_return_value` / `set_variable`：判据就是"`取CDP事件数据JSON("Debugger.paused")` 是否为空"（`MCP_Server_Reverse.wsv:1210-1213`、`:1238-1244`）。项目**已实现**零前置自动暂停（`MCP_Server.wsv:1658` `确保调试器已暂停`），且 `TOOL_PRE_CALLS` 已有先用 `browser_debugger_stack` 造暂停态的先例。
- `browser_forward`：`可否前进()` 需要有 forward 栈。用"导航 A → 导航 B → 后退"构造。
  注意 `wait_for_load: False` 是为了避免同步等待（这两次导航只是造历史，不需要等载入）。

---

## 3. (c) C 类真实缺陷（按严重度/修复价值排序）

### 3-1. `browser_find_by_tag` —— 本机上**永远不可能成功**的工具（最严重）
- 失败原文：`未找到标识为: mcp_probe 的浏览器 | 可能原因: 该标识未被 browser_user_tags 设置过, 或浏览器已关闭 | 建议: 先用 browser_list 查看现有浏览器及其 id`
- 位置：`src/MCP_Server_Core.wsv:5577`（分派）/ `:5585-5589`（查表）/ `:5605`（消息）。
- 为什么是缺陷（三条静态证据）：
  1. 全项目**没有任何工具能设置"用户标识"**：grep 全 src，`取用户标识` 只出现在 `MCP_Server_Core.wsv:3669`（读取上报）、`:5411`（窗口信息里的 `user_tag`）、`:5586`（查找）、`:5950`（列清单）；`browser_create` 的 schema 只有 `url`/`background`（`_audit/_tools_list.json`），没有 tag 参数。
  2. `browser_user_tags` 是只读的"列出用户标识"（`MCP_Server_Core.wsv:5947-5965`），**消息却说"该标识未被 browser_user_tags 设置过"** —— 把读取工具当成写入工具，误导调用方去找一个不存在的功能。
  3. 台账里 `browser_user_tags` 的实返是 `{"tags":[""]}`（round 11）→ 本机**只有空标识**，而空标识会被 `:5581-5584` 的"tag 缺少参数"守卫挡掉 → 没有任何可查的 tag。
- 结论：这不是"这个 tag 不存在"，而是"这个工具在本 MCP 内不可达"。调用方无论怎么重试、怎么按消息建议做（`browser_list` 只给 id，不给 tag）都只会一直拿到同一条失败。
- 建议修复（任选）：
  (a) 增加设置入口（如 `browser_create` 加 `tag` 参数，或加 `browser_set_tag {browser_id, tag}`），并在消息里写"标识需在创建浏览器时指定"；
  (b) 若产品上不打算开放，则把消息改成如实、可行动的版本，例如
  `未找到标识为 X 的浏览器 | 本机当前可用标识: (browser_user_tags 结果) | 本 MCP 未提供设置标识的接口, 该工具需要由宿主在创建浏览器时指定用户标识`。

### 3-2. `browser_find_by_hwnd` —— 不可行动，且无静态替代值
- 失败原文：`未找到窗口句柄为 1 的浏览器`
- 位置：`src/MCP_Server_Core.wsv:5918`（分派）/ `:5945`（消息）。
- 为什么是缺陷：消息只有一句，**没有**给出任何取得有效句柄/可替代工具的提示；对照同族的 `browser_find_by_tag`（`:5605`）就带了 `建议: 先用 browser_list …`。而本项目**确实有** `browser_get_window_handle`（台账 round 3 实返 `{"success":true,"hwnd":"2952610"}`，**已通过**）。
- 为什么不能按 A 处理：句柄是**每次运行都不同**的运行时值（`2952610`），无法写进 `TOOL_ARG_OVERRIDES` 常量；`TOOL_PRE_CALLS` 目前只执行前置调用，**没有"把前置输出塞进被测工具入参"的机制**（`tool_ledger.py:91-99`）。`hwnd=0` 会被 `:5922-5924` 判为缺参。
- 建议修复（任一即可让它变成"合法可行动"）：
  1. 消息补上取得方式与替代：`… | 如何取得有效句柄: 调 browser_get_window_handle (返回当前浏览器窗口句柄) 或 browser_list + browser_window_info; 也可用 browser_find_by_tag/browser_list 按 id 定位`；
  2. 或者在台账侧支持"动态入参"（例如 `TOOL_ARG_OVERRIDES` 允许 `{"hwnd": "$call:browser_get_window_handle.hwnd"}` 这类占位），那它就能归入 A。

### 3-3. `browser_reverse_precise_coverage` —— 默认动作落在未开启的前置上，错误原文未加工
- 失败原文：`Profiler.takePreciseCoverage 失败: Precise coverage has not been started.`
- 位置：`src/MCP_Server_Reverse.wsv:1129`（分派）；默认动作 `take` 于 `:1136-1139`；CDP 调用 `:1153-1156`；错误透传点 `MCP_Server_Reverse.wsv:2241-2249`（`执行V8CDP命令`）。
- 为什么是缺陷：
  1. `take` 是**默认动作**（空参即落到它），而 `take` 的前置（`action=start`）只有调用方自己知道 —— 典型的"默认动作在空参下永不可用"，与 `browser_reverse_runtime` 已被记录的问题同类（见 `mass_probe.py:198-200` 的注释）。
  2. 消息是**英文原文透传**：`执行V8CDP命令` 里有专门的"域未启用"改写分支（`MCP_Server_Reverse.wsv:2245-2248`，匹配 `not enabled` / `Agent is not` / `Debugger is not`），但 `Precise coverage has not been started.` **不匹配**任何一条 → 落到 `:2249` 的裸 `CDP方法名 + " 失败: " + v8Err`。调用方得到的是一句英文内核错误，**没有任何"先 action=start"的指引**，而且按 `mass_probe.py:294` 的"可行动"正则（`不能为空|必填|需|请|范围|无效|支持|例:|默认|\d`）它被判成 `ERR_WEAK`，这正是"消息不告诉调用方怎么继续"的判定。
- 建议修复（任一）：
  (a) 把 `has not been started` 也纳入 `:2245` 的改写分支，回 `精确覆盖率尚未开启: 请先调 browser_reverse_precise_coverage action=start (可再调 action=take)`；
  (b) 或让 `take` 在未开启时**自动 start 并在 auto_prepared 里如实上报**（与项目"零前置"一致），然后 take 一次即可。
- 备注：即使只做 (a)，台账里这一条也只是从"不可行动"变成"合法可行动"；要转 pass 需要 `action=start` 再 `take`，那属于 `TOOL_PRE_CALLS`（`[("browser_reverse_precise_coverage", {"action":"start"})]` + 保持默认 take）——但那等于把"默认动作不可用"这个缺陷遮掉，**建议先修 (a)/(b) 再考虑覆盖**。

### 3.3 附：不算 C、但建议顺手改的消息（A 类工具自带的次级问题）
- `browser_intercept`：`参数 url 不能为空`（`MCP_Server_Core.wsv:2504`）。同文件 `:2428` 的注释已经承认"省略 action 会落到规则分支并报出与真实原因无关的『参数 url 不能为空』"，但**同一个坑在 action 合法、url 缺失时依旧存在**。建议把 `:2504` 改成点名动作的版本：`action=modify/block/replace_data/... 需要 url(目标URL子串, 例: example.com)`。我仍把该工具归为 A（探针只给了 `action=modify`、没给 `url`，且存在 `clear` 这一无害覆盖）。
- `browser_set_window_style`：schema 里 `type`/`style` 都是自由整数（`_tools_list.json`），工具只认 `-16/-20/-12`。建议给 `type` 加 `enum: [-16,-20,-12]`，让 AI 调用方在 schema 层就看不到非法值（消息本身已经可行动，故仍归 B）。

---

## 4. (d) 未知项 / 需要实测才能定案的点

1. **`browser_forward` 到底是 A 还是 C（第一优先）**
   台账 round 1 的时序很反常：`browser_navigate`(→ example.com) → `browser_back` **成功**（`{"success":true,"message":"已后退"}`）→ 紧接着 `browser_forward` 报"无导航历史"；而 round 3 的 `browser_can_navigate` 给出 `{"can_go_back":true,"can_go_forward":false}` —— 刚后退过却仍有 back、没有 forward。
   两种可能：(i) 一次**新导航清空了 forward 栈**（round 3 的 `browser_get_focused_frame` 显示主框架 URL 是 `https://example.com/?cm=1789234782`，即某处自动做了带 cache-buster 的**重新导航**，而任何新导航都会清空 forward）；(ii) `browser_back` 的"已后退"是**假成功**（`可否后退()` 为真但 `后退()` 未生效，见 `MCP_Server_Core.wsv:197-201`，它只信 `可否后退()`，不校验实际地址变化）。
   会定案的测量：`navigate(A) → navigate(B) → browser_back → 立刻 browser_can_navigate`。若此时 `can_go_forward` 仍为 false → (ii)，应判 C（`browser_back` 假成功 / 前进栈不可用）；若为 true 则 A 的 PRE_CALL 方案成立。建议同时检查是否真有 `?cm=` 自动重导航插手。
2. **`browser_reverse_return_value` / `browser_reverse_set_variable` 前置补齐后是否真能通过**
   自动暂停点（`Debugger.pause` 制造）能否承载 `Debugger.setReturnValue`/`setVariableValue` 我不敢静态断言：`setReturnValue` 要求当前帧处于"即将返回"的语义位置，合成的 pause 可能返回 `Can only perform operation while paused` 之外的错误；`setVariableValue` 会拿 `variable_name="mcp_probe"` 去找变量，合成帧里几乎不可能存在该名字。
   会定案的测量：加 `TOOL_PRE_CALLS=[("browser_debugger_stack", {})]` 后看返回。若仍失败，则这些**次级**错误文本（`执行V8CDP命令` 的裸透传分支 `MCP_Server_Reverse.wsv:2249`）需要单独按 C 处理（消息应说明"合成暂停帧没有局部变量 X"）。另建议：给这两个工具补上 `确保调试器已暂停` 的自动暂停（`MCP_Server.wsv:1658`），与已经这么做的 `browser_debugger_script_source`（`MCP_Server_Core.wsv:5026-5031`）保持一致 —— 现在是同族工具零前置行为不一致。
3. **`browser_cdp_call` 的 CDP 方法选择**：`Runtime.evaluate`（+ params）是本机已证可用的路径；`Browser.getVersion` 更轻但我没有证据表明该 CEF 构建把 `Browser` 域绑定全了。二者都未验证。
4. **`browser_debugger_flow` / `browser_debugger_auto` 是否可能转成 pass**：本机测试页 example.com 现行版本**不含任何 `<script>`**（`browser_reverse_search_script` 台账 `count:0`、`scripts_json:"[]"`；`browser_debugger_set_breakpoint` 台账回 `"locations":[]`）。因此只要 `urlRegex` 指向当前页，就必然 0 命中。要让它通过必须导航到一个带外部脚本的页面（依赖外网，且会给后续工具带来不可控页面），故我判 B 而不提议覆盖。若主 agent 愿意接受"导航到某固定带脚本页面"，这两条可以按 A 处理（`{"breakpoint": "<该页脚本URL正则>", "url": "<该页>"}`）——这是**取舍问题不是能力问题**，请显式决定。
5. **异步型工具的 pass 证据偏弱**：`browser_wait`（守卫过后即回 `task_id`）、`browser_dom_select`、`browser_fill_exists`、`browser_vip_execute_js_context`、`browser_vip_dom_search` 等只回"已提交"，`classify()`（`mass_probe.py:283-317`）看到 `success:true` 即判 OK。也就是说这些工具"转通过"只证明**守卫之后没有立刻报错**，不证明结果正确。若台账要作为"每个功能都验证过"的证据，需要额外脚本去 `mcp_result` 取回结果做二次判定 —— 这超出本次只读分析的范围。
6. **并发写入风险**：`_tool_ledger.json` / `mass_probe.py` 在我阅读期间被改了三次（44 → 41 条失败、`mass_probe.py` 389 → 406 行）。本文件里的行号对应 `src/*.wsv` **当前**内容（`MCP_Server_Core.wsv` mtime 04:41:59、`MCP_Server_Reverse.wsv` 04:49:23、`MCP_Server.wsv` 04:48:24）；若源文件随后被改动，行号需重核。
7. **`browser_dom_checked`/`dom_selected` 即便注入元素也可能有别的坑**：`browser_dom_checked` 的 CDP 路径在取不到结果时会**回退原生** `填表框架.取元素选择框` 而该原生 API 在本内核下已知"恒返回空/null"（同族问题的注释见 `MCP_Server_Form.wsv:220-224`），因此注入后仍有可能拿到 `null` 形式的"成功"或误判。若出现这种情况，说明是 CDP 路径回退问题（C 级），而不是选择器问题。
