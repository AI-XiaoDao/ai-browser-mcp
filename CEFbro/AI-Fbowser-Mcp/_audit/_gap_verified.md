# 已核对的类库缺口汇总（真缺口 + 状态 + 证据）

> 由主代理维护。**实施任何"类库缺口"之前先看这一份** —— 它是三份逐条核对报告的结论汇总，
> 而 `_audit/_classlib_gap.md`（由 `classlib_gap.py` 生成）只是**待核对索引**：它的匹配口径
> 是"方法名是否出现在任一工具描述里"，**误报与漏报同时存在**（见文末"方法论警告"）。

## 一、真缺口与状态

| # | 类库方法 | 出处（核对报告） | 状态 | 证据 / 说明 |
|---|----------|------------------|------|-------------|
| 1 | `类_FBrowser_框架.载入请求 (请求)`（FBroLib.wsv:1669） | `_gap_recheck_1.md` 真缺口#1 | ✅ **已实现** | `browser_navigate` 新增 `method`/`headers`/`body`（提交式跳转）；请求头/体解析抽成 `应用请求头文本`/`应用请求体文本` 供"载入请求"与 `browser_create_url_request` **共用**；验收 `_audit/verify_navigate_request.py` **12/12**（本机 HTTP 服务当预言机：POST/自定义头/请求体逐字一致、body-only 自动 POST、**同址连续两次都真发**、GET 回归） |
| 2 | 菜单命令ID ⇄ 别名（项目只有正向链，事件 `context_menu_command` 只回数字） | `_gap_menu.md` §A2 | ✅ **已实现** | 新工具 `browser_menu_alias`（`action` 可省略；纯计算；反向查表**由既有正向链求值**、不建第二份表）；验收 `_audit/verify_menu_alias.py` **12/12**（17 项往返一致 + 清单与源码逐项一致 + 未知 ID 如实报 unrecognized + 失败可行动） |
| 3 | `类_FBrowser_URL请求事件.上传进度`（FBroEventControl.wsv:2314） | `_gap_vip_events.md` 真缺口#2 | ✅ **已实现并运行期验收** | 新增 `上传进度` 覆盖 → 事件 `urlreq_upload`（节流口径与下载进度一致、独立游标）；**零前置**：有请求体时自动置 `UR_FLAG_REPORT_UPLOAD_PROGRESS`（类库原文约束：不置则该回调永不触发）+ 自动开 urlreq 监控，均经 `auto_prepared` 上报；验收 `_audit/verify_urlreq_upload.py` **12/12**：3MB 文件上传 → 服务端实收 3,145,728 字节（预言机一）+ 事件 total=3,145,728（预言机二）+ GET 负对照无事件 + `body_file` 不存在时给可行动错误 |
| 4 | `类_FBrowser_框架.取父框架 ()`（FBroLib.wsv:1692） | `_gap_recheck_1.md` 真缺口#2 | ✅ **已实现** | `browser_get_frames` 每项新增 `parent_id`（主框架为空串）+ `is_focused`（同为类库零调用方法 `是否为焦点框架`）；验收 `_audit/verify_frames_parent.py` **11/11**，用"嵌套 srcdoc 框架名链"当预言机：主框架无父、外层父=主框架 id、**内层父=外层 id 且 ≠ 主框架 id**（证明是层级而非平铺）、`is_focused` 恰好一个为真 |
| 5 | `类_FBrowser_浏览器.尝试关闭浏览器 (...)`（FBroLib.wsv:796） | `_gap_recheck_1.md` 真缺口#3 | ✅ **已复核：保持现状（不接线、不删桩）** | 复核结论：`browser_close_try` 现在**不是**"看起来像能力却恒失败"的桩，而是一条**刻意的能力边界拒答** —— 实现原文：`⛔ 远程关闭浏览器已禁用(本工具刻意不实现)｜真实原因: 本项目是控制台程序, 浏览器窗口就是程序窗口, 关闭浏览器等于退出整个 MCP 服务 … 想关闭请用 browser_close(可指定 browser_id 只关后台浏览器) 或 browser_shutdown(需 confirm:true)`。即：**本机不支持 + 可行动替代**（正属目标 A 线允许的失败类别），且工具描述首句已写"⛔ 该工具恒失败, 请改用 browser_close"。保留它的价值 = 代理搜"优雅关闭/先问页面"时能一次拿到真实答案，比删掉后再去撞强制关闭更好 |
| 6 | `类_FBrowserVIP_控制器.高级_创建标签浏览器`（FBroVip.wsv:1201） | `_gap_vip_events.md` 真缺口#1 | ⛔ 暂不做 | 中高风险：需确认"谷歌UI模式"前提，且项目**刻意**拒绝实现 `browser_create_tab`（`MCP_Server_System.wsv` 内已有理由与替代路径） |
| 7 | 菜单只读探针（`取数量` + `存在快捷键_索引`/`取快捷键_索引`/`取颜色_索引`） | `_gap_menu.md` §A1 | ⏳ 待做（需回调挂钩） | 唯一能在零写入下描述"默认右键菜单长什么样（可读范围内）"的工具；挂钩必须放在 `浏览器_即将打开菜单` 内 `应用菜单规格` **之前**（否则读到的是本服务刚改过的模型）；⚠ 前提需实测：`*At` 接口存在 ≠ 默认菜单上真有数据 |
| 8 | 菜单按索引写（`设置快捷键_索引`/`移除快捷键_索引`/`置颜色_索引`…） | `_gap_menu.md` §A3 | ⏳ 待做（并入既有工具） | 应作为 `browser_context_menu` 规格的新行类型（`accelat/noaccelat/colorat/checkat`），**不要**新起第二个菜单状态机（会互相覆盖） |

## 二、判定计数（三份报告）

| 报告 | 范围 | 方法数 | 已覆盖 | 等价覆盖 | 真缺口 | N/A |
|------|------|--------|--------|----------|--------|-----|
| `_gap_recheck_1.md` | `类_FBrowser_浏览器` / 辅助功能 / `类_FBrowser_框架` / 基础框架 | 143 | 94 | 12 | **3** | 34 |
| `_gap_vip_events.md` | `类_FBrowserVIP_控制器` + FBroEventControl 8 类 + 事件基础设施 | 324 | 233 | 43 | **2** | 46 |
| `_gap_menu.md` | 菜单模式(36) + 菜单环境(21) + 回调(6) | 63 | 36 | — | 可实现 14 / 做不到 13 | — |

## 三、方法论警告（都会导致"白干一轮"）

1. **候选清单不可直接实施**：`classlib_gap.py` 的"名字出现在描述里即算命中"口径同时产生误报与漏报（文首已列例）。
2. **行号口径会翻倍**：`MCP_Server_System.wsv` / `MCP_Server_Form.wsv` / `MCP_Server_Reverse.wsv` / `MCP_Callbacks.wsv`
   的行尾是 `CR CR LF`；PowerShell `Select-String` / Python `splitlines` 给出的行号 ≈ LF 口径（DSH `read`/`grep`）的 **2 倍**。
   改代码前**按符号名 grep 重定位**，不要按行号跳。
