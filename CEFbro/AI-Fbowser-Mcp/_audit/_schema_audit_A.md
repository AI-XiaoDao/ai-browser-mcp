# Core 工具 schema↔实现 一致性审计 (A)

对象: `src/MCP_Server_Core.wsv` 的分派分支 vs `src/MCP_Server.wsv` 的 `添加工具JSON` 注册声明。**纯静态分析**（grep/正则+逐行阅读），未编译、未启动服务、未调用任何 MCP 接口。

## 0. 快照与口径

| 文件 | 行数 | 字节 | SHA256(前16) | mtime |
|---|---|---|---|---|
| `src/MCP_Server_Core.wsv` | 8866 | 581655 | `dc8166630a6c77d8` | 2026-09-13 12:19:55 |
| `src/MCP_Server.wsv` | 12610 | 769498 | `5ab0d73d254ec242` | 2026-09-13 12:24:56 |

- 行号口径: DSH `read`/`grep` 的 **LF 口径**；`MCP_Server_Core.wsv` 是纯 LF（无 CR CR LF 膨胀问题），`MCP_Server.wsv` 同为 LF 口径。
- ⚠ **分析期间源码被并发修改**：`MCP_Server_Core.wsv` 由会话初 578629 字节/8825 行变为 581655 字节/8866 行（快照 `dc816663…` 之后未再变，表中 Core 行号对其成立）；`MCP_Server.wsv` 在报告生成后又改动了一次（`21dd872e…` → `5ab0d73d…`，行数仍 12610），**上表已更新为新快照，且报告引用的每个 `MCP_Server.wsv` 行号都已对该新版本逐条复核通过**（16 个锚点全部命中：`:1874 params_text`、`:4131 url_regex`、`:4179/:4186 line_number/column_number`、`:4483/:4487/:4497/:4501`、`:4463 scriptId`、`:4470 url`、`:12131 browser_id`、`:1193 browser_debugger_pause 注册表`、`:5960/:5964/:5986`、`:6144`、`:7017`、`:6833/:6847/:6909`）。每处证据同时给出可自证的代码锚点（如 `yyjson取逻辑(参数JSON,"kernel")`），即使后续再改动也可按锚点复核。
- 扫描方法: ①grep `方法名 == "browser_xxx"` 得分派分支清单 ②对每个分支抽取参数读取调用（`yyjson取文本/取整数/取长整数/取小数/取逻辑/取逻辑_默认/参数键存在/yyjson取对象成员/yyjson取JSON文本` 且首参为 `参数JSON`）③对 `MCP命令服务器.X (..., 参数JSON)` 形式的**委托调用做传递闭包**（深度4，排除所在方法自身，避免递归进分派器）④在 `MCP_Server.wsv`（屏蔽掉注册行后）与其余 `.wsv` 中检索同名参数，判定是否由公共层/共享助手读取。

## 1. 扫描结果

| 项 | 数量 |
|---|---|
| Core 分派分支行（`否则/如果 (方法名 == "...")`） | 165 |
| 其中 `browser_*` 工具（含 `browser_aliases`/`browser_batch` 两个仅别名分支） | 162 |
| `MCP_Server.wsv` 中 `添加工具JSON` 注册总数 | 322 |
| Core 工具中在 tools/list **无注册** | 3（见 §4） |
| 差异条数（按类型） | MISSING_IN_SCHEMA 29, DECLARED_UNUSED 3, ACTION_MISMATCH 3, ENUM_MISMATCH 0, REQUIRED_MISMATCH 8, DESC_PROMISE 2 |
| 差异条数合计 | **45** |

## 2. 差异表