3. **"已覆盖"≠"可查"**：`app_*` 事件族 25 处"已覆盖"仅代表**接线+入库代码就位**，仓库自述本机不产出记录；
   同类问题还有"工具描述漏列事件名"（`context_menu*`/`quick_menu*` 已在本轮补进 `browser_event` 描述）。
4. **删桩也是进度**：像 `browser_close_try` 这种"恒失败但看起来像能力"的桩，比没有更糟（会诱导反复试错）。

## 四、"schema ↔ 实现一致性"专项审计（第125轮新增，**实施前必读**）

三个只读子代理按派发器文件分片，把 **322 个工具**的"schema 声明"与"实现真正读取的参数"做了机械双向 diff
（并对 `MCP命令服务器.X(..., 参数JSON)` 这类委托做深度 4 的传递闭包，避免把"由共享助手读取"误报成缺口）：

| 审计报告 | 范围 | 工具数 | 差异总数 | 其中 `MISSING_IN_SCHEMA`（最严重） |
|----------|------|--------|----------|-----------------------------------|
| `_audit/_schema_audit_A.md` | `MCP_Server_Core.wsv` | 162 | **45** | **29** |
| `_audit/_schema_audit_B.md` | `_Form`/`_System`/`_VIP` | 93 | **31** | **2** |
| `_audit/_schema_audit_C.md` | `_Reverse`/`_Kernel`/`_Workflow` | 65 | **29** | **7** |

**为什么这类缺陷优先级最高**：`MISSING_IN_SCHEMA` = 实现会读的参数**没写进 schema** ⇒ AI 代理**根本看不到它**，
只能猜或反复试错 —— 正是用户抱怨的"要试很多次才成功"。典型：`browser_reverse_instrument_script` 的 `confirm`
是 install 的硬前置却没声明（台账里它长期记 fail，成因就是"参数不可见"）。

### 已修（第125轮，共 28 项，全部编译 0 警告 + 验收通过）
- B 组 15 项：`vip_enable_js_env.confirm`、`vip_touch_cancel.x/y`、`vip_touch_emulation` 的 enable 缺省语义、
  `fill_attr_get/set`、`fill_select`、`set_preference`、`vip_execute_js_context` 的必填表、
  `fingerprint_languages` 二选一、`vip_mouse_wheel` 至少一个滚动量、`get_global_cache_dir`/`send_message`/`get_run_style`
  的描述改为与实现一致、`vip_fingerprint_ssl` **未知 tls 值改为明确拒绝**（原来静默回退成"不限制"却回 success = 假成功）。
- C 组 13 项：`reverse_instrument_script.confirm`、`kernel_events_all action=get`、`kernel_watch action=list`、
  `kernel_cdp_monitor action=list` + `max` 默认值 500→**200** 改准、`kernel_download action=list`、
  `kernel_reactor` 去掉"load_end 永不触发"的错误断言并把 `load_end`/`title_changed` 补进真实事件名清单。
- 验收：`_audit/verify_schema_audit_fixes.py` **17/17**（声明层 tools/list 断言 + 行为层真机调用：
  非法 tls 值必须失败、`fill_attr_get{selector}` 必须成功、`vip_enable_js_env` 不带 confirm 必须给可行动拒绝）。

### 遗留（A 组 Top 15 等，均有 `file:line` 证据，下一轮按序实施）
> **第135轮进展**：按要求把 3 条"刻意设计失败"逐条**受控实测**（干净实例、项间自动重启）：三个工具**按 schema 传参都能成功**（mouse_wheel 0.02s 且页面真的滚动 scrollY 0→120；enable_js_env 0.02s；instrument install 6.49s），旧失败全是**探针没传必填参**造成的假目标 ⇒ 已补 `DYNAMIC_ARGS`(confirm) 并改写为受控台账条目，**台账 323/323 通过 / 0 未通过**。同时实测推翻一处旧文案：`instrument_script` 的 `action=suppress` **已不能恢复**（`setSkipAllPauses 失败: timeout`，之后仍 35s 报错），描述已订正为"必须重启进程"；`enable_js_env` 描述补上"enable:false 不恢复(关闭后仍 30.32s)"。
> **第134轮进展**：`browser_execute_js/evaluate` 的 `file` **实测可用但失败文案误导** —— 目录外路径会被安全守卫拒绝，却报"缺少参数: 请提供 code 或 file"（调用方以为没传参）；已改为可行动报错（列出 code/code_base64/file 三种传法+ 点明"file 仅限进程运行目录内" + 给出改法）。同时把源码里既有但**未声明**的 `code_base64` 补进两个工具的 schema（免转义通道，适合含引号/换行/超大脚本）。验收 8/8。
> **第133轮进展**：**schema↔实现一致性审计收官** —— 清掉最后三个 no-op 声明（`debugger_last_paused.parse`、`reverse_scan_crypto.script_index`、`reverse_detect_obfuscator.script_index`，三者都是"声明了但实现从不读"，且已在描述里给出真正能限定范围的替代路径）。全量 323 工具扫描结果：**MISSING=0、疑死=0**（唯一剩余差异 `evaluate.max_ms` 属入口公共参数，非缺陷）。验收 5/5（含三个工具的真机回归）。
> **第132轮进展**：扫描器加 **闭包分析**（跟到共享助手，38 条差异 → 4 条）+ 补齐读取件清单（`yyjson取小数/取长整数/取对象成员_安全` 与限定接收者的对象式读取）—— 消除了两类假象；据此找出并修掉真实缺陷：`browser_fingerprint` 的 geolocation 只认 `latitude/longitude` 而 schema/兄弟工具用 `lat/lng` ⇒ **坐标被静默忽略**，现已两者都接受并都声明。验收 4/4。另记环境教训：长会话下窗口/渲染器状态会漂移（快检一次 55/56、鼠标 5.08s），干净重启即恢复 56/56，**延迟类断言失败前必须先干净复现**。
> **第131轮进展**：**全量 323 工具扫描 → MISSING(实现读却未声明) 清零**：12 个工具共 20 个参数补齐（back/forward 的 wait_for_load+async_only、cdp_event 的 event、console_eval 的 file、file_dialog 的 file_path/path、intercept 的 x/y/width/height、reverse_extract 的 script_id、instrument_script 的 verify、reverse_websocket 的 requestId、mcp_help 的 name/tool）。扫描器同时修了两个自身缺陷（花括号配平要跳过字符串、空前缀要全量扫）。验收 9/9，其中"重跑全量扫描 MISSING=0"是穷尽性证明。
> **第130轮进展**：`browser_get_text.max_chars` 由"声明未读"改为**真的截断**（实测 truncated_to=50）；补 `set_breakpoint` 的 `line_number/column_number`、`workflow_run` 的 `file` 与 **steps 字段表**（真跑 3 步内联工作流验证 total_steps=3）、`reverse_websocket` 的 `request_id` 并把 query 的真实语义（Network.getResponseBody，**不是**解码后的 WS 帧）写清；修好测量件 `_show_branch_params.py` 的分支匹配（隔行留空的文件会切错）。验收 12/12。
> **第129轮进展**：`browser_fingerprint` 补 17 个未声明参数（类型由实现读取函数判定）、`browser_collect` 补 4 个；把"通用参数(browser_id/max_ms/async_only/sync_wait)"与"HTTP 通道 ~1MB 会被断连且无错误码"写进 `initialize.instructions` 与 `mcp_help` 提示；新增可复用测量件 `_audit/_show_branch_params.py`。验收 8/8 + 8/8。
> **第128轮进展**：已修 `kernel_scheme` 的"空内容也回 success"、`kernel_ipc_clear/queue` 的 action 静默退化（未知 action 会退化成读取）；幽灵工具 `browser_debugger_pause` 已补注册（322→323），从"看不见的守卫"变成"看得见的守卫"（调用仍按设计拒绝），台账按人工受控记 pass。验收 `_audit/verify_kernel_guards.py` 12/12。
> **第127轮进展**：已修 `browser_dom_query.index`（静默错答案）、`dom_set_value.allow_empty`（死路）、`network.auto_enable`、`inject.inject_id`、`reverse_hook.url_pattern`、`view_source`（描述+max_chars）、`file_dialog`（描述）、touch 三件套 `kernel`；并记录一条陷阱：**改 schema 后必须用 tools/list 复核**，因为"在 helper 生成的整段 schema 后拼接"会产出非法 JSON 而被整段丢弃（编译与快检都发现不了）。
1. `browser_touch_press/_release/_move`：描述承诺 `kernel:true` 但 schema 只有 x/y（同族 mouse_* 都声明了 → 家族内自相矛盾）
2. `browser_file_dialog`：描述"打开对话框"但实现注释明写**不弹窗**，且 schema 零属性
3. `browser_view_source`：描述"在新标签打开 view-source"，实现只回文本；`max_chars` 未声明
4. `browser_dom_set_value`：报错指引 `allow_empty:1` 但该参数未声明、`value` 又是 required ⇒ **死路**
5. `browser_collect`：描述写了 `keyword`/`limit`，schema 只有 `action`
6. `browser_get_text.max_chars`：声明了但实现**从不读**（截断写死常量）
7. `browser_fingerprint`：6 组 19 个维度参数（min/max/seed、sample_rate、public_ip、latitude…）全部未声明
8. `browser_dom_query.index`：**静默失效**（返回第 1 个匹配，比报错更危险）
9. debugger 家族的 CDP 原生别名（`line_number`/`scriptId`/`url_regex`…）未声明
10. `browser_network.auto_enable`、`browser_inject.inject_id`、`browser_intercept` 的 width/height/x/y、
    `browser_reverse_hook.url_pattern`、`browser_execute_js` 的 `code|file` 二选一与 `code_base64`
11. B 组遗留：`set_css_version/set_web_version/set_v8_version` 数值范围、`vip_orientation` 的 1..4 映射、
    `enable_inspector`/`enable_devtools_observer` 的旧文案、`load_extension` 的 path|crx_path、
    `set_window_style` 的 -16/-20/-12 白名单、`shutdown` 的 1~3 秒钳制
12. C 组遗留：`workflow_run` 的 steps 字段表、`reverse_websocket query` 实为 `Network.getResponseBody`（且需 `request_id`）、
    `scan_crypto`/`detect_obfuscator` 的 `script_index` 声明未用、`workflow_run/get` 的 `file` 别名、
    `kernel_ipc_clear`/`kernel_scheme` 的**静默成功无校验**、`kernel_download` 的 download_id 形态
13. **幽灵工具**：`browser_debugger_pause` 有完整实现分支 + 命令行注册表项，但**没有 `添加工具JSON`** ⇒ 不进 tools/list，
    代理永远看不到（A 组 §表外发现；要么补注册，要么按"刻意禁用"写明理由）
14. 系统性观察：公共层参数几乎没写进 schema（`sync_wait` 322 个注册里声明 **0** 次、`async_only` 1 次、`browser_id` 1 次、
    `max_ms` 8 次）—— 值得单独一轮决定"是否统一声明"（它们由入口统一处理，声明后才可被发现）

## 五、第136轮新增：让 `browser_reverse_instrument_script` 可连续使用的实现方案

目标：把"装上插装后本会话 JS 通道被打死（execute_js 60s 超时，只能重启）"变成**可用但慢（~2-3 秒）**。

做法（复用既有"卡死自救"，不重复造轮子）：
1. `MCP_Server.wsv` 静态区新增标志 **`插装已安装`**；
2. `MCP_Server_Reverse.wsv`：`Debugger.setInstrumentationBreakpoint` 处置真，`Debugger.setSkipAllPauses`/remove 处置假；
3. `MCP_Server.wsv` 的 `执行CDP并同步等待`：该标志为真时把**首次预算压到 ~2500ms**，使自救（超时且有未处理 `Debugger.paused` → 自动 resume + 重试）在 2.5s 内发生；
4. 边界：仅在标志为真时生效；实现时按本机 `Debugger.paused` 返回体核实是否含 `reason` 以进一步收窄。

验收：①install 成功 ②随后 execute_js **成功且 <5s** ③连续 3 次成功 ④remove 后回到 0.03s 级 ⑤快检 56/56 ⑥做不到就如实保留"不可逆"结论。

锚点一律**按符号名 grep 复核**，不要按行号（本文件行号会漂）。


## 六、第137轮完成：插装装上后本会话 JS 通道**继续可用**（含归因更正）

### §157.1 归因（原始 CDP 通道量测，`_audit/probe_iv_timing.py`，可复现）

| 环节 | 实测 |
|---|---|
| A 未装插装: 原始 `Runtime.evaluate` | 结果 **0.02s** 到达 |
| B 装插装后**不 resume** | 派发被拦(HTTP 侧 30s 超时), 结果**永不到达** |
| C 同一任务ID: resume 之后**继续等** | resume 本身 0.04s, **原任务ID 的结果 0.00s 就到** |
| D 对照: resume 之后**重新派发**一条 | 20s 仍拿不到结果 |

结论：暂停发生在**渲染器**里 —— 被拦的那条 CDP 请求**一直挂在渲染器队列上**，resume 一发出就**立刻**完成。
故正确做法是「**resume 后继续等原来那条请求**」；而「resume 后重新派发」会**再次命中同一条插装**
（插装拦在脚本执行前），于是又要再 resume 一次，形成 6~20s 的死循环 —— 这正是"把首轮预算压到 2500ms"
仍然失败的成因（§156.2 里"重试一次即可"的假设只对了一半）。

### §157.2 落地改动（3 处 + 1 处幂等，均复用既有件，未新造轮子）

1. `执行CDP并同步等待`（`MCP_Server.wsv`）：记下 `原始预算`；插装态把**首轮**预算压到 **900ms**；
   自救改为 `Debugger.resume`（3000ms 预算）→ **续等原任务ID**（剩余预算，下限 2000ms）→
   只有续等仍失败才退回原有的"重新派发"兜底；