| 工具名 | 差异类型 | 实现读的参数(附 file:line) | schema 声明的属性 | 影响(一句话) | 建议修法(一句话) |
|---|---|---|---|---|---|
| `browser_back` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:254 `yyjson取逻辑_默认(参数JSON,"wait_for_load")` | (无属性) | 经共享助手 注册加载等待任务 读 wait_for_load(默认真), schema 无属性 → 代理无法让 back 不等待载入 | schema 增补 wait_for_load(与 navigate/reload 一致) |
| `browser_cdp_event` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:5117 `yyjson取文本(参数JSON,"event")` | event_name:text | 实现接受 event 作为 event_name 的别名, 描述与 schema 只说 event_name → 用 event 的调用方在 schema 上看不到 | schema 增补 event(别名) 或描述里说明 |
| `browser_collect` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:3955 `yyjson取文本(参数JSON,"keyword")`; MCP_Server_Core.wsv:3958 `yyjson取整数(参数JSON,"limit")` | action:text | 描述明写 `console_get 支持 keyword 参数按日志内容搜索, limit 限制条数`, schema 只声明 action → 代理看不到这两个参数(与题目中 browser_network 的 limit 同类缺陷) | schema 增加 keyword/limit 两个属性 |
| `browser_collect` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:3870 `yyjson取逻辑(参数JSON,"clear")` | action:text | action=reverse_prepare 会读 clear(默认非假=清空), schema 未声明 → 代理无法在不清理的情况下做场景预备 | schema 增加 clear:boolean 属性并说明默认行为 |
| `browser_console_eval` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2341 `yyjson取文本(参数JSON,"file")` | expression:text | 实现支持用 file 传JS文件路径(并做安全路径校验), schema 只声明 expression → file 用法不可发现 | schema 增加 file:text 属性 |
| `browser_debugger_enable / browser_debugger_resume / browser_debugger_step_over / browser_debugger_step_into / browser_debugger_step_out / browser_debugger_stack` | `MISSING_IN_SCHEMA` | MCP_Server.wsv:1874 `params_text = yyjson取JSON文本 (参数JSON, "params")`(共享助手 `执行CDP命令`; 这 6 个工具经委托进入该助手, 故 params 确被读取) | (无属性; 仅 `browser_debugger_stack` 声明 stack_trace_id:text) | 这些工具经共享助手 执行CDP命令 调用, 该助手会读 params 作为 CDP 参数; 六个工具的 schema 都是空属性(或只声明自身参数) → params 属于'可用但不可见'。注: 该助手同时服务 browser_cdp / browser_cdp_call, 后者已声明 params, 故本条为低优先级 | 若确属有意能力则在描述中说明可传 params; 否则在助手层忽略这些工具传入的 params |
| `browser_debugger_flow` | `MISSING_IN_SCHEMA` | MCP_Server.wsv:4131 `yyjson取文本(参数JSON,"url_regex")` [经 执行Debugger断点流程JSON]; MCP_Server.wsv:4179 `yyjson取整数(参数JSON,"line_number")` [经 执行Debugger断点流程JSON]; MCP_Server.wsv:4186 `yyjson取整数(参数JSON,"column_number")` [经 执行Debugger断点流程JSON]; MCP_Server.wsv:3159 `yyjson取文本(参数JSON,"expression")` [经 执行Debugger断点流程JSON>取Debugger表达式Raw文本] | url:text, breakpoint:text, line:integer, column:integer, expressions:text, expand:boolean, return_by_value:boolean, max_ms:integer, resume:boolean | 委托 执行Debugger断点流程JSON 读 url_regex(与 url 等价) / line_number / column_number(与 line/column 等价) 以及 expression(expressions 的单数形式), schema 只声明 url/line/column/expressions → 4 个别名不可发现 | schema 增补别名或统一为一种写法 |
| `browser_debugger_script_source` | `MISSING_IN_SCHEMA` | MCP_Server.wsv:4483 `yyjson取整数(参数JSON,"line_number")` [经 执行Debugger脚本源JSON]; MCP_Server.wsv:4497 `yyjson取整数(参数JSON,"column_number")` [经 执行Debugger脚本源JSON]; MCP_Server.wsv:4487 `yyjson取整数(参数JSON,"lineNumber")` [经 执行Debugger脚本源JSON]; MCP_Server.wsv:4501 `yyjson取整数(参数JSON,"columnNumber")` [经 执行Debugger脚本源JSON]; MCP_Server.wsv:4463 `yyjson取文本(参数JSON,"scriptId")` [经 执行Debugger脚本源JSON]; MCP_Server.wsv:4470 `yyjson取文本(参数JSON,"url")` [经 执行Debugger脚本源JSON] | call_frame_id:text, script_id:text, line:integer, column:integer, context_lines:integer, include_source:boolean | 委托 执行Debugger脚本源JSON 读 CDP 驼峰名(lineNumber/columnNumber/scriptId)与下划线别名, schema 只声明 line/column/script_id → CDP 原生字段名不可发现 | schema 增补别名, 或描述里明确支持 CDP 原生字段名 |
| `browser_debugger_set_breakpoint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:5388 `yyjson取整数(参数JSON,"line_number")`; MCP_Server_Core.wsv:5395 `yyjson取整数(参数JSON,"column_number")` | url:text, line:integer, column:integer | 实现同时接受 line/line_number 与 column/column_number 两组别名, schema 只声明 line/column → 别名不可发现 | schema 增补别名或说明二者等价 |
| `browser_dom_set_value` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:1998 `yyjson取整数(参数JSON,"allow_empty")` | selector:text, value:text, frame_id:text | 实现用 allow_empty:1 才能传空 value 清空元素; 失败消息自己就提示 `如需清空请设置 allow_empty:1`, 但 schema 未声明 → 代理收到提示却无法发现该参数 | schema 增加 allow_empty:integer 属性 |
| `browser_evaluate` | `MISSING_IN_SCHEMA` | MCP_Server.wsv:8269 `yyjson取文本(参数JSON,"code_base64")` [经 解码JS代码] | code:text, file:text, max_ms:integer | 同上: 实现支持 code_base64, schema 未声明 | schema 增加 code_base64:text 属性 |
| `browser_execute_js` | `MISSING_IN_SCHEMA` | MCP_Server.wsv:8269 `yyjson取文本(参数JSON,"code_base64")` [经 解码JS代码] | code:text, file:text, frame_id:text, world:text | 解码JS代码 支持 code_base64(base64 内联JS, 免转义), 描述与 schema 均未提 → 代理不知道可用 | schema 增加 code_base64:text 属性 |
| `browser_file_dialog` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:7139 `yyjson取文本(参数JSON,"path")`; MCP_Server_Core.wsv:7142 `yyjson取文本(参数JSON,"file_path")` | (无属性) | schema 无任何属性, 但实现必须先有 path(或别名 file_path) 否则直接失败; 代理看不到参数名只能靠报错文本试错 | schema 增加 path(text,必填) 与 file_path(别名) |
| `browser_fingerprint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2411 `yyjson取整数(参数JSON,"min")`; MCP_Server_Core.wsv:2413 `yyjson取整数(参数JSON,"max")`; MCP_Server_Core.wsv:2422 `yyjson取整数(参数JSON,"seed")` | action:text, config:text | action=audio_random 读 min/max/seed, schema 只声明 action/config → 随机噪点区间不可发现 | schema 增补 min/max/seed(或写进 config 说明) |
| `browser_fingerprint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2462 `yyjson取整数(参数JSON,"sample_rate")`; MCP_Server_Core.wsv:2464 `yyjson取整数(参数JSON,"channels")`; MCP_Server_Core.wsv:2466 `yyjson取整数(参数JSON,"frames_per_buffer")` | action:text, config:text | action=audio_param 读 sample_rate/channels/frames_per_buffer, schema 未声明 | schema 增补这三个 audio 参数 |
| `browser_fingerprint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2503 `yyjson取文本(参数JSON,"public_ip")`; MCP_Server_Core.wsv:2503 `yyjson取文本(参数JSON,"local_ip")`; MCP_Server_Core.wsv:2503 `yyjson取文本(参数JSON,"host")`; MCP_Server_Core.wsv:2503 `yyjson取逻辑(参数JSON,"disable")` | action:text, config:text | action=webrtc 读 public_ip/local_ip/host/disable, schema 未声明 | schema 增补 webrtc 四参数 |
| `browser_fingerprint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2509 `yyjson取小数(参数JSON,"latitude")`; MCP_Server_Core.wsv:2511 `yyjson取小数(参数JSON,"longitude")` | action:text, config:text | action=geolocation 读 latitude/longitude, schema 未声明 | schema 增补 latitude/longitude |
| `browser_fingerprint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2517 `yyjson取整数(参数JSON,"offset_h")`; MCP_Server_Core.wsv:2517 `yyjson取整数(参数JSON,"offset_m")`; MCP_Server_Core.wsv:2517 `yyjson取文本(参数JSON,"name")`; MCP_Server_Core.wsv:2517 `yyjson取文本(参数JSON,"iana")` | action:text, config:text | action=timezone 读 offset_h/offset_m/name/iana, schema 未声明(注: 此处的 name 与 工具名 无关) | schema 增补时区四参数 |
| `browser_fingerprint` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2526 `yyjson取整数(参数JSON,"tls_min")`; MCP_Server_Core.wsv:2527 `yyjson取整数(参数JSON,"tls_max")`; MCP_Server_Core.wsv:2531 `yyjson取文本(参数JSON,"ciphers")` | action:text, config:text | action=ssl 读 tls_min/tls_max/ciphers, schema 未声明 | schema 增补 SSL 三参数 |
| `browser_forward` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:278 `yyjson取逻辑_默认(参数JSON,"wait_for_load")` | (无属性) | 同上: forward 也经 注册加载等待任务 读 wait_for_load, schema 无属性 | schema 增补 wait_for_load |
| `browser_inject` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:3382 `yyjson取文本(参数JSON,"inject_id")` | type:text, code:text, persist:boolean | persist+type=js 时用 inject_id 作持久V8扩展标识(缺省自动生成), schema 只声明 type/code/persist → 代理无法指定/覆盖标识 | schema 增加 inject_id:text 属性 |
| `browser_intercept` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:2690 `yyjson取整数(参数JSON,"width")`; MCP_Server_Core.wsv:2692 `yyjson取整数(参数JSON,"height")`; MCP_Server_Core.wsv:2694 `yyjson取整数(参数JSON,"x")`; MCP_Server_Core.wsv:2696 `yyjson取整数(参数JSON,"y")` | action:text, url:text, search_text:text, replace_text:text, file_path:text, line_start:integer, line_end:integer, target:text | action=popup_config 读 width/height(必填>0) 与 x/y, schema 未声明 → 弹窗配置动作按 schema 无法调用 | schema 增加 width/height/x/y 四个 integer 属性 |
| `browser_network` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:3498 `yyjson取逻辑(参数JSON,"auto_enable")` | action:text, request_id:text, url:text, wait_ms:integer, limit:integer | 描述明写 `list 默认 auto_enable`, 实现读 auto_enable:false 跳过自动开启, schema 未声明 → 该开关不可发现 | schema 增加 auto_enable:boolean 属性 |
| `browser_reverse_extract` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:7960 `yyjson取文本(参数JSON,"script_id")` | mode:text, url_pattern:text, script_index:text, keyword:text | 实现读 script_id(按脚本ID取源码), schema 只声明 mode/url_pattern/script_index/keyword → 该取源方式不可发现 | schema 增加 script_id:text 属性 |
| `browser_reverse_hook` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:7555 `yyjson取文本(参数JSON,"url_pattern")` | target:text, type:text, capture_args:boolean, capture_return:boolean, capture_stack:boolean | type=xhr_fetch 时实现要求 target 或 url_pattern, schema 只声明 target/type/capture_* → 只给 url_pattern 的用法不可发现 | schema 增加 url_pattern:text 属性 |
| `browser_touch_move` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:6613 `yyjson取逻辑(参数JSON,"kernel")` | x:integer, y:integer | 同上: 描述承诺 kernel:true, schema 无该属性 | 补 kernel 属性声明 |
| `browser_touch_press` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:6547 `yyjson取逻辑(参数JSON,"kernel")` | x:integer, y:integer | 描述明写 `仅当传 kernel:true 才走内核级注入`, 但 schema 只声明 x/y → 代理看不到 kernel, 永远用不上内核路径(同族 mouse_click/move/wheel 都声明了 kernel) | 在 schema 增加 属性项JSON("kernel","boolean","true=内核级注入(会使CDP通道失效)") |
| `browser_touch_release` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:6580 `yyjson取逻辑(参数JSON,"kernel")` | x:integer, y:integer | 同上: 描述承诺 kernel:true, schema 无该属性 | 补 kernel 属性声明 |
| `browser_view_source` | `MISSING_IN_SCHEMA` | MCP_Server_Core.wsv:4211 `yyjson取整数(参数JSON,"max_chars")` | (无属性) | 实现读 max_chars 控制返回源码截断上限, schema 无属性 → 代理无法控制返回体积 | schema 增加 max_chars:integer 属性 |
| `browser_debugger_last_paused` | `DECLARED_UNUSED` | 分支(MCP_Server_Core.wsv:5631-5647)内 0 处 `parse` 读取; `parse` 的实际读取点在 browser_debugger_evaluate → MCP_Server_Core.wsv:5582 `yyjson取逻辑_默认 (参数JSON, "parse", 假)` | parse:boolean | schema 声明 parse, 但该分支只读 CDP 事件并调 解析Debugger暂停摘要, 从不读 parse(读 parse 的是 browser_debugger_evaluate) → 参数完全无效 | 删掉 parse 属性 |
| `browser_dom_query` | `DECLARED_UNUSED` | 分支(MCP_Server_Core.wsv:1890-1956)内 0 处 `index` 读取(实现用 document.querySelector 取单元素); 全仓该参数读取点仅 MCP_Kernel.wsv:1649 `索引 = MCP命令服务器.yyjson取整数 (参数JSON, "index")`(方法 分派_源码提取, 属另一工具) | selector:text, attribute:text, index:integer, frame_id:text | schema 声明 index, 实现用 document.querySelector 取单个元素, 从不读 index → 传 index=2 会静默忽略并返回第 1 个匹配(同名 index 只被其它工具的 分派_源码提取 使用) | 删掉 index, 或实现 querySelectorAll + index 取第 N 个(推荐后者并在描述写明 1 基/0 基) |
| `browser_get_text` | `DECLARED_UNUSED` | 分支(MCP_Server_Core.wsv:513-656)内 0 处 `max_chars` 读取; 全仓 max_chars 读取点仅 MCP_Server_Core.wsv:502(browser_get_source) / :2059(browser_dom_get_html) / :4211(browser_view_source), 全文截断用常量(MCP_Server_Core.wsv:629 `全文上限 = MCP_常量.截断_源码默认字节`) | selector:text, max_chars:integer, frame_id:text | schema 声明 max_chars, 但实现全文/选择器两条路径都不读它(全文截断用常量 MCP_常量.截断_源码默认字节) → 代理设了 max_chars 却完全无效, 且会误以为已限流 | 删掉该属性, 或让实现真正按 max_chars 截断(推荐后者: 与 browser_get_source/dom_get_html 行为对齐) |
| `browser_collect` | `ACTION_MISMATCH` | MCP_Server_Core.wsv:3848 `如果 (action == "network_enable" \|\| ... \|\| action == "enable" \|\| action == "disable" ...)`; 另 MCP_Server_Core.wsv:3947 `否则 (action == "console_get")` | action:text | action 描述枚举里没有裸 enable/disable/get, 但实现第 3848 行接受 action=="enable"/"disable"/"get"(以及 console_* 通配下未单列的 console_get) → 实现的取值集合大于描述 | 把裸 enable/disable/get/console_get 写进 action 描述, 或去掉这三个别名 |
| `browser_fingerprint` | `ACTION_MISMATCH` | MCP_Server_Core.wsv:2627 `未知action: ... \| 支持: clear/count/.../set_batch`(无 ua) | action:text, config:text | action 描述把 ua 列在枚举里(canvas_random/.../ssl/ua/set_batch/...), 但实现第 2627 行的未知 action 提示与 12 个分支都不含 ua → 按描述传 action=ua 必然落到 '未知action' 失败(描述后半句虽写 'ua 走 browser_fingerprint_ua', 但枚举混列仍会误导) | 从 action 描述中移除 ua, 只在说明里写 '设置 UA 请用 browser_fingerprint_ua' |
| `browser_network` | `ACTION_MISMATCH` | MCP_Server_Core.wsv:3464 `如果 (action == "body" \|\| action == "network_body")` | action:text, request_id:text, url:text, wait_ms:integer, limit:integer | 实现额外接受 action=="network_body"(与 body 等价), action 描述只列 body/network_* 系列 → 多出一个未列取值(反向: 实现 ⊃ 描述, 属低危) | 在 action 描述里补 network_body, 或在描述中说明 body 的别名 |
| `browser_console_eval` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:2341 `expression = ...yyjson取文本 (参数JSON, "file")`(file 作为 expression 的替代) + schema required=["expression"] | expression:text | schema required=["expression"], 但实现允许用 file 替代 expression → 只给 file 的合法调用会被严格客户端按 required 拒绝 | 描述与 schema 改为 'expression 或 file 二选一' |
| `browser_dom_set_value` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:1998 `如果 (value == "" && ...yyjson取整数 (参数JSON, "allow_empty") == 0)` 与 MCP_Server.wsv:11249 的 `多属性Schema文本(..., "\"selector\",\"value\"")` | selector:text, value:text, frame_id:text | schema required=["selector","value"], 但实现允许 value 为空(配合 allow_empty:1 清空元素) → 想走清空路径的调用会被 required 拦下, 而本来能解锁它的 allow_empty 又未声明, 形成死路 | 保留 required 但把 allow_empty 声明出来并在描述说明 '清空元素: 传 allow_empty:1'(或把 value 从 required 移除) |
| `browser_evaluate` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:340 `返回 (..."缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径)")` (第2处) | code:text, file:text, max_ms:integer | 同上: schema 无 required, 实现要求 code 或 file 之一 | 同上 |
| `browser_execute_js` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:340 `返回 (..."缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径)")` | code:text, file:text, frame_id:text, world:text | schema 的 required 为空(多属性Schema文本 第二参 = ""), 但实现 code/file 都为空时直接失败 → 违反 schema 的调用会运行期报错 | required 补 ["code"] 并在描述写明 code 与 file 二选一(或改用 oneOf) |
| `browser_hash` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:6482 `data 不能为空 \| 空串摘要无意义...` | action:text, data:text, path:text, uppercase:boolean | schema required=["action"], 但实现 md5/xxhash/crc32 三个 action 都要求 data(空则失败 'data 不能为空'), 仅 md5_file 不需要 → 条件必填未在 schema 体现 | 描述写明 'data: md5/xxhash/crc32 必填'; 或 schema 用 oneOf 表达 |
| `browser_highlight` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:8573 起 selector 读取 + `selector " + MCP_常量.错误_缺少参数` | selector:text, action:text, duration_ms:integer | schema required 为空, 但 action=show(默认) 时 selector 为空会失败 'selector 缺少参数' → 默认动作下的必填项未声明 | 描述写明 'action=show 时 selector 必填' |
| `browser_intercept` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:2713 `url = ...yyjson取文本 (参数JSON, "url")` + `参数 url 不能为空` | action:text, url:text, search_text:text, replace_text:text, file_path:text, line_start:integer, line_end:integer, target:text | schema required=["action"], 但多个动作(如 modify/replace_*/block/line_replace/popup_config)在缺少 url(或 width/height) 时直接失败 → 条件必填未在 schema/描述分动作说明 | 在 action 描述里逐动作标注所需参数 |
| `browser_reverse_hook` | `REQUIRED_MISMATCH` | MCP_Server_Core.wsv:7538-7541 `xhr_fetch 需要 target 或 url_pattern` | target:text, type:text, capture_args:boolean, capture_return:boolean, capture_stack:boolean | schema required 为空, 但 type=xhr_fetch 时实现要求 target 或 url_pattern 至少一个(否则失败), type=function_call 要求 target → 依赖 action/type 的条件必填未声明 | 在描述里写明各 type 的必填项 |
| `browser_file_dialog` | `DESC_PROMISE` | MCP_Server_Core.wsv:7137 `// 安全设计: 传 path 参数直接返回该路径(验证存在性), 不弹任何窗口`; 失败分支 `文件对话框已改为程序化选择(不弹窗口)` | (无属性) | 描述只有 '打开文件对话框', 但实现第 7137 行注释明确 '传 path 参数直接返回该路径(验证存在性), 不弹任何窗口', 且缺 path 时返回 '文件对话框已改为程序化选择(不弹窗口)' → 描述承诺了一个实现故意不做(且做不了)的行为; 同时 schema 无属性, 代理只会在失败后才知道要传 path | 描述改为 '校验并返回文件路径(不弹窗口); 必传 path' 并补 schema 属性 |
| `browser_view_source` | `DESC_PROMISE` | MCP_Server_Core.wsv:4205 `// 安全设计: 源码文本经MCP返回, 不弹任何窗口` | (无属性) | 描述 '在新标签打开当前页面源码视图(view-source:)', 但实现第 4205 行注释明确 '源码文本经MCP返回, 不弹任何窗口', 分支实际是取源码文本(受 max_chars 截断)并返回 → 描述承诺的行为不存在 | 描述改为 '返回当前页面源码文本(不新开标签)'; 需要真源码视图请另注册工具或说明不可用 |