2. 同一处新增**"无暂停记录 → 把压缩掉的预算补等回来"**：压缩绝不会把"慢命令"变成"提前失败"（总等待上限不变）；
3. `MCP_Server_Reverse.wsv`：install **在自检之前**置位 `插装已安装`；`suppress` 的 note 按实测更正；
   `remove` 改为**确认拦停解除后**才清标志，且本机未实现 `Debugger.removeInstrumentationBreakpoint` 时
   **自动兜底**为 `setSkipAllPauses(true)`（复用既有 `执行V8CDP命令`，不另写实现）；
4. `action=install` 重复调用改为**幂等成功**（`already_installed:true`）——旧实现把重复调用报成失败，
   正是"代理换别的方法反复试错"的触发点。

### §157.3 验收（全部运行期实测，非静态推断）

- `_audit/verify_round137.py` **8/8**：install **1.01s**；execute_js ×3 = **0.99 / 0.96 / 0.97s**（修前 60s 超时失败）；
  dom_query 0.96s；remove 0.05s；remove 后 execute_js 0.02s；`browser_status` 健康。
- `_audit/verify_round137b.py` **19/19**：①自救方式确为"续等原请求"（`auto_prepared` 原文）；
  ①b 重复 install 幂等（0.03s）；②`skip=true` 后 **2 秒忙等脚本仍成功（2.10s）** ← 证明"补等"分支确实存在；
  ③恢复拦截后 0.96s；④`remove` 走兜底成功（0.05s）；⑥remove 后再 install 成功、通道 0.03s。
- 快检 **56/56**（干净实例）；编译 **0 警告**；卫生扫描**全零**；
  台账 **323/323 = 323 通过 / 0 未通过**（`browser_reverse_instrument_script` 复测 pass 1.04s）。

### §157.4 更正与残留（如实）

- §155.3 / §156.1 的"安装后只能重启"**已不成立**，描述与报告同步更正；
  "重启可彻底清掉插装定义"仍成立（本机没有可用的单独卸载方法）。
- 本机 Chromium **未实现** `Debugger.removeInstrumentationBreakpoint`（实测 `wasn't found`），
  故 `remove` 的真实语义是"解除拦停（兜底 `setSkipAllPauses(true)`）"，而不是"抹掉定义"——描述与 note 均如实写明。
- 插装态下每条 CDP 脚本请求仍有 **~0.95s** 的固定开销（一次暂停 + 一次 resume），属机制性成本，已在工具描述里给出数字。

复核锚点（按**符号名** grep，不按行号）：`原始预算` / `救活预算` / `补等结果` / `already_installed` / `插装已安装`。


## 七、第138轮完成：把"显示出来却做不到事"的工具清零（dead-end = 0）

### §158.1 系统性扫描（不再靠"被点名才修"）

新增 `_audit/scan_deadends.py` → `_audit/_deadend_scan.md`：从 `添加工具JSON` 取**全部 323 个已显示工具**，
在 `分类分派_*` 里定位其分支，若分支**第一条可执行语句**就是无条件的 `命令失败` 返回，则判定为 dead-end
（"显示出来却永远做不到事"）。扫描结果：

| 阶段 | dead-end 命中 |
|---|---|
| 扫描前 | **1** —— `browser_close_try`（`browser_debugger_pause` 已于本轮稍早修好） |
| 修复后 | **0** |

### §158.2 `browser_debugger_pause`：从"⛔ 恒失败守卫"变成**真正可用的安全暂停**

- 原实现无条件返回"已禁用"；而项目里**早就有**安全机制 `确保调试器已暂停`
  （先显式 `Debugger.enable` → 用页面自身 `setTimeout(...,30)` 安排一个**必然很快执行**的语句给 pause 做落点
  → 再 `Debugger.pause` → 等 `Debugger.paused`），`step_over/step_into/step_out` 等 8 处已在用。
- 现改为复用它，并在调用前**武装既有的防呆网**（`暂停前事件指纹` + `待恢复暂停时间` ⇒ 主循环 `检查暂停自动恢复`
  10 秒没等到暂停事件就自动 resume，防队列被堵）；只在"调用前页面未暂停"时武装，避免误 resume。
- 实测（`_audit/verify_pause_tool.py` **11/11**）：pause **0.06s 成功**并带 `auto_prepared`；
  暂停态 `browser_debugger_last_paused` 能读到现场（`reason:other` + call_frame_id）；暂停态 `execute_js` 仍 0.03s
  （**不卡死实例**）；重复 pause 幂等成功 0.02s；`about:blank` 上也有界返回 0.17s（不挂起）。
  台账复测：**pass 0.06s**（原为人工受控条目，现已变成真测）。

### §158.3 `browser_close_try`：从"⛔ 恒失败(已废弃)"变成**统一关闭入口**

- 背景事实：类库 `尝试关闭浏览器(TryCloseBrowser)` 在本项目**恒返回假**（缺它要求的"顶层窗口关闭处理器"），
  所以老实现注定失败 —— 不是参数问题，是路径不存在。
- 修法（**转发复用，不另写关闭逻辑**）：
  · 传 `browser_id` 且**不是主窗口** → 转发 `browser_close`（真正关闭）；
  · 目标为主窗口 → 关闭它等于退出整个 MCP 服务，故需 `confirm:true`（转发 `browser_shutdown` 的安全关闭序列），
    不带 confirm 时明确拒绝并给替代。
- 归属判定踩坑并修掉：**不能用 `取主浏览器 ()`** —— 路由层已把参数里的 `browser_id` 写进静态 `目标浏览器ID`，
  而 `取主浏览器()` 在该值 >0 时返回的**就是目标自己**，于是"目标==主窗口"恒成立（实测现象：传后台浏览器 id 却报
  "需 confirm:true"）。改按 `FBrowser_浏览器_取ID清单 ()` 的**最小 id** 认定主窗口（枚举方式与 `browser_list` 一致）。
- 实测（`_audit/verify_close_try.py` **12/12**）：后台浏览器 `browser_id=2` → `browser_close_try` 成功关闭，
  `browser_list` 回读 `[1,2]→[1]`；无效 id → 明确失败；不带 confirm 关主窗口 → 可行动拒绝；
  `confirm:true` → **程序真的退出**（`browser_status` 3.5s 内不再可用）；重启后一切正常；
  `tools/list` 复核 schema 三参数齐备（改 schema 必须运行期复核）。

### §158.4 状态

| 指标 | 值 |
|---|---|
| 工具数 | **323** |
| dead-end（已显示却只会失败） | **0** |
| 台账 | **323/323 = 323 通过 / 0 未通过** |
| 快检 | **56/56**（干净实例） |
| 编译 | **0 警告** |
| 卫生扫描 | **全零**（操作备注/死代码备注/残注释/零引用方法/零引用成员/重复分支/幽灵注册） |
| 剩余"刻意的守卫" | 2 个：`browser_create_tab`、`browser_task_runner_post` —— 二者**不在 tools/list 里**（未显示），
且被调用时给出明确原因与替代，不影响"已显示能力必须可用"这一条 |

复核锚点（按符号名 grep）：`scan_deadends.py` / `ct清单` / `确保调试器已暂停` / `检查暂停自动恢复`。


## 八、第139轮完成：菜单族补齐（只读实况快照 + 按索引写 + wipe）与 4 处"承诺了却没生效"的静默缺陷

### §159.1 静默缺陷（已修，编译 0 警告，逐条有实测/静态证据）

| # | 缺陷 | 证据（修前） | 修法 |
|---|------|--------------|------|
| 1 | `browser_key_event.modifiers` **声明了却在 VIP 路径被丢弃** ⇒ Ctrl/Shift/Alt 组合键静默失效 | `MCP_Server_Core.wsv` 的 VIP 三分支只传 `key`；只有 CEF 退路写 `按键事件.修饰位` | 三处都传第 2 参（类库约定 **Alt=1/Ctrl=2/Meta=4/Shift=8**）；CEF 退路按语义换算成 CEF 旗标（Shift=2/Ctrl=4/Alt=8/Command=16），不再把掩码直接塞进去 |
| 2 | `browser_context_menu action=set` 的载荷**不是合法 JSON**（拼接漏逗号：`"warnings":""spec_lines":`） | 实测 `json.loads(data)` 失败 | 补回逗号（`","spec_lines":`） |
| 3 | `browser_vip_mouse_press/release` **永远按左键**（类库第 3 参 `按键类型` 从未传）+ 缺 x/y 时退化成在 (0,0) 按下 | 无 `button` 参数、无 x/y 守卫 | 补 `button`(0/1/2) + x/y 必填守卫；`browser_vip_mouse_click` 补 `delay_ms`（类库第 4 参 `单击延时` 被截断） |
| 4 | `browser_fingerprint_pixel_ratio.value` 声明为 `text`（实现按小数读） | schema 类型与语义不符 | 改 `number` 并注明文本也接受（读取器已对文本节点归一化） |

### §159.2 菜单族补齐（`_gap_menu.md` §A1/§A3 两条"待做"落地）

- **只读实况快照**（新工具 `browser_menu_probe`，注册号 1330）：在 CEF 回调内、**施加规格之前**读。
  实测拿到 **declared_count=17 / read_count=17**，其中 **6 项带快捷键提示**；每次"菜单被打开"最多采一次；
  武装 30 秒内有效，`get` 支持 `wait_ms` 等一次晚到的采集。
- **按索引写**（并入既有 `browser_context_menu`，不新起第二个菜单状态机）：行类型
  `accelat` / `noaccelat`（可回读）/ `checkat` / `colorat` / `fontat`（后三者类库无 getter，记入 `verify_unavailable`），
  第 3 列是**索引**；另加 `wipe`（清空本次菜单，必须**唯一一行** + `confirm_wipe:true`）。
- **实测推翻一条旧结论**：规格 `item|…|26501|1|0|` + `accelat||17|1|0|70C` + `accelat||0|1|0|70C` 施加后
  **`verified_items=2` 且 `apply_failed` 为空** ⇒ **按索引可以改到浏览器默认菜单项**（第 0 项也成功，
  `存在快捷键_索引` 回读为真）。旧结论"默认项改不动"只对**按命令ID**的修改类成立。
- **另一个实测缺陷并已修**：索引类行会**重复落进**公共快捷键块（那段按命令ID设快捷键），
  于是"生效了却额外多出两条 `[accel N 未生效]`"污染 `apply_failed`；已加排除条件，修后 `apply_failed` 为空。
- **诚实边界（写进工具描述）**：原生右键菜单是**模态**的 ——
  第 1 次 `arm` 必成功（0.03~0.36s），第 2/3 次必然等不到回调，且 CDP 的 Esc（走渲染器）**关不掉**它
  （加了"清场 + 3 次尝试"后仍第 2 次必失败）。故 `arm` 只派发**一次** + 短等 1.5 秒，抓不到就**如实**返回
  "已武装 + 原因 + 两条下一步"，不再白等 5.7 秒。快照可读范围只有**条目数 + 每项是否带快捷键提示**
  （`是否可见/是否选中/取菜单类型/取分组ID/取子菜单` 全部收**命令ID**，对未知 ID 的默认项读不到 —— 不谎报）。

### §159.3 验收与状态

| 项 | 结果 |
|---|---|
| `_audit/verify_menu_probe.py` | **22/22 通过**（快照 / 索引写 / 诚实回包 / 守卫 / 收尾健康） |
| 台账 | **324/324 = 324 通过 / 0 未通过**（新工具 `browser_menu_probe` 已测 pass 1.94s） |
| 快检 | **56/56**（干净实例） |
| 编译 | **0 警告** |
| 卫生扫描 | **全零**（操作备注/死代码备注/残注释/零引用方法/零引用成员/重复分支/幽灵注册） |

**流程教训（写下来避免重犯）**：验证脚本自己的 `payload()` 只处理"`data` 是字符串"这一种形态，
遇到"`data` 直接是对象"就把 `apply_count` 读成 `None`，一度误判成"规格没施加" ——
**探针解析器也要当被测对象**（与 build_args 漏解包同一类问题）。


## 九、第140轮完成：修复"注册成功却永不执行"的 CDP 预注入 + 两处诚实化 + 启动期事件可观测

### §160.1 `browser_reverse_preload`：修前是**假能力**（注册成功，脚本永不执行）

三臂对照实测（同一实例、干净重启、导航到带时间戳的新地址、读双哨兵）：

| 臂 | 做法 | 导航后 `window.__plS` |
|---|---|---|
| A | 只调 `browser_reverse_preload`（**修前行为**） | **`undefined`** —— CDP 回 `success` + `identifier:1`，脚本从未执行 |
| B | 先 `Page.enable` 再注册 | **`C1`** ✅ |
| C | `Page.enable` + 连续注册两次 | **`C1`** ✅ |

⇒ 在本机 `Page.addScriptToEvaluateOnNewDocument` **必须先启用 Page 域**才生效。
而多个工具描述把 `browser_reverse_preload` 推荐为"在所有页面JS之前注入 / 拦打包器最稳"的路径 ——
**修前那条建议指向一个静默无效的通道**。

修法（零前置，遵循项目既有 `auto_prepared` 惯例）：`browser_reverse_preload` 内部先 `Page.enable`，
失败则**明确失败**（而不是回一个假成功），成功则 `记录自动补域 ("Page")` 让回包带 `auto_prepared: Page.enable`。
旁证：注册动作本身**不会**拖慢 JS 通道（注册前后 `execute_js` 均 0.03s）。

### §160.2 `browser_inject {persist:true, type:"handler"}`：从"静默改变语义"改为**可行动拒绝**