## 3. 非差异（已核查，不报为缺口）

- **公共层参数**（在 `MCP_Server.wsv` 入口/共享助手里读，不属分支缺口）: `browser_id` → `MCP_Server.wsv:12131`(`执行浏览器命令`); `async_only`/`sync_wait` → `MCP_Server.wsv:5960/5964`(`应同步等待`); `max_ms` → `MCP_Server.wsv:6144`(`取同步等待毫秒`) 与 `:7017`(`注册加载等待任务`)，由 `MCP_Server.wsv:6833`(应同步等待 调用点) 与 `MCP_Server.wsv:6847`(取同步等待毫秒 调用点)、`MCP_Server.wsv:6909`(批量子命令同款调用) 在同步等待路径上统一调用。
  - 附带观察（非本表差异）: 这些公共层参数几乎未写进任何 schema —— `sync_wait` 在 322 个注册里声明 **0** 次，`async_only` 1 次(`browser_get_title`)，`browser_id` 1 次(`browser_close`)，`max_ms` 8 次。代理只能从个别工具的描述文本里偶然看到它们。
- `browser_network` 的 `request_id`/`url`/`wait_ms` **不是** DECLARED_UNUSED: `action=body` 时第 3467 行把同一个 `参数JSON` 转交 `browser_network_body`，后者确实读这三个参数（`MCP_Server_Core.wsv:5175` request_id / `:5186` url / `:5188` wait_ms）。
- `browser_dom_set_value` 之外的 `frame_id`、`max_chars`(get_source/dom_get_html)、`format` 等均为 schema 已声明且实现确读，一致。
- **`ENUM_MISMATCH` 本轮 0 条**（两项机械检查的结论）: ① 把 Core 每个工具的描述与 action 描述里的英文取值全部取出，在整个源码树中检索（屏蔽注册行与描述字符串本身，避免"描述自证"）—— 除 `cache_path`/`TryCloseBrowser`/`cpp`/`hpp`/`HMAC`/`HEX`/`wss` 这类非取值词外，没有任何"描述给了但代码里不存在"的取值；② 逐项核对描述中的取值示例与实现校验: `browser_screenshot` 描述 `format=png/jpeg/webp` 与实现 `MCP_Server_Core.wsv:2851 如果 (fmt != "png" && fmt != "jpeg" && fmt != "webp")` 一致；`browser_network_export` 的 `format=har` 与实现 `MCP_Server_Core.wsv:3731 如果 (neFormat == "har")` 一致。**特别说明**: 任务描述里举例的 `detail_enable` vs `detail` 不一致在当前快照中**已不存在** —— `browser_network` 同时接受 `detail_enable` 与 `network_detail_enable`(`MCP_Server_Core.wsv:3475`)，`browser_collect` 也在 `MCP_Server_Core.wsv:3848` 接受 `detail_enable`，两处描述与实现取值集合一致。
- `browser_evaluate` 的 `max_ms` 由上述公共层同步等待路径读取，故不计入 DECLARED_UNUSED。

## 4. 附加发现（无对应的差异类型，单列）

- **幽灵工具 `browser_debugger_pause`**: Core 有完整分派分支（`MCP_Server_Core.wsv:5329` 一带，含 `安全设计: 原始Debugger.pause在无JS执行点的页面上永不返回` 注释），命令行注册表也有条目（`MCP_Server.wsv:1193 命令注册表.置整数值 ("browser_debugger_pause", 832)`），但 **没有任何 `添加工具JSON ("browser_debugger_pause", ...)`** → 它不会出现在 tools/list 里，代理永远看不到也调不到。
- `browser_aliases` / `browser_batch` 同样没有同名注册，但它们是 `aliases` / `batch` 的**规范化别名**（`方法名 == "aliases" || 方法名 == "browser_aliases"`），属有意设计。

## 5. Top 15 待修清单（按影响排序）

1. **browser_touch_press/release/move** — `MISSING_IN_SCHEMA` | 参数: kernel → 描述承诺 kernel:true 内核注入路径, schema 只给 x/y → 该能力对代理完全不可达（同族 mouse_* 已声明 kernel，属明显不一致）
2. **browser_file_dialog** — `DESC_PROMISE + MISSING_IN_SCHEMA` | 参数: path/file_path → 描述说'打开文件对话框'但实现故意不弹窗；且 schema 零属性, 代理必须先失败一次才知道要传 path —— 一次调用成功率几乎为 0
3. **browser_view_source** — `DESC_PROMISE + MISSING_IN_SCHEMA` | 参数: max_chars → 描述说'在新标签打开源码视图'但实现只回文本；且能控制返回体积的 max_chars 未声明
4. **browser_dom_set_value** — `MISSING_IN_SCHEMA + REQUIRED_MISMATCH` | 参数: allow_empty → 报错文本让代理'设置 allow_empty:1', 但 schema 既未声明 allow_empty 又把 value 标为必填 → 提示给出的路走不通(死路)
5. **browser_collect** — `MISSING_IN_SCHEMA` | 参数: keyword/limit/clear → 描述明写 keyword/limit, schema 只声明 action → 代理看不到(与已知 browser_network limit 同类)
6. **browser_get_text** — `DECLARED_UNUSED` | 参数: max_chars → schema 承诺的限流参数实现从不读, 全文截断写死常量 → 代理以为已限流, 实际可能拿到 256KB 全文
7. **browser_fingerprint** — `MISSING_IN_SCHEMA` | 参数: 19 个维度参数 → 指纹是核心反检测能力, 但 6 组子参数全部未声明, 代理只能照描述猜键名(如 timezone 的 offset_h/offset_m/iana)
8. **browser_network** — `MISSING_IN_SCHEMA` | 参数: auto_enable → 描述提到 auto_enable 而 schema 未声明 → 无法阻止 list 隐式开启网络日志
9. **browser_debugger_script_source / _flow / _set_breakpoint** — `MISSING_IN_SCHEMA` | 参数: line_number/column_number/lineNumber/columnNumber/scriptId/url_regex/expression → 实现接受 CDP 原生驼峰名与下划线别名, schema 只声明一种写法 → 照 CDP 习惯传参的代理会以为不支持
10. **browser_inject** — `MISSING_IN_SCHEMA` | 参数: inject_id → 持久注入标识不可发现, 无法覆盖/复用已注入的扩展
11. **browser_intercept** — `MISSING_IN_SCHEMA` | 参数: width/height/x/y → popup_config 按 schema 无法调用(width/height 必填却不可见)
12. **browser_reverse_hook** — `MISSING_IN_SCHEMA` | 参数: url_pattern → xhr_fetch 要求 target 或 url_pattern, 后者不可见 → 只能照报错试错
13. **browser_execute_js / browser_evaluate** — `REQUIRED_MISMATCH + MISSING_IN_SCHEMA` | 参数: code|file, code_base64 → schema 无 required 但实现要求 code/file 之一; code_base64 免转义通道也不可见
14. **browser_dom_query** — `DECLARED_UNUSED` | 参数: index → 传 index 静默失效, 返回第 1 个匹配 → 代理会拿到错误元素且毫不知情(比报错更危险)
15. **browser_debugger_last_paused / browser_console_eval / browser_back / browser_forward** — `DECLARED_UNUSED` / `REQUIRED_MISMATCH` / `MISSING_IN_SCHEMA` | 参数: parse / file / wait_for_load → 低危清理项: parse 完全无效; console_eval 的 file 替代路径被 required=[expression] 挡住; back/forward 的 wait_for_load 未声明(navigate/reload 已声明, 属家族内不一致)