实测：传 `handler` 时其代码最终走 `浏览器_载入开始 → 应用持久V8到框架 → 框架.执行JS代码`，
即被当作**普通页面 JS** 执行（哨兵 `window.__mcpHandlerRan='H1'` 在重载后可读），
**不是**它承诺的"页面 JS 调原生并同步回值"的原生桥。真实 handler 桥需要渲染进程内
`FBrowser_V8_注册JS扩展` / `FBrowser_JS交互_注册`，而本项目渲染进程事件不派发到主进程、
JS 交互桥也已两轮实测判定不可用。

修法：`type=handler` 明确拒绝 + 给出三条**实测有效**的替代（`type:js + persist:true`、
`browser_reverse_preload`(已修)、`browser_execute_js`），并如实说明"现状会被当普通 JS 跑"。
同时订正了 `type:js` 分支的注释：真正生效路径是 `浏览器_载入开始`（旧注释写的 `渲染_即将创建V8环境`
是渲染进程事件、在本项目不派发）。

### §160.3 启动期事件：从"永久丢失"到**可查**（两个成因叠加，都已修）

| 成因 | 说明 | 修法 |
|---|---|---|
| ① `记录事件日志` 在 SQLite 未就绪时直接 `return` | 启动期事件都早于 `启动MCP服务器`（SQLite 打开） | 改为进**内存环形缓冲**（每条 5 成员，上限 40 条），DB 就绪后由写入路径**与查询路径**双向 flush（只靠写入路径 flush 会因"之后再无同族事件"而永远查不到） |
| ② 内层总闸 `是否监控应用事件` 默认假 | `记录应用监控事件` 包装里还有一道总闸，且只能在启动**之后**打开 ⇒ 本族开关判过也没用 | 5 处启动期记录点改为**直调** `记录应用事件`（它们已各自判过本族开关）；`是否监控启动流程` 改**默认真** |
| ③ 查询闸门漏算本族开关 | `app开关已开` 只算了总闸/渲染/WS 三族，漏了启动族与扩展族 ⇒ 事件已入库却报"开关未开启" | 补全五族开关 |

**实测（修后，同一实例）**：`app_startup_cmdline` **1 条**（data=`{"process_type":""}`）、
`app_startup_request_context_ready` **2 条**、`app_startup_child_process` 多条 —— 三者修前都是"查不到"。
同时把过宽文案按实测**收窄**：`app_render_*` / `app_v8_*` / `app_render_ws_*` 由渲染进程触发、本机不派发
（仍然不入库）；而**主进程族**（启动期 / 扩展生命周期）会入库。旧文案"整个 app_* 族永远不会入库"已更正
（`MCP_Server_Core.wsv` 两处 + `main.wsv` 注释）。

### §160.4 验收与状态

| 项 | 结果 |
|---|---|
| `_audit/verify_round140.py` | **12/12** |
| 台账 | **324/324 = 324 通过 / 0 未通过**（`browser_reverse_preload` 复测 pass 0.05s 且带 `auto_prepared: Page.enable`；`browser_inject` pass） |
| 快检 | **56/56** |
| 编译 | **0 警告** |
| 卫生扫描 | **全零** |

**流程教训（第二次同类）**：本轮又一次在**探针**上栽跟头 —— `event_count()` 只处理"`data` 是对象"，
遇到"`data` 是列表"就把**已有记录**读成 `-1`；另有断言把文案里的 `type:js` 写成 `type=js`。
结论：**探针解析器与断言字面量同样属于被测对象**，失败时必须打印原文（本轮已按此打印全文定位）。

### §160.5 顺带修掉两处"探针缺参假失败"（不是产品缺陷）

复测事件族工具时 `browser_collect` / `browser_network` 记成 fail，回包原文分别是
`未知action:  | 支持: …` 与 `action 不能省略 | 可用: list(查询, 不改开关) / …`，且 `args={}` ——
即**探针没传 action**，撞上了工具自己的缺参守卫（那测的是守卫，不是实现）。
按 `mass_probe.py` 里 `TOOL_ARG_OVERRIDES` 表头写明的既有做法，补两个**只读且无害**的值：
`browser_collect{action:"get"}`、`browser_network{action:"list"}`。复测双双 **pass**，台账回到 **324/324**。


## 十、第141轮完成：三个纯函数工具 + 整页截图（此前做不到）+ **修掉"截图打死 CDP 通道"**

### §161.1 新增三个工具（327 = 324 + 3）

| 工具 | 类库依据 | 解决的问题 |
|---|---|---|
| `browser_json` | `FBrowser_Parser_解析JSON`(433) / `写入JSON`(450) / `字节值解析为JSON`(443) | 代理拿到的常是 JSON 文本却**没有可信的合法性判据**；`validate` 给确定结论（非法也回 success + `valid:false`，那是校验结论不是故障）、`normalize` 回规范化 JSON、`from_base64` 走类库字节入口（不猜编码）；`allow_trailing_commas` 透传类库选项 |
| `browser_data_uri` | `FBrowser_Parser_取数据URI`(394) | 以前只能"base64 编码 + 手工拼 `data:` 前缀"，容易漏 mime/编码声明 |
| `browser_by_index` | `FBrowser_浏览器_通过序号取浏览器`(487) | 补齐序号语义；类库原文"获取失败返回**空浏览器**" ⇒ 越界**明确失败**并附 ID 清单便于交叉核对（序号与 `browser_list` 不保证同序，已在描述里写明） |

验收 `_audit/verify_round141.py` **23/23**：合法/非法 JSON 判别、`allow_trailing_commas` **判别差**、
normalize 往返结构等价、`from_base64` 与文本入口一致、非法输入走 normalize 给可行动失败、
data URI 载荷**独立 base64 解码一致** + **页面 `fetch` 真读到**（标题预言机）、by_index 与 browser_list 交叉核对 + 越界可行动失败。

### §161.2 `browser_screenshot`：整页截图此前**根本做不到**，且 `width/height/scale` 一直被忽略

实测（三臂，判据 = **PNG 头解析出的像素尺寸**）：

| 臂 | 参数 | 结果 |
|---|---|---|
| A | 默认（`fromSurface` 写死假）+ 800×600 | **(984, 705)** —— 宽高被忽略，拿到的是窗口可见区 |
| B | `from_surface:true` + 800×600 | **(800, 600)** ✅ rect 生效 |
| C | `from_surface:true` + `full_page`（页面 scrollHeight=5350） | **(984, 5350)** ✅ 与 scrollHeight 完全一致 |

⇒ 第 4 参 `是否表面` 决定"截 view(窗口) 还是 surface(按 rect 区域)"；项目把它写死成假，
于是**对外宣称的 `width/height/x/y/scale` 一直静默无效**。已改默认真（想回到旧行为显式传 `false`）。

### §161.3 高影响缺陷：**类库截图路线会把本会话 CDP 命令通道打死**（已改走 CDP）

| 路线 | 截图本身 | 截图后的 CDP 命令通道 |
|---|---|---|
| 类库 `高级_网页截图`（VIP 内核路线） | 正常 0.05s | **被打死**：之后原始 `Runtime.evaluate` 30s 超时、`execute_js` 30~35s 才靠原生回退返回或直接失败、`debugger_enable` 20s 超时；`注销CDP观察者`+重挂**也救不回来** ⇒ 用户看到的正是"截完图之后每个工具都要等半分钟、还会连续失败" |
| CDP `Page.captureScreenshot` | 正常（视口 0.04s / 整页 0.17s） | **完全健康**：截图前后 `execute_js` 都是 0.03s（两臂各测两次） |

修法（不重复造轮子 —— CDP 本就是项目主通道）：
1. `browser_screenshot` **默认走 CDP** `Page.captureScreenshot`（支持 format/quality/fromSurface/captureBeyondViewport/clip），
   图片**同步回包**（无需 `mcp_result` 轮询）；
2. `via:"library"` 才走类库路线，且回包**如实警告**"该路线会让本会话 CDP 命令通道失效"；
3. 非法 `via` 明确拒绝。

途中踩到两个坑（都已修）：① CDP 载荷在同步结果的 **`message`**（裸通道实测形态）而非 `result`，需容错提取；
② 本项目 YYJSON 对象**不支持嵌套对象成员**，`clip` 用"文本成员"传会被 CDP 判 `Invalid parameters` ⇒ 参数整段拼接。

验收 `_audit/verify_round141N.py` **11/11**：整页高度 == scrollHeight、**截图后 `execute_js` 仍 0.03s**、
连截 3 张后仍 <1s、rect 生效（800×600）、jpeg 质量透传（q10 6968 字节 vs q95 23104 字节）、`via` 守卫。

### §161.4 状态

| 项 | 结果 |
|---|---|
| 工具数 | **327** |
| 台账 | **327/327 = 327 通过 / 0 未通过**（新工具均已测 pass；`browser_screenshot` 复测 pass 0.08s via=cdp） |
| 验收 | `verify_round141` **23/23**、`verify_round141N` **11/11** |
| 快检 / 编译 / 卫生扫描 | **56/56** / **0 警告** / **全零** |

**流程教训（第三次同源）**：`browser_by_index` 复测记 fail，根因是**探针造了越界序号**(通用整数兜底 10)
撞上工具守卫 ⇒ 已按 `mass_probe` 既有做法补 `index:0`。探针的"通用兜底值"必须落在**运行期合法域**内。

---

## §162 第142轮: DOM 族真执行化(实测记录)

### §162.1 根因与通道纪律(经 7 个探针实测)
- **毒化源钉死**: 类库 `开发者DOM.启用("all")` 与 `预查找文本`(即使调用失败)都会**延迟打死本会话 CDP 通道**
  (之后每条 CDP 命令 30s 才返回, 需重启)。此前"分支内提交 nodeId 命令会挂住"的结论是**被该毒化污染的误判**。
- 我方 CDP 通道(DOM 域)全程 0.02~0.08s 且零毒化; `DOM.enable(includeWhitespace:none)` 经我方通道安全且可复用
  (新增中央辅助 `确保DOM域已启用`)。
- 本机 CEF 事实: ① performSearch/getSearchResults 需先 enable; ② 搜索结果要真实 nodeId 必须先 getDocument
  填充映射(否则 nodeIds 全 0); ③ 每次 getDocument 都**重建节点映射**(同一元素三次枚举 nodeId 18/36/54)并作废旧
  搜索会话; ④ **无 DOM.discardSearch**(实测 -32601) → disable+enable 重建等效清除(实测证实); ⑤ setOuterHTML
  为替换语义(旧 nodeId 可能作废), 提交成功+旧 id 消失=已替换确认; ⑥ CEF 序列化把属性引号归一成双引号
  (提交 `<b id='bold'>` 回读为 `<b id="bold">`), 回读比对需引号归一兜底。

### §162.2 工具升级
- `browser_vip_dom_search`: 类库异步两步 → **单次调用**(enable→getDocument 填充→performSearch→getSearchResults),
  回包 searchId/resultCount/returned/nodeIds; 新增 from_index/to_index 翻页(自动收敛 resultCount; 0 命中直接回空)。
- `browser_vip_dom_node_edit`: "可行动路由" → **真执行+回读验证**。node_id/selector 双路径(selector 内部
  getDocument+querySelector 定位, 抗映射重建, 推荐); 失效 node_id → 可行动报错(重新枚举/改 selector);
  回读: 属性类 getAttributes、源码/节点值类 getOuterHTML、remove_node 以 Could not find node 为已删确认、
  setOuterHTML 以旧 id 作废为已替换确认; 验证失败如实报错不假成功; discard_search 用 disable+enable 重建说明等效清除全部会话。
- `browser_vip_dom_get_document`: 保持 CDP 路线; pierce=true 安全闸门(含 author shadow root 页面拒绝, 页面侧廉价探测);
  描述补 nodeId 有效期(每次枚举重建映射)。

### §162.3 验收
| 项 | 结果 |
|---|---|
| `verify_round142f` | **43/43**(枚举×3 可重复 / pierce 闸门 / node_id+selector 双路径真执行且页面侧回读一致 / 搜索单次取回 / 翻页 / discard / 失效 id 可行动 / 全程健康探针 ≤1s) |
| 台账 | **328/328** pass; DOM 三件套复测 pass |
| 快检/回归 | fastcheck **56/56** / 137b **19/19** / menu_probe **22/22** |
| 编译/卫生 | 0 警告 / 全零 |

---

## §163 第143/144轮: 每轮一测(用户新要求) + 类库面全量分诊

### §163.1 每轮只测一个(台账 OK_MANUAL → OK_LIVE)
- 候选清单 = 台账 8 个"人工核对、未真机实测"项(`_audit/find_untested.py` 重扫; 落账 `_audit/mark_live.py`)。
- **第143轮 `browser_close`**(`verify_round143_close` 12/12): 受控第二后台浏览器实测 → 发现"关闭异步生效、
  成功回执先于生效"缺陷 → **已修**: 提交后轮询 ≤2.5s 确认清单移除(回读确认), 未确认如实报错。→ OK_LIVE。
- **第144轮 `browser_close_try`**(`verify_round144_close_try` 15/15): 非主浏览器直关+回读确认 / 主窗口守卫
  (confirm:true 才走 shutdown, 拒绝文案含替代) / 负控可行动。→ OK_LIVE。
- 剩余候选 6: browser_reverse_patch / browser_set_preference / browser_set_s5_proxy / browser_shutdown /
  browser_vip_enable_js_env / browser_vip_mouse_wheel。

### §163.2 类库面全量分诊(6 个子代理并行, 只读; 结论均已入轮内汇报)
- 类_FBrowser_浏览器 6 候选: **全部误报**(已有等价工具); 真增强 3 处(browser_clear_cache 补 origin/targets/storage_types;
  browser_start_download 补 save_dir(须联动事件侧); 无窗口后台浏览器窗口操作加护栏)。
- FBrowser辅助功能: 真缺口 browser_by_id / browser_count(低优先); base64 二进制出口半个缺口(改造 browser_base64_decode
  或指向 browser_codec)。