## 6. 复核指引

每条差异的复核方式（无需编译）: 在 `src/MCP_Server_Core.wsv` 按表中行号/锚点定位读取调用 → 在 `src/MCP_Server.wsv` 按 `添加工具JSON ("<工具名>"` 找到注册行，读其 schema 表达式的 `属性项JSON(...)` 列表，比对属性名集合；`多属性Schema文本` 的第二个参数为空字符串时表示 **不输出 required**。

## 7. 修复状态复核（针对最新 `5ab0d73d` 版本重新抽查）

写报告后又出现两次对 `MCP_Server.wsv` 的改动（`21dd872e…` → `5ab0d73d…`；`_audit/` 下同时出现了 `_apply_schema_audit_fixes*.py`、`verify_schema_audit_fixes.py`）。因此对表内最要紧的条目在新版本上**再抽查了一遍**，结论是**均尚未修复**，本报告仍然可执行：

| 抽查项 | 新版本实际 schema | 结论 |
|---|---|---|
| `browser_touch_press/_release/_move` | 仍是 `双/多属性` 只有 `x`/`y`（无 `kernel`） | 未修复 |
| `browser_file_dialog` | 描述仍是 `打开文件对话框`，schema 仍**零属性** | 未修复 |
| `browser_view_source` | 描述仍是 `在新标签打开当前页面源码视图(view-source:)`，schema 仍零属性 | 未修复 |
| `browser_collect` | action 描述里仍写着 `keyword`（正文也写 `keyword`/`limit`），schema 仍只声明 `action` | 未修复 |
| `browser_dom_set_value` | 仍是 `selector/value/frame_id`（无 `allow_empty`） | 未修复 |
| `browser_inject` | 仍是 `type/code/persist`（无 `inject_id`） | 未修复 |
| `browser_intercept` | 仍是 8 个属性（无 `width/height/x/y`） | 未修复 |
| `browser_network` | 仍是 `action/request_id/url/wait_ms/limit`（无 `auto_enable`） | 未修复 |
| `browser_cdp_event` | 仍是 `单参数Schema文本("event_name",...)`，别名 `event` 未声明 | 未修复 |
| `browser_fingerprint` | 仍是 `action/config`（19 个维度参数未声明） | 未修复 |
| `browser_back` / `browser_forward` | 仍零属性（无 `wait_for_load`） | 未修复 |
| `browser_get_text.max_chars` / `browser_dom_query.index` / `browser_debugger_last_paused.parse` | 三个属性仍**在 schema 里**（即"声明了但实现不读"依旧成立） | 未修复 |