- 类_FBrowser_命令行 9 项: 6 项已覆盖(config 通道); 真缺口 远程调试端口/全局代理/单进程(均启动级, 需重启);
  **启用无头模式 = 类库复制粘贴 Bug**(方法体=自动播放函数) → 永久封堵不接。
- 类_FBrowser_菜单模式: 36 方法, 已覆盖 25/36; 可补 4 项(索引类真值回读 取快捷键_索引/取颜色_索引、自建项
  verify(取菜单类型/取分组ID/取快捷键/取颜色)、取子菜单 修父ID寻址缺陷、按命令ID 的 color/font); 13 项能力原生级做不到;
  **取菜单标签 一参包装 vs 原生两参声明 → 预期编译不过, 不可用**。
- 类_FBrowserVIP_控制器(115 公开方法): 100 个驱动工具面; 真缺口 6 项(过滤器_替换资源_数据/文件、过滤器_修改内容、
  过滤器撤销、高级_创建标签浏览器、browser_set_proxy 第4参); **确认 bug: browser_vip_get_js_env_ids 对文本列表用
  取整数值 → ids 全 0**(类库注释+官方例子 main14.wsv 佐证, 待修); 高级_执行JS 5 个硬编码参数待暴露
  (timeout_ms/repl_mode/user_gesture/silent/disable_breaks)。
- 类_FBrowser_应用事件(30 公开方法): 30/30 已接线; **B-7 双闸不一致真 bug**: event_extension_enable /
  event_render_enable / event_renderws_enable 只置族开关不置总闸 是否监控应用事件 → "已启用"回执但一条不落库
  (假成功回执, 待修); WS 收发/创建关闭事件记空串(B-1..B-3); app_startup_webkit_init 族归属文案不一致(B-8)。

### §163.3 每轮一测收官(第144~150轮)
8 个 OK_MANUAL 候选**全部转 OK_LIVE**, `find_untested.py` = **0**(里程碑达成):
- 144 browser_close_try 15/15(非主直关+回读确认/主窗口守卫/负控)
- 145 browser_reverse_patch 16/16(dry_run 不替换; 实改热替换; 页面侧 V1→V2 回读)
- 146 browser_set_preference 16/16(**修复假成功**: 字体类 pref 对既有/新建浏览器均无页面侧效果且未知名不报错
  → 回包与描述改诚实边界"写入存储, 非行为保证")
- 147 browser_set_s5_proxy 14/14(死端口代理阻断异源导航→错误页; 清除后同导航恢复; CDP 不毒化)
- 148 browser_shutdown 9/9(守卫→confirm:true→进程 3.6s 真退出→重启可恢复)
- 149 browser_vip_enable_js_env 14/14(启用/关闭**双向**毒化 CDP 与警告一致、重启恢复; **修复**: 关闭路径原静默
  毒化 → 补诚实警告)
- 150 browser_vip_mouse_wheel 12/12(**修复**: 调用前自动 显示隐藏窗口(真) —— 内核注入效果受窗口前台状态影响,
  默认流程实测出现过回包成功但页面侧不滚; 修复后 scrollY=700; 毒化与警告一致; CDP 版 browser_mouse_wheel
  对照 0.03s 不毒化且页面侧回读一致)
规矩固化: 后续新增工具必须真机实测落账, 不允许再出现 OK_MANUAL。

---

## §164 第151~163轮: B线能力缺口实现与修复(逐轮记录)

- **151 修复 browser_vip_get_js_env_ids 取整数 bug**: 类库文本列表用 取整数值 → ids 全 0(官方例子 main14 佐证);
  改 取文本值 并实测揭露清单元素是**上下文对象 JSON 文本**, ids_int 两级解析 context.id 提取真实 id。
  验收 verify_round151_envids 8/8。附带修复 mark_live 台账轮次类型 bug(字符串轮次致 max+1 崩溃)。
- **152 新工具 browser_by_id / browser_count**(328→330): 交叉核对确认的真缺口; 受控验收 verify_round152_byid 14/14;
  台账逐个实测 pass。
- **153 修复事件族双闸假成功(B-7)**: event_extension_enable 只置族开关不置总闸 → "已启用"回执但 app_extension_*
  不落库; 现同时打开总闸并如实回执。verify_round153_gate 7/7。
- **154/155 VIP 响应过滤器三件套**(330→333): browser_vip_filter_patch_text(文本改写 4 模式×5 匹配)、
  browser_vip_filter_replace_data(body/base64 整体替换)、browser_vip_filter_replace_file(本地文件版+路径遍历拦截)。
  页面侧回读验证 19/19+19/19+13/13; 过滤器不毒化 CDP。
- **156 browser_vip_execute_js_context 六参数暴露**(timeout_ms/repl_mode/user_gesture/silent/disable_breaks/
  include_command_line_api, 原全部写死) + 默认路径自动解析 context_id(原报不可行动的"VIP操作失败")。
  verify_round156_execparams 11/11。
- **157 browser_clear_cache 全局版参数粒度**(origin/targets/storage_types) + 共享解析器 解析清理掩码列表
  (与 clear_cache_browser 去重 ~45 行)。行为级验证(页面侧 localStorage 清除) 13/13。
- **158 菜单索引真值回读**: 快照 accel{key_code,shift,ctrl,alt} 四元组(取快捷键_索引, 默认菜单项可读: index0=Alt+Left);
  accelat 施加后真值比对。verify_round158_menuaccel 11/11; 回归 22/22。
- **159 browser_start_download save_dir**(工具侧+事件侧联动单次消费): 文件落进自定义目录回读验证 8/8;
  顺手修复下载分支 ftp 协议放行矛盾(共享校验器放行但文案说仅 http/https)。
- **160 取子菜单 父ID寻址修复**: 原"只看父ID!=0挂最近子菜单"多 sub 必挂错; 改 取子菜单(父ID) 精确寻址 +
  **成员数回读**(取数量≥1 决定性证明)。verify_round160_parent 9/9 + 孤儿对照 7/7。
- **161 自建项类型回读**: 取菜单类型 包装 菜单项类型取值, 四创建分支(item=1/check=2/radio=3/sub=5)真值回读;
  按命令ID accel 改 取快捷键 真值比对。verify_round161_ownitems 9/9。
- **162 颜色面**: color 按命令ID 动词 + 取颜色 回读; colorat 升级 取颜色_索引 回读; 共享 菜单颜色解析。
  **实测本机硬边界: CEF 置颜色/置颜色_索引 恒返回假**(自建/默认、text/bg、按ID/按索引全试) → 工具如实进
  apply_failed 并写入描述。verify_round162_color 11/11。
- **163 radio 群ID回读**: 取分组ID 与行内群ID 比对。verify_round163_group 9/9。
- 菜单模式 36 方法: 未覆盖 11 项处理完毕(取菜单标签=一参包装 vs 原生两参声明判不可用; 置空=设计不需要;
  置字体=类库自注"待验证"且无 getter, 只报 requested 不虚构回读)。
