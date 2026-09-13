# VIP 控制器族 + 事件/回调族 —— 类库 API 面 × MCP 工具面 逐条交叉核对

只读静态审计（未编译、未启动进程、未访问 9222、未调用任何 MCP 工具）。所有结论均可按 `file:line` 复核。

## 0. 审计口径与证据链

**类库侧（只读）**：`C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\`
- `FBroVip.wsv`：`类_FBrowserVIP_控制器` = **117 个方法**（L189–L1356），其中 2 个非公开（`指纹_虚拟内核功能` 类库自标"弃用"、`逐字分割` 为私有辅助）。
- `FBroEventControl.wsv`：8 个事件/回调类，**合计 166 个方法**
  `类_FBrowser_应用事件`(32)、`类_FBrowser_浏览器事件`(90)、`类_FBrowser_JS交互事件`(4)、`类_FBrowser_资源处理器`(8)、`类_FBrowser_资源过滤器`(6)、`类_FBrowser_服务器事件`(10)、`类_FBrowser_开发者消息事件`(7)、`类_FBrowser_URL请求事件`(9)。
- `FBroLib.wsv`：与应用事件注册/回调指针相关的类 = `FBrowser初始化控制`（`FBrowser_初始化`/`FBrowser_关闭`）+ `类_FBrowser_事件智能指针`（9 方法）。

> **任务书 ③ 的文件归属更正**：任务书称"`FBroLib.wsv` 里与应用事件相关的类（形如 `类_FBrowser_应用事件`，约 27 个方法）"。
> 实际 `类_FBrowser_应用事件` **定义在 `FBroEventControl.wsv:5`**（32 个方法），`FBroLib.wsv` 内**不存在**该类（已 grep `^类 ` 全表核对，FBroLib.wsv 的类为 `FBrowser初始化控制`/`类_FBrowser_事件智能指针`/`FBrowser类辅助`/`FBrowser辅助功能`/`类_FBrowser_浏览器`/…）。
> 本报告按"意图"覆盖：应用事件类在 §2.1 全量列出，FBroLib 侧的事件注册/指针类在 §3 全量列出。

**MCP 侧**：
- 工具注册：`src/MCP_Server.wsv` 共 **321** 个 `添加工具JSON ("...")`（含 `browser_vip_*` / `browser_fingerprint_*` / `browser_event` / `browser_collect` / `browser_kernel_*` 等）。
- 分派分支：`否则 (方法名 == "...")`，分布在 `MCP_Server_VIP.wsv`(71) / `MCP_Server_Core.wsv`(157) / `MCP_Server_Reverse.wsv` / `MCP_Server_System.wsv` / `MCP_Kernel.wsv` / `MCP_Server.wsv`。
- 事件接收：本项目的 SDK 事件**不用** `<接收事件>`（全仓库仅 `MCP_Stdio.wsv:327` 一处，属线程事件），而是**继承 SDK 事件类 + `@虚拟方法 = 可覆盖`**：
  - 应用事件 → `main.wsv:302` `类_MCP_初始化事件 <基础类 = 类_FBrowser_应用事件>`，30 个覆盖，注册入口 `main.wsv:128 FBrowser_初始化 (设置, 初始化事件)`。
  - 浏览器事件 → `MCP_BrowserEvents.wsv:19` `类_MCP_浏览器事件 <基础类 = 类_FBrowser_浏览器事件>`，90 个覆盖（L71–L3530）。**这是本项目最重要的事件流实现文件。**
  - 回调类 → `MCP_Callbacks.wsv`（DevTools 观察者 L495、URL 请求回调 L740、资源过滤器 L1010/L1085 等）。
- **事件流查询工具**：`browser_event`（分派 `MCP_Server_Core.wsv:4887`；注册 `MCP_Server.wsv:11282`）→ `查询事件日志`（`MCP_Server.wsv:5209`）。
- **事件开关工具**：`browser_collect`（`MCP_Server_Core.wsv:3704`；注册 `MCP_Server.wsv:11058`）、`browser_kernel_events_all`（`MCP_Kernel.wsv:116`；注册 `MCP_Server.wsv:11146`）。监控开关变量表见 `MCP_Server.wsv:337–388`（默认只开 载入/生命周期/标题/下载，其余族默认关）。
- **入库管道**：`记录监控事件`（`MCP_BrowserEvents.wsv:29`，开关为假时不入库但**仍触发反应器**）→ `记录浏览器事件`（`MCP_Server.wsv:8077`）→ `记录事件日志 ("browser_event", …)`（`MCP_Server.wsv:8091`）；应用事件走 `记录应用事件`（`MCP_Server.wsv:8096`）→ `log_type="app_event"`（`MCP_Server.wsv:8108`）；控制台日志 `MCP_Server.wsv:8148`（log_type=`console`）。

**行号约定（复核必读）**：本报告行号取自 DSH 的 `grep`/`read` 工具（ripgrep 语义）。部分 `.wsv` 含裸 CR，**PowerShell `Select-String` 在同一文件上会给出偏移的行号**（例：`MCP_Server_Core.wsv` 的 `browser_event` 分支，ripgrep=L4887、Select-String=L4882；`MCP_Server_System.wsv` 的 `browser_create_tab` 分支，ripgrep=L16、Select-String=L31）。复核请用 `grep`/`read`。

**判定取值**：`已覆盖`（类库方法 → 对应 MCP 工具分支，同能力）/ `等价覆盖`（用别的类库方法或 CDP 达到同能力）/ `真缺口`（类库有、MCP 无等价能力）/ `N/A`（纯基础设施、内部回调、不该暴露成工具）。

---

## 1. `类_FBrowserVIP_控制器`（`FBroVip.wsv` L175–L1361）逐条核对（117 行）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 是否为空 | FBroVip.wsv:189 | N/A | — | 指针判空，MCP 在分支内自用（如 `MCP_Server_VIP.wsv:232-245`），无暴露价值 |
| 置空 | FBroVip.wsv:194 | N/A | — | 生命周期内部操作 |
| 取浏览器 | FBroVip.wsv:199 | 等价覆盖 | browser_list `MCP_Server_Core.wsv:749` / browser_get_id `:1404` / browser_get_main_browser `:6859` | 类库是"控制器→浏览器"反向取；MCP 以 browser_id 为主键寻址，同能力 |
| 清理数据 | FBroVip.wsv:205 | 已覆盖 | browser_fingerprint action=clear `MCP_Server_Core.wsv:2306`（注册 `MCP_Server.wsv:11054`） | 工具描述明写"clear 全清(类库清理数据: 指纹/代理/wss/debugger/isTrusted 全部VIP数据)" |
| 指纹_清空调用计数 | FBroVip.wsv:211 | 已覆盖 | browser_fingerprint action=clear_count `MCP_Server_Core.wsv:2306` | `MCP_Server.wsv:11054` 描述区分 clear 与 clear_count（语义不同） |
| 指纹_取调用计数 | FBroVip.wsv:216 | 已覆盖 | browser_fingerprint action=count `MCP_Server_Core.wsv:2306` | 返回 JSON 计数文本；描述注明"是指纹API被调用次数，不是生效项数" |
| 指纹_虚拟ProductSub | FBroVip.wsv:225 | 已覆盖 | browser_fingerprint_product_sub `MCP_Server_VIP.wsv:638` / browser_vip_fingerprint_product `:1026` | 两处均调用 `vip_ctrl.指纹_虚拟ProductSub` |
| 指纹_虚拟Vendor | FBroVip.wsv:231 | 已覆盖 | browser_vip_fingerprint_product `MCP_Server_VIP.wsv:1026` | 同工具四字段之一 |
| 指纹_虚拟VendorSub | FBroVip.wsv:237 | 已覆盖 | browser_fingerprint_vendor_sub `MCP_Server_VIP.wsv:655` / browser_vip_fingerprint_product `:1026` | — |
| 指纹_虚拟UserAgent | FBroVip.wsv:243 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` / browser_fingerprint action=ua `MCP_Server_Core.wsv:2306` | 参数为 `类_FBrowserVIP_UA数据`，见 §4 附录 |
| 指纹_虚拟Languages | FBroVip.wsv:249 | 已覆盖 | browser_fingerprint_languages `MCP_Server_VIP.wsv:391` | 空文本即复位（`MCP_Server_VIP.wsv:411-415`） |
| 指纹_虚拟AppCodeName | FBroVip.wsv:255 | 已覆盖 | browser_fingerprint_appcodename `MCP_Server_VIP.wsv:604` | — |
| 指纹_虚拟AppName | FBroVip.wsv:261 | 已覆盖 | browser_fingerprint_appname `MCP_Server_VIP.wsv:374` | — |
| 指纹_虚拟AppVersion | FBroVip.wsv:267 | 已覆盖 | browser_fingerprint_appversion `MCP_Server_VIP.wsv:621` | — |
| 指纹_虚拟Product | FBroVip.wsv:273 | 已覆盖 | browser_vip_fingerprint_product `MCP_Server_VIP.wsv:1026` | — |
| 指纹_虚拟HardwareConcurrency | FBroVip.wsv:279 | 已覆盖 | browser_vip_fingerprint_hardware `MCP_Server_VIP.wsv:1014` | 参数 concurrency |
| 指纹_虚拟CookieEnabled | FBroVip.wsv:285 | 已覆盖 | browser_fingerprint_cookie_enabled `MCP_Server_VIP.wsv:547` | — |
| 指纹_虚拟DeviceMemory | FBroVip.wsv:291 | 已覆盖 | browser_vip_fingerprint_hardware `MCP_Server_VIP.wsv:1014` | 参数 memory |
| 指纹_虚拟Canvas_随机 | FBroVip.wsv:297 | 已覆盖 | browser_vip_fingerprint_canvas `MCP_Server_VIP.wsv:928` / browser_fingerprint action=canvas_random `MCP_Server_Core.wsv:2306` | 返回噪点指纹串 |
| 指纹_虚拟WebGL_随机 | FBroVip.wsv:308 | 已覆盖 | browser_vip_fingerprint_webgl `MCP_Server_VIP.wsv:940` | — |
| 指纹_虚拟Audio_随机 | FBroVip.wsv:318 | 已覆盖 | browser_vip_fingerprint_audio `MCP_Server_VIP.wsv:952` | — |
| 指纹_虚拟Canvas_定值 | FBroVip.wsv:328 | 已覆盖 | browser_vip_fingerprint_canvas_fixed `MCP_Server_VIP.wsv:673` | 与随机互斥 |
| 指纹_虚拟WebGL_定值 | FBroVip.wsv:334 | 已覆盖 | browser_vip_fingerprint_webgl_fixed `MCP_Server_VIP.wsv:690` | — |
| 指纹_虚拟Audio_定值 | FBroVip.wsv:340 | 已覆盖 | browser_vip_fingerprint_audio_fixed `MCP_Server_VIP.wsv:707` | — |
| 指纹_虚拟Plugins | FBroVip.wsv:346 | 已覆盖 | browser_fingerprint_plugins `MCP_Server_VIP.wsv:357` | 修改类型+JSON |
| 指纹_虚拟JavaEnabled | FBroVip.wsv:353 | 已覆盖 | browser_fingerprint_java_enabled `MCP_Server_VIP.wsv:564` | — |
| 指纹_虚拟Webdriver | FBroVip.wsv:359 | 已覆盖 | browser_fingerprint action=set_batch `MCP_Server_Core.wsv:2306` | 调用点 `MCP_Server_Core.wsv:2529`；反检测预设内自动置假 `MCP_Server.wsv:2228` |
| 指纹_虚拟OnLine | FBroVip.wsv:365 | 已覆盖 | browser_fingerprint_online `MCP_Server_VIP.wsv:581` | — |
| 指纹_虚拟Canvas字体指纹 | FBroVip.wsv:371 | 已覆盖 | browser_vip_fingerprint_canvas_font `MCP_Server_VIP.wsv:975` / browser_font_randomize `:453` | Canvas 2D measureText 度量，独立维度 |
| 指纹_虚拟CSS字体指纹 | FBroVip.wsv:378 | 已覆盖 | browser_vip_fingerprint_font `MCP_Server_VIP.wsv:964` / browser_font_randomize `:453` | 字体清单+宽高偏移 |
| 指纹_虚拟屏幕XY | FBroVip.wsv:387 | 已覆盖 | browser_fingerprint_screen_xy `MCP_Server_VIP.wsv:777` | window.screenX/screenY |
| 指纹_虚拟屏幕分辨率 | FBroVip.wsv:396 | 已覆盖 | browser_vip_fingerprint_screen `MCP_Server_VIP.wsv:1000` | — |
| 指纹_虚拟屏幕可用高度和宽度 | FBroVip.wsv:405 | 已覆盖 | browser_vip_fingerprint_screen `MCP_Server_VIP.wsv:1000` | 同工具 avail_w/avail_h |
| 指纹_虚拟屏幕pixelDepth | FBroVip.wsv:414 | 已覆盖 | browser_vip_fingerprint_screen `MCP_Server_VIP.wsv:1000` | 同工具 pixel_depth |
| 指纹_虚拟屏幕colorDepth | FBroVip.wsv:422 | 已覆盖 | browser_vip_fingerprint_screen `MCP_Server_VIP.wsv:1000` | 同工具 depth |
| 指纹_虚拟DevicePixelRatio | FBroVip.wsv:430 | 已覆盖 | browser_fingerprint_pixel_ratio `MCP_Server_VIP.wsv:742` | — |
| 指纹_虚拟Webglvendor | FBroVip.wsv:438 | 已覆盖 | browser_fingerprint_webgl_vendor `MCP_Server_VIP.wsv:422` | 同工具同时设 vendor+renderer（L441/L444） |
| 指纹_虚拟Webglrenderer | FBroVip.wsv:446 | 已覆盖 | browser_fingerprint_webgl_vendor `MCP_Server_VIP.wsv:422` | — |
| 指纹_虚拟Rect | FBroVip.wsv:454 | 已覆盖 | browser_vip_fingerprint_rect `MCP_Server_VIP.wsv:725` | — |
| 指纹_虚拟WebrtcIP | FBroVip.wsv:465 | 已覆盖 | browser_vip_fingerprint_webrtc `MCP_Server_VIP.wsv:856` | 公网/本地/host/禁用 4 参 |
| 指纹_虚拟Date时区 | FBroVip.wsv:479 | 已覆盖 | browser_vip_fingerprint_timezone `MCP_Server_VIP.wsv:867` | offset_h/m+name+iana |
| 指纹_虚拟Viewport | FBroVip.wsv:491 | 已覆盖 | browser_vip_fingerprint_viewport `MCP_Server_VIP.wsv:988` | 调用点注明"第三参是Height"（`MCP_Server_VIP.wsv:994`） |
| 指纹_启用触摸事件 | FBroVip.wsv:500 | 已覆盖 | browser_fingerprint_touch_enable `MCP_Server_VIP.wsv:759` / browser_vip_touch_emulation `:1686` | 内核级触摸仿真开关 |
| 指纹_虚拟内核功能 | FBroVip.wsv:508 | N/A | — | 类库自标"**弃用**"，且**无 `<公开>`**（非公开方法）；等价能力=`内核开关_设置CSS/Web/V8内核`（`MCP_Server_VIP.wsv:1219/1248/1277`） |
| 指纹_设置SSL加密套件 | FBroVip.wsv:517 | 已覆盖 | browser_vip_fingerprint_ssl `MCP_Server_VIP.wsv:908` | TLS 版本枚举经 `MCP_Server_Utils.wsv:47-59` 映射 |
| 指纹_虚拟BatteryManagerCharging | FBroVip.wsv:529 | 已覆盖 | browser_vip_fingerprint_battery `MCP_Server_VIP.wsv:1040` | 同工具 charging |
| 指纹_虚拟BatteryManagerChargingTime | FBroVip.wsv:535 | 已覆盖 | browser_vip_fingerprint_battery `MCP_Server_VIP.wsv:1040` | 同工具 charging_time |
| 指纹_虚拟BatteryManagerDischargingTime | FBroVip.wsv:543 | 已覆盖 | browser_vip_fingerprint_battery `MCP_Server_VIP.wsv:1040` | 同工具 discharging_time |
| 指纹_虚拟BatteryManagerLevel | FBroVip.wsv:551 | 已覆盖 | browser_vip_fingerprint_battery `MCP_Server_VIP.wsv:1040` | 同工具 level |
| 指纹_虚拟AudioInput设备 | FBroVip.wsv:557 | 已覆盖 | browser_vip_fingerprint_media_devices `MCP_Server_VIP.wsv:1054` | target=audio_input；工具强化了 type/devices 校验 |
| 指纹_虚拟VideoInput设备 | FBroVip.wsv:569 | 已覆盖 | browser_vip_fingerprint_media_devices `MCP_Server_VIP.wsv:1054` | target=video_input |
| 指纹_虚拟AudioOutput设备 | FBroVip.wsv:581 | 已覆盖 | browser_vip_fingerprint_media_devices `MCP_Server_VIP.wsv:1054` | target=audio_output |
| 指纹_虚拟定位 | FBroVip.wsv:595 | 已覆盖 | browser_vip_fingerprint_geolocation `MCP_Server_VIP.wsv:878` | 调用点补默认值 `MCP_Server_Core.wsv:2441` |
| 指纹_虚拟屏幕方向 | FBroVip.wsv:609 | 已覆盖 | browser_vip_orientation `MCP_Server_VIP.wsv:1801` | — |
| WebSocket_启用拦截 | FBroVip.wsv:617 | 已覆盖 | browser_vip_websocket_intercept `MCP_Server_VIP.wsv:12` | 渲染侧事件由 `main.wsv:824-898` 覆盖并写 `app_render_ws_*` |
| 高级_设置触发鼠标触摸事件 | FBroVip.wsv:623 | 等价覆盖 | browser_vip_touch_emulation（mode=mouse）`MCP_Server_VIP.wsv:1686` | 该分支走 **CDP `Emulation.setEmitTouchEventsForMouse`**（不需刷新、不破 CDP）；类库内核级路径由 `指纹_启用触摸事件`（`MCP_Server_VIP.wsv:1732`）承担 |
| 高级_设置代理 | FBroVip.wsv:630 | 已覆盖 | browser_set_s5_proxy `MCP_Server_VIP.wsv:44` / browser_set_proxy `MCP_Server_Core.wsv:1484` | 调用点 `MCP_Server_VIP.wsv:60`、`MCP_Server_Core.wsv:1503` |
| 高级_清空代理 | FBroVip.wsv:644 | 已覆盖 | browser_vip_clear_s5_proxy `MCP_Server_VIP.wsv:167` / browser_clear_proxy `MCP_Server_Core.wsv:1525` | — |
| 开发者消息_发送消息 | FBroVip.wsv:651 | 已覆盖 | browser_vip_send_devtools_msg `MCP_Server_VIP.wsv:1306` | 调用点 `MCP_Server_VIP.wsv:1326` |
| 开发者消息_执行方法 | FBroVip.wsv:682 | 已覆盖 | browser_cdp_call `MCP_Server_Core.wsv:4870` | 经 `执行CDP命令`（`MCP_Server.wsv:1867`）→ `vip_ctrl.开发者消息_执行方法`（`MCP_Server.wsv:1796`）；注意 `MCP_Server.wsv:1762` 注释指出该方法**不自检观察者**，故必须先 `确保CDP观察者已注册`（`:1926`） |
| 开发者消息_启用监管者事件 | FBroVip.wsv:697 | 已覆盖 | browser_vip_enable_devtools_observer `MCP_Server_VIP.wsv:1629` / browser_vip_enable_inspector `:184` | 两工具均路由到 `确保CDP观察者已注册`（`MCP_Server.wsv:1926`，内部调用点 `:1948`） |
| 开发者消息_关闭监管者事件 | FBroVip.wsv:710 | 已覆盖 | 同上两工具 enable=false 路径 `MCP_Server_VIP.wsv:1677-1681` / `:238-243` | 路由到 `注销CDP观察者`（`MCP_Server.wsv:1966`，调用点 `:1988`）；工具文案注明"下一次 CDP 调用会自动重新注册、通常无需重启" |
| 高级_网页截图 | FBroVip.wsv:717 | 已覆盖 | browser_screenshot `MCP_Server_Core.wsv:2764` | 调用点 `MCP_Server_Core.wsv:2822`，走 `类_MCP_截图异步回调`（`MCP_Callbacks.wsv:390`） |
| 高级_启用执行环境 | FBroVip.wsv:738 | 已覆盖 | browser_vip_enable_js_env `MCP_Server_VIP.wsv:250` | 调用点 `MCP_Server_VIP.wsv:271`；工具已加 confirm 语义 |
| 高级_取当前环境ID清单 | FBroVip.wsv:745 | 已覆盖 | browser_vip_get_js_env_ids `MCP_Server_VIP.wsv:285` | 调用点 `MCP_Server_VIP.wsv:296` |
| 高级_执行JS | FBroVip.wsv:753 | 已覆盖 | browser_vip_execute_js_context（缺省 target=按 context_id）`MCP_Server_VIP.wsv:1493`（调用点 `:1556`）/ browser_execute_js（CDP）`MCP_Server_Core.wsv:285` | 不需要 VIP 环境时项目推荐 CDP 路线 |
| 高级_执行JS_框架ID | FBroVip.wsv:777 | 已覆盖 | browser_vip_execute_js_context frame_id `MCP_Server_VIP.wsv:1493`（调用点 `:1552`） | 框架ID 由 `browser_vip_get_js_env_ids` 给出 |
| 高级_执行JS_主框架 | FBroVip.wsv:800 | 已覆盖 | browser_vip_execute_js_context target=main `MCP_Server_VIP.wsv:1493`（调用点 `:1538`） | — |
| 高级_执行JS_全部框架 | FBroVip.wsv:821 | 已覆盖 | browser_vip_execute_js_context target=all_frames `MCP_Server_VIP.wsv:1493`（调用点 `:1530`） | 回包为逐帧累计（工具描述已注明） |
| 高级_执行JS_框架序号 | FBroVip.wsv:843 | 已覆盖 | browser_vip_execute_js_context target=frame_index `MCP_Server_VIP.wsv:1493`（调用点 `:1547`） | 序号语义以类库注释为准（与 DevTools 序号不一定一致） |
| 高级_发送触摸事件 | FBroVip.wsv:866 | 等价覆盖 | browser_touch_press/release/move `MCP_Server_Core.wsv:6397/6430/6463` + browser_vip_touch_cancel `MCP_Server_VIP.wsv:321` | MCP 无"原始 type+触摸点数组+修饰符"一次下发入口；按 type 拆成三工具。**参数面更窄**（无多触点数组/修饰符） |
| 高级触摸_按下 | FBroVip.wsv:876 | 已覆盖 | browser_touch_press（kernel:true）`MCP_Server_Core.wsv:6397` | 默认走 CDP（`:6407-6413`），显式 `kernel:true` 才调用 `vip.高级触摸_按下`（`:6423`）；工具文案含 CDP 失效警告 |
| 高级触摸_放开 | FBroVip.wsv:887 | 已覆盖 | browser_touch_release（kernel:true）`MCP_Server_Core.wsv:6430` | 调用点 `:6456` |
| 高级触摸_移动 | FBroVip.wsv:898 | 已覆盖 | browser_touch_move（kernel:true）`MCP_Server_Core.wsv:6463` | 调用点 `:6489` |
| 高级触摸_取消 | FBroVip.wsv:909 | 已覆盖 | browser_vip_touch_cancel `MCP_Server_VIP.wsv:321` | 调用点 `:331` |
| 高级触摸_单击 | FBroVip.wsv:920 | 等价覆盖 | browser_touch_press + browser_touch_release `MCP_Server_Core.wsv:6397/6430` | 类库多"单击延时"参数（默认 50ms），MCP 无对应；功能等价 |
| 高级_发送键盘事件 | FBroVip.wsv:932 | 等价覆盖 | browser_key_event（CDP）`MCP_Server_Core.wsv:1008` + browser_vip_key_input/type `MCP_Server_VIP.wsv:1167/1195` | 类库支持的 keyIdentifier/code/isSystemKey/nativeVirtualKeyCode 等细粒度字段未逐一暴露 |
| 高级键盘_按下 | FBroVip.wsv:969 | 已覆盖 | browser_vip_key_press `MCP_Server_VIP.wsv:120` | 调用点 `:136` |
| 高级键盘_放开 | FBroVip.wsv:978 | 已覆盖 | browser_vip_key_release `MCP_Server_VIP.wsv:143` | 调用点 `:159` |
| 高级键盘_单击 | FBroVip.wsv:987 | 已覆盖 | browser_vip_key_click `MCP_Server_VIP.wsv:1144` | 调用点 `:1160` |
| 高级键盘_输入字符 | FBroVip.wsv:999 | 已覆盖 | browser_vip_key_input `MCP_Server_VIP.wsv:1167` | 调用点 `:1188` |
| 逐字分割 | FBroVip.wsv:1006 | N/A | — | 无 `<公开>`，私有辅助方法 |
| 高级键盘_输入文本 | FBroVip.wsv:1015 | 已覆盖 | browser_vip_key_type `MCP_Server_VIP.wsv:1195` | 调用点 `:1211` |
| 高级_发送鼠标事件 | FBroVip.wsv:1032 | 等价覆盖 | browser_mouse_click/move/wheel（CDP）`MCP_Server_Core.wsv:892/966/1415` + browser_vip_mouse_* `MCP_Server_VIP.wsv:68/98/795/812/829` | 同上：原始全参入口未暴露（clickCount/pointerType/timestamp 等） |
| 高级鼠标_按下 | FBroVip.wsv:1062 | 已覆盖 | browser_vip_mouse_press `MCP_Server_VIP.wsv:795` | 调用点 `:805`；工具文案已标注 **CDP 通道会失效** |
| 高级鼠标_放开 | FBroVip.wsv:1084 | 已覆盖 | browser_vip_mouse_release `MCP_Server_VIP.wsv:812` | 调用点 `:822` |
| 高级鼠标_移动 | FBroVip.wsv:1106 | 已覆盖 | browser_vip_mouse_move `MCP_Server_VIP.wsv:98` | 调用点 `:113` |
| 高级鼠标_滚轮滚动 | FBroVip.wsv:1113 | 已覆盖 | browser_vip_mouse_wheel `MCP_Server_VIP.wsv:829` | 调用点 `:848` |
| 高级鼠标_单击 | FBroVip.wsv:1122 | 已覆盖 | browser_vip_mouse_click `MCP_Server_VIP.wsv:68` | 调用点 `:91`；同样带 CDP 失效警告 |
| 过滤器_修改内容 | FBroVip.wsv:1134 | 等价覆盖 | browser_intercept `MCP_Server_Core.wsv:2563`（action=modify，注册 `MCP_Server.wsv:11056`） | 走**手写 ResponseFilter 通道**：`浏览器_获取资源过滤器`（`MCP_BrowserEvents.wsv:366`）→ `类_MCP_篡改过滤器`（`MCP_Callbacks.wsv:1085`）。源码注释明写"手写资源篡改: … **不依赖VIP官方过滤器**"（`MCP_BrowserEvents.wsv:390`）。差异：VIP 版支持"响应协议头替换 + 全局作用域"，手写通道只改 body |
| 过滤器_取消修改内容 | FBroVip.wsv:1147 | 等价覆盖 | browser_intercept action=unmodify/clear `MCP_Server_Core.wsv:2563` | 工具描述："unmodify(按url撤销资源替换规则…幂等成功)…注: clear 与 un* 只作用于手写过滤器通道, 不含 VIP 过滤器" |
| 过滤器_取消全部修改内容 | FBroVip.wsv:1155 | 已覆盖 | browser_intercept action=clear `MCP_Server_Core.wsv:2563`；维护路径 `清理VIP拦截资源` `MCP_Server.wsv:9865`（调用点 `:9879`） | VIP 通道的"全清"在关闭/维护时由 `清理VIP拦截资源` 调用（`:9942` 触发） |
| 过滤器_替换资源_数据 | FBroVip.wsv:1162 | 等价覆盖 | browser_intercept action=replace_data `MCP_Server_Core.wsv:2563` | 手写篡改过滤器 `待输出文本`（`MCP_BrowserEvents.wsv:448`）；MIME/响应头参数无对应入口 |
| 过滤器_替换资源_文件 | FBroVip.wsv:1174 | 等价覆盖 | browser_intercept action=replace_file `MCP_Server_Core.wsv:2563` | `MCP_BrowserEvents.wsv:466-509` 含路径越界/文件不存在的显式拒绝 |
| 过滤器_取消替换资源 | FBroVip.wsv:1186 | 等价覆盖 | browser_intercept action=unreplace `MCP_Server_Core.wsv:2563` | 只撤销 replace_file 类规则 |
| 过滤器_取消全部替换资源 | FBroVip.wsv:1194 | 已覆盖 | 维护路径 `清理VIP拦截资源` `MCP_Server.wsv:9865`（调用点 `:9880`） | 同上；对代理不可见的内部清理 |
| 高级_创建标签浏览器 | FBroVip.wsv:1201 | **真缺口** | browser_create_tab `MCP_Server_System.wsv:16`（工具**刻意拒实现**） | 见 §5.2 缺口 1 |
| 内核开关_禁用ConsoleDebug | FBroVip.wsv:1219 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（调用点 `:1881`） | 单工具多布尔开关 |
| 内核开关_禁用ConsoleWarn | FBroVip.wsv:1226 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1879`） | — |
| 内核开关_禁用ConsoleError | FBroVip.wsv:1232 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1880`） | — |
| 内核开关_禁用ConsoleInfo | FBroVip.wsv:1239 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1882`） | — |
| 内核开关_禁用ConsoleLog | FBroVip.wsv:1246 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1878`） | — |
| 内核开关_禁用ConsoleAssert | FBroVip.wsv:1253 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1885`） | — |
| 内核开关_禁用ConsoleDir | FBroVip.wsv:1260 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1886`） | — |
| 内核开关_禁用ConsoleTable | FBroVip.wsv:1267 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1887`） | — |
| 内核开关_禁用ConsoleGroup | FBroVip.wsv:1275 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1890`） | — |
| 内核开关_禁用ConsoleTime | FBroVip.wsv:1282 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1888`） | — |
| 内核开关_禁用ConsoleProfile | FBroVip.wsv:1290 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1891`） | — |
| 内核开关_禁用ConsoleCount | FBroVip.wsv:1297 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1889`） | — |
| 内核开关_禁用ConsoleTrace | FBroVip.wsv:1304 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1883`） | — |
| 内核开关_禁用ConsoleClear | FBroVip.wsv:1312 | 已覆盖 | browser_vip_disable_console `MCP_Server_VIP.wsv:1868`（`:1884`） | — |
| 内核开关_禁用Performance检测 | FBroVip.wsv:1319 | 已覆盖 | browser_vip_disable_console（performance 字段）`MCP_Server_VIP.wsv:1868`（调用点 `:1911`） | 含 performance_min_ms/performance_max_ms |
| 内核开关_设置CSS内核 | FBroVip.wsv:1329 | 已覆盖 | browser_vip_set_css_version `MCP_Server_VIP.wsv:1219` | 调用点 `:1241` |
| 内核开关_设置Web内核 | FBroVip.wsv:1336 | 已覆盖 | browser_vip_set_web_version `MCP_Server_VIP.wsv:1248` | 调用点 `:1270` |
| 内核开关_设置V8内核 | FBroVip.wsv:1342 | 已覆盖 | browser_vip_set_v8_version `MCP_Server_VIP.wsv:1277` | 调用点 `:1299` |
| 内核开关_禁用Debugger | FBroVip.wsv:1348 | 已覆盖 | browser_vip_disable_debugger `MCP_Server_VIP.wsv:339` | 调用点 `:349`；注意 `MCP_Server.wsv:1909/2205` 的自愈逻辑（与 CDP 观察者冲突，创建浏览器时统一恢复） |
| 内核开关_设置EventIsTrusted | FBroVip.wsv:1354 | 已覆盖 | browser_vip_set_is_trusted `MCP_Server_VIP.wsv:1919` | 调用点 `:1930` |

**§1 计数**：已覆盖 101 / 等价覆盖 11 / 真缺口 1 / N/A 4 = 117。

---

## 2. `FBroEventControl.wsv` 事件/回调类逐条核对（166 行）

来源列中：
- `BE:` = `MCP_BrowserEvents.wsv`（浏览器事件覆盖类，90 个覆盖，L71–L3530）
- `MAIN:` = `main.wsv`（应用事件覆盖类 `类_MCP_初始化事件`，L302 起）
- 记录行 `REC:` 指 `记录监控事件 (...)` 或其事件类型字符串的所在行；查询工具统一为 **browser_event**（分派 `MCP_Server_Core.wsv:4887`，注册 `MCP_Server.wsv:11282`）。

### 2.1 `类_FBrowser_应用事件`（L5–L431，32 方法）

> ⚠ **总前提（本仓库自述 + 既定事实）**：`main.wsv:944-955` 注释明确写："实测(报告 141 节): 本机 app_* 族(含 app_render_*/app_v8_*/app_startup_*)不会入库 —— 渲染进程是 SDK 自带的 FBroSubprocess.exe, 事件不派发到本项目的事件覆盖上…此处保留接线仅为「若将来换构建即可生效」, 请勿据此承诺事件可用。"
> `browser_event` 的 app_ 分支也内置了同口径的诚实告知（`MCP_Server_Core.wsv:4929-4939`）。
> 因此下表的"已覆盖"含义是**接线+入库代码已就位**，**不代表本机构建下会产生记录**。

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:7 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:13 | N/A | — | SDK 内部生命周期 |
| 请求环境初始化完毕 | FBroEventControl.wsv:232 | 已覆盖 | browser_event event_type=app_startup_request_context_ready `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:495，记录 MAIN:502（开关 `是否监控启动流程`，`MCP_Server.wsv:337-388` 族表） |
| 扩展插件_创建成功 | FBroEventControl.wsv:240 | 已覆盖 | browser_event event_type=app_extension_created `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:764，记录 MAIN:775 |
| 扩展插件_创建失败 | FBroEventControl.wsv:247 | 已覆盖 | browser_event event_type=app_extension_create_failed `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:778，记录 MAIN:793 |
| 扩展插件_载入成功 | FBroEventControl.wsv:256 | 已覆盖 | browser_event event_type=app_extension_loaded `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:796，记录 MAIN:807 |
| 扩展插件_卸载成功 | FBroEventControl.wsv:263 | 已覆盖 | browser_event event_type=app_extension_unloaded `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:810，记录 MAIN:821 |
| 获取默认事件 | FBroEventControl.wsv:272 | N/A | — | 覆盖 MAIN:956 的作用是给"内置/谷歌模式的内部浏览器"装本项目事件类（`用户额外配置.置事件`，MAIN:965-967），属内部接线钩子，不可查询也不应暴露 |
| 执行关闭完毕 | FBroEventControl.wsv:282 | N/A | — | 覆盖 MAIN:341 仅设"结束程序=真"，进程退出路径，非可查询事件 |
| 即将处理命令行 | FBroEventControl.wsv:290 | 已覆盖 | browser_event event_type=app_startup_cmdline `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:505，记录 MAIN:646 |
| 注册自定义方案 | FBroEventControl.wsv:294 | N/A | — | 覆盖 MAIN:367 注册 `mcp` 方案（CEF 要求初始化前声明）；等价能力=`browser_kernel_scheme`（`MCP_Kernel.wsv:80`）——见 §5.3 误报 ⑯ |
| 浏览器_初始化完毕 | FBroEventControl.wsv:297 | N/A | — | 覆盖 MAIN:315 是 **MCP 自举入口**（启动服务器/写环境变量/触发首浏览器），非事件查询项 |
| 浏览器_即将启动子进程 | FBroEventControl.wsv:299 | 已覆盖 | browser_event event_type=app_startup_child_process `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:649，记录 MAIN:656 |
| 浏览器_即将启动消息调度 | FBroEventControl.wsv:302 | 已覆盖 | browser_event event_type=app_startup_message_pump `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:659，记录 MAIN:669 |
| 渲染_即将初始化WebKit | FBroEventControl.wsv:305 | 已覆盖 | browser_event event_type=app_startup_webkit_init `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:672，记录 MAIN:678 |
| 渲染_浏览器创建 | FBroEventControl.wsv:307 | 已覆盖 | browser_event event_type=app_render_browser_created `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:446，记录 MAIN:453 |
| 渲染_即将销毁浏览器 | FBroEventControl.wsv:311 | 已覆盖 | browser_event event_type=app_render_browser_destroyed `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:456，记录 MAIN:462 |
| 渲染_即将创建V8环境 | FBroEventControl.wsv:314 | 已覆盖 | browser_event event_type=app_render_v8_context_created `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:681，记录 MAIN:690（另 MAIN:691 写"渲染侧"旁路） |
| 渲染_即将释放V8环境 | FBroEventControl.wsv:319 | 已覆盖 | browser_event event_type=app_v8_released `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:418，记录 MAIN:427 |
| 渲染_即将捕获异常 | FBroEventControl.wsv:324 | 已覆盖 | browser_event event_type=app_v8_exception `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:348，记录 MAIN:363（含 message/url/stack） |
| 渲染_焦点节点改变 | FBroEventControl.wsv:331 | 已覆盖 | browser_event event_type=app_dom_focus_changed `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:377，记录 MAIN:415；MAIN:386-401 带 300ms 节流（持 `事件节流锁`） |
| 渲染_收到消息 | FBroEventControl.wsv:336 | 已覆盖 | browser_event event_type=app_render_message_received `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:694，记录 MAIN:707 |
| 渲染_载入状态被改变 | FBroEventControl.wsv:345 | 已覆盖 | browser_event event_type=app_render_loading_state `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:713，记录 MAIN:728 |
| 渲染_载入开始 | FBroEventControl.wsv:351 | 已覆盖 | browser_event event_type=app_render_load_start `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:732，记录 MAIN:744 |
| 渲染_载入结束 | FBroEventControl.wsv:356 | 已覆盖 | browser_event event_type=app_render_load_end `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:748，记录 MAIN:760 |
| 渲染_载入错误 | FBroEventControl.wsv:361 | 已覆盖 | browser_event event_type=app_render_load_error `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:430，记录 MAIN:443 |
| 进程间消息_收到主进程消息 | FBroEventControl.wsv:371 | N/A | — | 覆盖 MAIN:471 **只在渲染进程执行**；主进程侧对应物是 `进程间消息_收到渲染进程消息`（BE:2645，已入库）与 `browser_kernel_ipc_queue`（`MCP_Kernel.wsv:88`） |
| 渲染_VIP_WebSocket客户端_创建 | FBroEventControl.wsv:380 | 已覆盖 | browser_event event_type=app_render_ws_created `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:824，记录 MAIN:833 |
| 渲染_VIP_WebSocket客户端_关闭 | FBroEventControl.wsv:388 | 已覆盖 | browser_event event_type=app_render_ws_closed `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:837，记录 MAIN:846 |
| 渲染_VIP_WebSocket客户端_连接服务器 | FBroEventControl.wsv:398 | 已覆盖 | browser_event event_type=app_render_ws_connect `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:850，记录 MAIN:865 |
| 渲染_VIP_WebSocket客户端_接收数据 | FBroEventControl.wsv:408 | 已覆盖 | browser_event event_type=app_render_ws_recv `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:869，记录 MAIN:880 |
| 渲染_VIP_WebSocket客户端_发送数据 | FBroEventControl.wsv:420 | 已覆盖 | browser_event event_type=app_render_ws_send `MCP_Server_Core.wsv:4887` | 覆盖 MAIN:886，记录 MAIN:897 |

**§2.1 计数**：已覆盖 25 / 等价覆盖 0 / 真缺口 0 / N/A 7 = 32。

### 2.2 `类_FBrowser_浏览器事件`（L434–L1762，90 方法）—— 本项目事件流的主体

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:436 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:442 | N/A | — | SDK 内部生命周期 |
| 浏览器_收到消息 | FBroEventControl.wsv:563 | 等价覆盖 | browser_kernel_ipc_queue `MCP_Kernel.wsv:88` / browser_cdp_call `MCP_Server_Core.wsv:4870` | 覆盖 BE:2695 用于本项目自定义 IPC 通道读写，**事件本体未入库**；CEF 进程消息语义在 MCP 侧由注入队列/ CDP 承担 |
| 浏览器_即将导航 | FBroEventControl.wsv:581 | 已覆盖 | browser_event event_type=navigate `MCP_Server_Core.wsv:4887` | 覆盖 BE:1219，记录 BE:1251；同时承担 `是否Hook导航` 拦截（BE:105） |
| 浏览器_从标签打开地址 | FBroEventControl.wsv:600 | 已覆盖 | browser_event event_type=open_url_from_tab `MCP_Server_Core.wsv:4887` | 覆盖 BE:2936，记录 BE:2950 |
| 浏览器_请求证书错误 | FBroEventControl.wsv:621 | 等价覆盖 | browser_kernel_cert（action=list/ignore）`MCP_Kernel.wsv:60`（注册 `MCP_Server.wsv:11128`） | 覆盖 BE:2547 做放行判定但**未入库**；证书错误清单/忽略开关由内核工具提供 |
| 浏览器_选择客户端证书 | FBroEventControl.wsv:641 | 已覆盖 | browser_event event_type=client_cert_selected `MCP_Server_Core.wsv:4887` | 覆盖 BE:3102，记录 BE:3117 |
| 浏览器_渲染视图 | FBroEventControl.wsv:658 | 已覆盖 | browser_event event_type=render_view_ready `MCP_Server_Core.wsv:4887` | 覆盖 BE:3026，记录 BE:3031 |
| 浏览器_渲染意外终止 | FBroEventControl.wsv:668 | 已覆盖 | browser_event event_type=crash `MCP_Server_Core.wsv:4887` | 覆盖 BE:1017，记录 BE:1069（`记录加载事件("crash")`）；查询时跨浏览器ID（`MCP_Server_Core.wsv:4951-4954`） |
| 浏览器_获得需授权证书 | FBroEventControl.wsv:682 | 等价覆盖 | browser_set_proxy（用户名/密码）`MCP_Server_Core.wsv:1484` | 覆盖 BE:2589 **未入库**；代理认证凭据改由工具参数下发 |
| 浏览器_创建完毕 | FBroEventControl.wsv:700 | 已覆盖 | browser_event event_type=browser_created `MCP_Server_Core.wsv:4887` | 覆盖 BE:71，记录 BE:173；**该覆盖同时是自动注册 CDP 观察者的入口**（BE:97 `确保CDP观察者已注册`） |
| 浏览器_即将打开新窗口 | FBroEventControl.wsv:721 | 已覆盖 | browser_event event_type=popup `MCP_Server_Core.wsv:4887` | 覆盖 BE:1405，记录 BE:1521 |
| 浏览器_打开新窗口失败 | FBroEventControl.wsv:742 | 已覆盖 | browser_event event_type=popup_failed `MCP_Server_Core.wsv:4887` | 覆盖 BE:1569，记录 BE:1583 |
| 浏览器_即将打开开发者窗口 | FBroEventControl.wsv:763 | 已覆盖 | browser_event event_type=devtools_popup `MCP_Server_Core.wsv:4887` | 覆盖 BE:1537，记录 BE:1563 |
| 浏览器_执行关闭 | FBroEventControl.wsv:780 | 已覆盖 | browser_event event_type=do_close `MCP_Server_Core.wsv:4887` | 覆盖 BE:2523，记录 BE:2529 |
| 浏览器_即将关闭 | FBroEventControl.wsv:789 | 已覆盖 | browser_event event_type=browser_closing `MCP_Server_Core.wsv:4887` | 覆盖 BE:215，记录 BE:227；该覆盖同时清理 VIP 开发者消息（BE:283） |
| 浏览器_地址被改变 | FBroEventControl.wsv:799 | 已覆盖 | browser_event event_type=url_changed `MCP_Server_Core.wsv:4887` | 覆盖 BE:965，记录 BE:1001（同值去重，BE:979） |
| 浏览器_标题被改变 | FBroEventControl.wsv:811 | 已覆盖 | browser_event event_type=title_changed `MCP_Server_Core.wsv:4887` | 覆盖 BE:1773，记录 BE:1795（直接 `记录浏览器事件`） |
| 浏览器_网页图标被改变 | FBroEventControl.wsv:822 | 已覆盖 | browser_event event_type=favicon `MCP_Server_Core.wsv:4887` | 覆盖 BE:2205，记录 BE:2241 |
| 浏览器_全屏模式被改变 | FBroEventControl.wsv:831 | 已覆盖 | browser_event event_type=fullscreen `MCP_Server_Core.wsv:4887` | 覆盖 BE:2179，记录 BE:2197 |
| 浏览器_工具栏被改变 | FBroEventControl.wsv:839 | 已覆盖 | browser_event event_type=tooltip `MCP_Server_Core.wsv:4887` | 覆盖 BE:2980，记录 BE:2986 |
| 浏览器_状态栏被改变 | FBroEventControl.wsv:850 | 已覆盖 | browser_event event_type=status_message `MCP_Server_Core.wsv:4887` | 覆盖 BE:1623，记录 BE:1641 |
| 浏览器_控制台消息 | FBroEventControl.wsv:861 | 已覆盖 | browser_collect action=console_get `MCP_Server_Core.wsv:3704` | 覆盖 BE:187 走 `记录控制台消息`（log_type=console，`MCP_Server.wsv:8148`），非 browser_event 通道 |
| 浏览器_自动调整尺寸 | FBroEventControl.wsv:875 | 已覆盖 | browser_event event_type=auto_resize `MCP_Server_Core.wsv:4887` | 覆盖 BE:3009，记录 BE:3020 |
| 浏览器_加载进度被改变 | FBroEventControl.wsv:888 | 已覆盖 | browser_event event_type=load_progress `MCP_Server_Core.wsv:4887` | 覆盖 BE:2489，记录 BE:2513 |
| 浏览器_光标被改变 | FBroEventControl.wsv:901 | 已覆盖 | browser_event event_type=cursor_changed `MCP_Server_Core.wsv:4887` | 覆盖 BE:2992，记录 BE:3003 |
| 浏览器_即将改变媒体访问 | FBroEventControl.wsv:915 | 已覆盖 | browser_event event_type=media_access_change `MCP_Server_Core.wsv:4887` | 覆盖 BE:3185，记录 BE:3207 |
| 浏览器_即将加载资源 | FBroEventControl.wsv:931 | 已覆盖 | browser_event event_type=resource_request `MCP_Server_Core.wsv:4887` | 覆盖 BE:1807，记录 BE:1841；同时是资源替换/篡改/缓存的 Hook 点（BE:113/390/569） |
| 浏览器_获取资源处理器 | FBroEventControl.wsv:951 | 等价覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖 BE:318 用于装方案资源处理器（`类_MCP_方案资源处理器` `MCP_Kernel.wsv:1859`）；属注册回调机制，非事件流 |
| 浏览器_重定向资源 | FBroEventControl.wsv:968 | 已覆盖 | browser_event event_type=resource_redirect `MCP_Server_Core.wsv:4887` | 覆盖 BE:1887，记录 BE:1915 |
| 浏览器_响应资源 | FBroEventControl.wsv:983 | 已覆盖 | browser_event event_type=resource_response `MCP_Server_Core.wsv:4887` | 覆盖 BE:1851，记录 BE:1877 |
| 浏览器_获取资源过滤器 | FBroEventControl.wsv:1003 | 等价覆盖 | browser_intercept `MCP_Server_Core.wsv:2563` / browser_inject `MCP_Server_Core.wsv:3228` | 覆盖 BE:366 按规则挂 `类_MCP_篡改过滤器`（`MCP_Callbacks.wsv:1085`）或 `类_MCP_缓存过滤器`（`:1010`） |
| 浏览器_资源加载完毕 | FBroEventControl.wsv:1018 | 等价覆盖 | browser_network `MCP_Server_Core.wsv:3316` / browser_network_body `:5032` | 覆盖 BE:587 **未入库**；资源完成事实由网络日志（log_type=network/network_detail）覆盖 |
| 浏览器_处理协议请求 | FBroEventControl.wsv:1038 | 已覆盖 | browser_event event_type=protocol_execution `MCP_Server_Core.wsv:4887` | 覆盖 BE:2956，记录 BE:2967 |
| 浏览器_载入状态被改变 | FBroEventControl.wsv:1050 | 已覆盖 | browser_event event_type=loading_state_change `MCP_Server_Core.wsv:4887` | 覆盖 BE:1589，记录 BE:1615 |
| 浏览器_载入开始 | FBroEventControl.wsv:1061 | 已覆盖 | browser_event event_type=load_start `MCP_Server_Core.wsv:4887` | 覆盖 BE:1659，记录 BE:1691 |
| 浏览器_载入结束 | FBroEventControl.wsv:1071 | 已覆盖 | browser_event event_type=load_end `MCP_Server_Core.wsv:4887` | 覆盖 BE:907，记录 BE:929（`记录加载事件`，含 status_code）；并驱动等待任务（BE:953） |
| 浏览器_载入错误 | FBroEventControl.wsv:1080 | 已覆盖 | browser_event event_type=load_error `MCP_Server_Core.wsv:4887` | 覆盖 BE:1703，记录 BE:1761 |
| 浏览器_即将打开菜单 | FBroEventControl.wsv:1090 | 已覆盖 | browser_event event_type=context_menu_opening `MCP_Server_Core.wsv:4887` | 覆盖 BE:2842，记录 BE:2852（`构建菜单环境摘要`） |
| 浏览器_菜单被调用 | FBroEventControl.wsv:1109 | 已覆盖 | browser_event event_type=context_menu_run `MCP_Server_Core.wsv:4887` | 覆盖 BE:2862，记录 BE:2871 |
| 浏览器_菜单被点击 | FBroEventControl.wsv:1127 | 已覆盖 | browser_event event_type=context_menu_command `MCP_Server_Core.wsv:4887` | 覆盖 BE:2877，记录 BE:2892 |
| 浏览器_菜单被关闭 | FBroEventControl.wsv:1142 | 已覆盖 | browser_event event_type=context_menu_dismissed `MCP_Server_Core.wsv:4887` | 覆盖 BE:2898，记录 BE:2904 |
| 浏览器_即将运行快捷菜单 | FBroEventControl.wsv:1153 | 已覆盖 | browser_event event_type=quick_menu_* `MCP_Server_Core.wsv:4887` | 覆盖 BE:2735（**本体未入库**）；快捷菜单的 command/dismiss 已入库（BE:2920/2932） |
| 浏览器_即将运行快捷菜单命令 | FBroEventControl.wsv:1169 | 已覆盖 | browser_event event_type=quick_menu_command `MCP_Server_Core.wsv:4887` | 覆盖 BE:2908，记录 BE:2920 |
| 浏览器_即将取消快捷菜单 | FBroEventControl.wsv:1183 | 已覆盖 | browser_event event_type=quick_menu_dismissed `MCP_Server_Core.wsv:4887` | 覆盖 BE:2926，记录 BE:2932 |
| 浏览器_可下载 | FBroEventControl.wsv:1193 | 已覆盖 | browser_event event_type=download_request `MCP_Server_Core.wsv:4887` | 覆盖 BE:2381，记录 BE:2403 |
| 浏览器_即将下载 | FBroEventControl.wsv:1209 | 已覆盖 | browser_event event_type=download_start `MCP_Server_Core.wsv:4887` | 覆盖 BE:633，记录 BE:707/719（含 start_error 分支 BE:687） |
| 浏览器_正在下载 | FBroEventControl.wsv:1225 | 已覆盖 | browser_event event_type=download_progress `MCP_Server_Core.wsv:4887` | 覆盖 BE:735，记录 BE:779；终态类型 BE:857；下载控制另见 browser_kernel_download `MCP_Kernel.wsv:72` |
| 浏览器_按下某键 | FBroEventControl.wsv:1237 | 已覆盖 | browser_event event_type=key_press `MCP_Server_Core.wsv:4887` | 覆盖 BE:2417，记录 BE:2441 |
| 浏览器_按下某键后 | FBroEventControl.wsv:1253 | 已覆盖 | browser_event event_type=key_event `MCP_Server_Core.wsv:4887` | 覆盖 BE:3123，记录 BE:3130 |
| 浏览器_即将打开对话框 | FBroEventControl.wsv:1270 | 已覆盖 | browser_event event_type=file_dialog `MCP_Server_Core.wsv:4887` | 覆盖 BE:2131，记录 BE:2165；文件选择另见 browser_file_dialog `MCP_Server_Core.wsv:6995` |
| 浏览器_JS即将打开对话框 | FBroEventControl.wsv:1297 | 已覆盖 | browser_event event_type=js_dialog `MCP_Server_Core.wsv:4887` | 覆盖 BE:2007，记录 BE:2075（直接 `记录浏览器事件`） |
| 浏览器_JS即将打开离开对话框 | FBroEventControl.wsv:1317 | 已覆盖 | browser_event event_type=before_unload `MCP_Server_Core.wsv:4887` | 覆盖 BE:2095，记录 BE:2121 |
| 浏览器_JS重置对话框 | FBroEventControl.wsv:1328 | 已覆盖 | browser_event event_type=js_dialog_reset `MCP_Server_Core.wsv:4887` | 覆盖 BE:3151，记录 BE:3156 |
| 浏览器_JS对话框关闭 | FBroEventControl.wsv:1333 | 已覆盖 | browser_event event_type=js_dialog_closed `MCP_Server_Core.wsv:4887` | 覆盖 BE:3160，记录 BE:3165 |
| 浏览器_即将失去焦点 | FBroEventControl.wsv:1338 | 已覆盖 | browser_event event_type=focus_lost `MCP_Server_Core.wsv:4887` | 覆盖 BE:2451，记录 BE:2463 |
| 浏览器_请求焦点 | FBroEventControl.wsv:1344 | 已覆盖 | browser_event event_type=set_focus `MCP_Server_Core.wsv:4887` | 覆盖 BE:3136，记录 BE:3145 |
| 浏览器_收到焦点 | FBroEventControl.wsv:1353 | 已覆盖 | browser_event event_type=focus_gained `MCP_Server_Core.wsv:4887` | 覆盖 BE:2471，记录 BE:2481 |
| 浏览器_查找返馈 | FBroEventControl.wsv:1362 | 已覆盖 | browser_event event_type=find_result `MCP_Server_Core.wsv:4887` | 覆盖 BE:2249，记录 BE:2281；查找动作 browser_find `MCP_Server_Core.wsv:863` |
| 浏览器_拖拽进入 | FBroEventControl.wsv:1376 | 已覆盖 | browser_event event_type=drag_enter `MCP_Server_Core.wsv:4887` | 覆盖 BE:3039，记录 BE:3081 |
| 浏览器_拖拽区域改变 | FBroEventControl.wsv:1391 | 已覆盖 | browser_event event_type=draggable_regions_changed `MCP_Server_Core.wsv:4887` | 覆盖 BE:3091，记录 BE:3098 |
| 进程间消息_收到渲染进程消息 | FBroEventControl.wsv:1401 | 已覆盖 | browser_event event_type=ipc_from_renderer / ipc_from_renderer_ext `MCP_Server_Core.wsv:4887` | 覆盖 BE:2645，记录 BE:2691/2721；队列读取 browser_kernel_ipc_queue `MCP_Kernel.wsv:88`；发送侧 browser_send_message `MCP_Server_System.wsv:25` |
| 离屏渲染_获取根屏幕矩形 | FBroEventControl.wsv:1420 | 已覆盖 | browser_event event_type=offscreen_get_root_rect `MCP_Server_Core.wsv:4887` | 覆盖 BE:3276，记录 BE:3300；仅 OSR 模式触发（开关说明 `MCP_Server.wsv:386`） |
| 离屏渲染_获取视图矩形 | FBroEventControl.wsv:1437 | 已覆盖 | browser_event event_type=offscreen_get_view_rect `MCP_Server_Core.wsv:4887` | 覆盖 BE:3329，记录 BE:3353 |
| 离屏渲染_获取屏幕点 | FBroEventControl.wsv:1454 | 已覆盖 | browser_event event_type=offscreen_get_screen_point `MCP_Server_Core.wsv:4887` | 覆盖 BE:3310，记录 BE:3323 |
| 离屏渲染_获取窗口信息 | FBroEventControl.wsv:1473 | 已覆盖 | browser_event event_type=offscreen_get_screen_info `MCP_Server_Core.wsv:4887` | 覆盖 BE:3359，记录 BE:3365 |
| 离屏渲染_即将显示弹窗 | FBroEventControl.wsv:1486 | 已覆盖 | browser_event event_type=offscreen_popup_show `MCP_Server_Core.wsv:4887` | 覆盖 BE:3371，记录 BE:3380 |
| 离屏渲染_移动调整弹窗 | FBroEventControl.wsv:1501 | 已覆盖 | browser_event event_type=offscreen_popup_size `MCP_Server_Core.wsv:4887` | 覆盖 BE:3384，记录 BE:3408 |
| 离屏渲染_将被绘制 | FBroEventControl.wsv:1514 | 已覆盖 | browser_event event_type=offscreen_paint `MCP_Server_Core.wsv:4887` | 覆盖 BE:3414，记录 BE:3429 |
| 离屏渲染_将被加速绘制 | FBroEventControl.wsv:1531 | 已覆盖 | browser_event event_type=offscreen_paint_accelerated `MCP_Server_Core.wsv:4887` | 覆盖 BE:3433，记录 BE:3444 |
| 离屏渲染_开始拖拽 | FBroEventControl.wsv:1546 | 已覆盖 | browser_event event_type=offscreen_start_dragging `MCP_Server_Core.wsv:4887` | 覆盖 BE:3448，记录 BE:3462 |
| 离屏渲染_更新拖动光标 | FBroEventControl.wsv:1561 | 已覆盖 | browser_event event_type=offscreen_update_drag_cursor `MCP_Server_Core.wsv:4887` | 覆盖 BE:3468，记录 BE:3477 |
| 离屏渲染_滚动偏移量改变 | FBroEventControl.wsv:1571 | 已覆盖 | browser_event event_type=offscreen_scroll_offset `MCP_Server_Core.wsv:4887` | 覆盖 BE:3481，记录 BE:3492 |
| 离屏渲染_IME范围改变 | FBroEventControl.wsv:1584 | 已覆盖 | browser_event event_type=offscreen_ime_range `MCP_Server_Core.wsv:4887` | 覆盖 BE:3496，记录 BE:3503 |
| 离屏渲染_文本选择改变 | FBroEventControl.wsv:1597 | 已覆盖 | browser_event event_type=offscreen_text_selection `MCP_Server_Core.wsv:4887` | 覆盖 BE:3507，记录 BE:3517 |
| 离屏渲染_虚拟键盘请求 | FBroEventControl.wsv:1609 | 已覆盖 | browser_event event_type=offscreen_virtual_keyboard `MCP_Server_Core.wsv:4887` | 覆盖 BE:3521，记录 BE:3530 |
| 浏览器_即将创建主框架Document | FBroEventControl.wsv:1620 | 已覆盖 | browser_event event_type=main_document_creating `MCP_Server_Core.wsv:4887` | 覆盖 BE:2971，记录 BE:2976 |
| 浏览器_获取音频参数 | FBroEventControl.wsv:1632 | 等价覆盖 | browser_vip_fingerprint_audio `MCP_Server_VIP.wsv:952` / browser_fingerprint action=audio_random `MCP_Server_Core.wsv:2306` | 覆盖 BE:1923 仅用于**音频指纹 Hook**，**未入库**；音频侧能力由指纹工具承担 |
| 浏览器_即将启动音频流 | FBroEventControl.wsv:1645 | 等价覆盖 | browser_vip_fingerprint_audio `MCP_Server_VIP.wsv:952` | 覆盖 BE:2765 为 Hook 内部回调，未入库 |
| 浏览器_收到音频流包 | FBroEventControl.wsv:1654 | 等价覆盖 | browser_vip_fingerprint_audio `MCP_Server_VIP.wsv:952` | 覆盖 BE:2781，未入库（原始 PCM 包不适合入事件日志） |
| 浏览器_即将结束音频流 | FBroEventControl.wsv:1665 | 等价覆盖 | browser_vip_fingerprint_audio `MCP_Server_VIP.wsv:952` | 覆盖 BE:2799，未入库 |
| 浏览器_音频流出现错误 | FBroEventControl.wsv:1673 | 等价覆盖 | browser_vip_fingerprint_audio `MCP_Server_VIP.wsv:952` | 覆盖 BE:2811，未入库 |
| 浏览器_即将执行Chrome命令 | FBroEventControl.wsv:1681 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` / browser_cdp_call `MCP_Server_Core.wsv:4870` | 覆盖 BE:2825（Chrome 命令执行钩子），未入库 |
| 浏览器_即将创建框架 | FBroEventControl.wsv:1693 | 已覆盖 | browser_event event_type=frame_created `MCP_Server_Core.wsv:4887` | 覆盖 BE:2293，记录 BE:2313；默认关（高噪声），需 `browser_collect event_frame_enable`（`MCP_Server_Core.wsv:3704`） |
| 浏览器_即将连接框架 | FBroEventControl.wsv:1701 | 已覆盖 | browser_event event_type=frame_attached `MCP_Server_Core.wsv:4887` | 覆盖 BE:3169，记录 BE:3176 |
| 浏览器_即将拆离框架 | FBroEventControl.wsv:1709 | 已覆盖 | browser_event event_type=frame_detached `MCP_Server_Core.wsv:4887` | 覆盖 BE:2321，记录 BE:2339 |
| 浏览器_即将改变主框架 | FBroEventControl.wsv:1716 | 已覆盖 | browser_event event_type=main_frame_changed `MCP_Server_Core.wsv:4887` | 覆盖 BE:2347，记录 BE:2369 |
| 浏览器_即将请求媒体访问许可 | FBroEventControl.wsv:1725 | 已覆盖 | browser_event event_type=permission_media_request `MCP_Server_Core.wsv:4887` | 覆盖 BE:3213，记录 BE:3227；需 `event_permission_enable` |
| 浏览器_即将显示许可提示 | FBroEventControl.wsv:1740 | 已覆盖 | browser_event event_type=permission_prompt_show `MCP_Server_Core.wsv:4887` | 覆盖 BE:3233，记录 BE:3247 |
| 浏览器_即将关闭许可提示 | FBroEventControl.wsv:1754 | 已覆盖 | browser_event event_type=permission_prompt_close `MCP_Server_Core.wsv:4887` | 覆盖 BE:3252，记录 BE:3263 |

**§2.2 计数**：已覆盖 76 / 等价覆盖 12 / 真缺口 0 / N/A 2 = 90。

### 2.3 `类_FBrowser_JS交互事件`（L1764–L1827，4 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:1766 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:1773 | N/A | — | SDK 内部生命周期 |
| 即将查询 | FBroEventControl.wsv:1790 | 等价覆盖 | browser_reverse_add_binding `MCP_Server_Reverse.wsv:1654`（注册 `MCP_Server.wsv:11315`） | CEF `FBroQueryFunctions` 协议（页面 JS 主动回调原生）在本项目**无注册调用**（全 src 无 `FBrowser_JS交互_注册`），改由 **CDP `Runtime.addBinding`** 提供"页面→原生"推送能力（工具文案：不改 JS 对象、`fn.toString` 查不出，适合防检测）；方向相同（渲染侧→主控），形态是内建函数而非 query/cancel 双函数 |
| 即将取消查询 | FBroEventControl.wsv:1808 | 等价覆盖 | browser_reverse_add_binding `MCP_Server_Reverse.wsv:1654` / browser_kernel_ipc_queue `MCP_Kernel.wsv:88` | 同上；"取消/取回"语义由 `__mcp_ipc_queue` 轮询（`main.wsv:468-490` 注入队列 + MAIN:471 渲染侧接收）承担 |

**§2.3 计数**：已覆盖 0 / 等价覆盖 2 / 真缺口 0 / N/A 2 = 4。
（旁证：仓库 `_audit/remove_js_query_bridge.py` 文件名表明该桥曾实现后被移除——仅作线索，不作为源码行号证据。）

### 2.4 `类_FBrowser_资源处理器`（L1828–L1934，8 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:1830 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:1836 | N/A | — | SDK 内部生命周期 |
| 打开 | FBroEventControl.wsv:1878 | 已覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖：`类_MCP_方案资源处理器`（`MCP_Kernel.wsv:1859`）L1864 |
| 处理请求 | FBroEventControl.wsv:1887 | 已覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖 `MCP_Kernel.wsv:1888` |
| 取响应头 | FBroEventControl.wsv:1895 | 已覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖 `MCP_Kernel.wsv:1897` |
| 忽略 | FBroEventControl.wsv:1904 | 已覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖 `MCP_Kernel.wsv:1908` |
| 读取 | FBroEventControl.wsv:1913 | 已覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖 `MCP_Kernel.wsv:1917` |
| 退出 | FBroEventControl.wsv:1925 | 已覆盖 | browser_kernel_scheme `MCP_Kernel.wsv:80` | 覆盖 `MCP_Kernel.wsv:1950` |

**§2.4 计数**：已覆盖 6 / 等价覆盖 0 / 真缺口 0 / N/A 2 = 8。
备注：这是"内部回调机制"——处理器内容由 MCP 固定实现（本地内容/方案服务），**不应**做成"可注册回调"工具；需要自有内容服务时用 `browser_kernel_scheme`。

### 2.5 `类_FBrowser_资源过滤器`（L1935–L2051，6 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:1937 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:1943 | N/A | — | SDK 内部生命周期 |
| 结束 | FBroEventControl.wsv:1981 | 等价覆盖 | browser_intercept action=clear/unmodify/unreplace `MCP_Server_Core.wsv:2563` | 覆盖实现：`类_MCP_篡改过滤器`（`MCP_Callbacks.wsv:1455`）/`类_MCP_缓存过滤器`（`:1067`）的 `结束` |
| 初始化过滤器 | FBroEventControl.wsv:1987 | 等价覆盖 | browser_intercept `MCP_Server_Core.wsv:2563` / browser_inject `MCP_Server_Core.wsv:3228` | 覆盖 `MCP_Callbacks.wsv:1099`（篡改）/`:1017`（缓存）——由 URL 规则驱动 |
| 获取数据 | FBroEventControl.wsv:1994 | 等价覆盖 | browser_intercept `MCP_Server_Core.wsv:2563` | 覆盖 `MCP_Callbacks.wsv:1107` / `:1023`（分包接收，body 改写前置） |
| 修改数据 | FBroEventControl.wsv:2007 | 等价覆盖 | browser_intercept `MCP_Server_Core.wsv:2563` | 覆盖 `MCP_Callbacks.wsv:1198` / `:1041`（返回整数：改写字节数/继续码） |

**§2.5 计数**：已覆盖 0 / 等价覆盖 4 / 真缺口 0 / N/A 2 = 6。

### 2.6 `类_FBrowser_服务器事件`（L2052–L2170，10 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:2054 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:2060 | N/A | — | SDK 内部生命周期 |
| 服务器即将创建 | FBroEventControl.wsv:2083 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:9`：**这是 MCP 自己的 HTTP/WS 传输层**（`MCP_Server.wsv:248` 实例、`:9619 FBrowser_服务器_创建`），把工具调用送进来；暴露成工具会导致自指/死锁，属基础设施 |
| 服务器即将销毁 | FBroEventControl.wsv:2093 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:27`，同上 |
| 收到客户端连接 | FBroEventControl.wsv:2104 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:33`，同上 |
| 收到客户端断开连接 | FBroEventControl.wsv:2116 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:36`，同上 |
| 收到HTTP请求 | FBroEventControl.wsv:2125 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:40`，同上（MCP 协议入口） |
| 收到WebSocket请求 | FBroEventControl.wsv:2138 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:296`，同上 |
| 收到WebSocket连接 | FBroEventControl.wsv:2152 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:319`，同上 |
| 收到WebSocket消息 | FBroEventControl.wsv:2162 | N/A | — | 覆盖 `MCP_Server_HTTP.wsv:325`，同上（`MCP_Server.wsv:441` 注释指出该事件循环单线程、不可在同步等待中重入） |

**§2.6 计数**：已覆盖 0 / 等价覆盖 0 / 真缺口 0 / N/A 10 = 10。
备注：若需要"给页面/外部提供本地 HTTP 内容服务"，等价能力是 `browser_kernel_scheme`（`MCP_Kernel.wsv:80`），**不是**再开一个 CEF 服务器。

### 2.7 `类_FBrowser_开发者消息事件`（L2171–L2250，7 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:2173 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:2179 | N/A | — | SDK 内部生命周期 |
| 开发者消息_VIP_收到消息 | FBroEventControl.wsv:2198 | 已覆盖 | browser_vip_send_devtools_msg `MCP_Server_VIP.wsv:1306` / browser_cdp_call `MCP_Server_Core.wsv:4870` | 覆盖：`类_MCP_DevTools观察者`（`MCP_Callbacks.wsv:495`）L497；观察者注册 `确保CDP观察者已注册`（`MCP_Server.wsv:1926`） |
| 开发者消息_VIP_执行完成 | FBroEventControl.wsv:2211 | 已覆盖 | browser_cdp_call `MCP_Server_Core.wsv:4870` | 覆盖 `MCP_Callbacks.wsv:513`（CDP 异步结果回传，`mcp_result` 取回 `MCP_Server_Core.wsv:4147`） |
| 开发者消息_VIP_收到事件 | FBroEventControl.wsv:2227 | 已覆盖 | browser_cdp_event `MCP_Server_Core.wsv:4971` / browser_kernel_cdp_monitor `MCP_Kernel.wsv:92` | 覆盖 `MCP_Callbacks.wsv:524`（CDP 事件缓冲，按 event_name 查询） |
| 开发者消息_VIP_已附加 | FBroEventControl.wsv:2237 | 已覆盖 | browser_vip_enable_devtools_observer `MCP_Server_VIP.wsv:1629` | 覆盖 `MCP_Callbacks.wsv:546`；工具回包内说明 `cdp_ready` 语义 |
| 开发者消息_VIP_已分离 | FBroEventControl.wsv:2243 | 已覆盖 | browser_vip_enable_devtools_observer enable=false `MCP_Server_VIP.wsv:1677-1681` | 覆盖 `MCP_Callbacks.wsv:554`；注销路径 `MCP_Server.wsv:1966` |

**§2.7 计数**：已覆盖 5 / 等价覆盖 0 / 真缺口 0 / N/A 2 = 7。

### 2.8 `类_FBrowser_URL请求事件`（L2251–L2360，9 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 类_初始化 | FBroEventControl.wsv:2253 | N/A | — | SDK 内部生命周期 |
| 类_清理 | FBroEventControl.wsv:2259 | N/A | — | SDK 内部生命周期 |
| 开始创建 | FBroEventControl.wsv:2282 | 已覆盖 | browser_create_url_request `MCP_Server_Core.wsv:7100`（注册 `MCP_Server.wsv:11106`） | 覆盖：`类_MCP_URL请求回调`（`MCP_Callbacks.wsv:740`）L856 |
| 读取结束 | FBroEventControl.wsv:2293 | 已覆盖 | browser_create_url_request `MCP_Server_Core.wsv:7100` | 覆盖 `MCP_Callbacks.wsv:784` |
| 即将完成 | FBroEventControl.wsv:2303 | 已覆盖 | browser_create_url_request `MCP_Server_Core.wsv:7100` | 覆盖 `MCP_Callbacks.wsv:797`（取状态码/状态文本/MIME） |
| 上传进度 | FBroEventControl.wsv:2314 | **真缺口** | — | 见 §5.2 缺口 2 |
| 下载进度 | FBroEventControl.wsv:2329 | 已覆盖 | browser_create_url_request `MCP_Server_Core.wsv:7100` | 覆盖 `MCP_Callbacks.wsv:876` |
| 获取到数据 | FBroEventControl.wsv:2342 | 已覆盖 | browser_create_url_request `MCP_Server_Core.wsv:7100` | 覆盖 `MCP_Callbacks.wsv:757`（分包数据回调） |
| 获得需授权证书 | FBroEventControl.wsv:2357 | 已覆盖 | browser_create_url_request `MCP_Server_Core.wsv:7100` | 覆盖 `MCP_Callbacks.wsv:896`（返回逻辑型） |

**§2.8 计数**：已覆盖 6 / 等价覆盖 0 / 真缺口 1 / N/A 2 = 9。

**§2 合计**：已覆盖 118 / 等价覆盖 18 / 真缺口 1 / N/A 29 = 166。

---

## 3. `FBroLib.wsv` 侧的事件注册 / 回调指针类（11 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| FBrowser初始化控制.FBrowser_初始化 | FBroLib.wsv:93 | N/A | — | 内部启动：`main.wsv:128 FBrowser_初始化 (设置, 初始化事件)`，事件类为 `类_MCP_初始化事件`（`main.wsv:302`）。属进程初始化，不可远程暴露（会导致重复初始化） |
| FBrowser初始化控制.FBrowser_关闭 | FBroLib.wsv:113 | N/A | — | 内部：`main.wsv:279 FBrowser_关闭 (真)`；远程入口是 `browser_shutdown`（`MCP_Server_System.wsv:197`），无需重复造 |
| 类_FBrowser_事件智能指针.FBrowser创建事件智能指针 | FBroLib.wsv:281 | N/A | — | 嵌入式方法，编译期语法糖；MCP 各处直接用 `.创建(...)` |
| 类_FBrowser_事件智能指针.是否为空 | FBroLib.wsv:287 | N/A | — | 指针判空基础设施 |
| 类_FBrowser_事件智能指针.创建 | FBroLib.wsv:292 | N/A | — | 基础设施；MCP 用例：`MCP_BrowserEvents.wsv:428`（篡改过滤器）、`MCP_BrowserEvents.wsv:571`（缓存过滤器）、`MCP_Server.wsv:9598`（服务器事件） |
| 类_FBrowser_事件智能指针.引用 | FBroLib.wsv:298 | N/A | — | 裸指针引用，MCP 未使用 |
| 类_FBrowser_事件智能指针.取指针 | FBroLib.wsv:305 | N/A | — | 类库自注"存在一定的不安全性"，不应暴露 |
| 类_FBrowser_事件智能指针.取执行类 | FBroLib.wsv:312 | N/A | — | 基础设施；MCP 用例：`MCP_BrowserEvents.wsv:430`（设置篡改动作字段） |
| 类_FBrowser_事件智能指针.取事件数据类型 | FBroLib.wsv:319 | N/A | — | 基础设施 |
| 类_FBrowser_事件智能指针.释放 | FBroLib.wsv:324 | N/A | — | 生命周期 |
| 类_FBrowser_事件智能指针.置空 | FBroLib.wsv:329 | N/A | — | 生命周期 |

**§3 计数**：已覆盖 0 / 等价覆盖 0 / 真缺口 0 / N/A 11 = 11。

---

## 4. 附录（非强制范围，但影响 §1 的 `指纹_虚拟UserAgent`）：`类_FBrowserVIP_UA数据`（`FBroVip.wsv:1722-1947`，30 方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 是否为空 | FBroVip.wsv:1737 | N/A | — | 数据持有类判空 |
| 创建 | FBroVip.wsv:1742 | N/A | — | MCP 内部构造（`MCP_Server_VIP.wsv:1738` 分支内建 UA 数据） |
| 置UserAgent | FBroVip.wsv:1747 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | 调用点 `MCP_Server_VIP.wsv:1795` |
| 置AcceptLanguage | FBroVip.wsv:1753 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | 工具字段 accept_language |
| 置Platform | FBroVip.wsv:1759 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置HighPlatform | FBroVip.wsv:1765 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | userAgentData.platform |
| 置Brands | FBroVip.wsv:1771 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | 双文本数组 |
| 置FullVersionList | FBroVip.wsv:1777 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置FullVersion | FBroVip.wsv:1783 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置PlatformVersion | FBroVip.wsv:1789 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置Architecture | FBroVip.wsv:1795 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置Model | FBroVip.wsv:1801 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置Mobile | FBroVip.wsv:1807 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置Bitness | FBroVip.wsv:1813 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置Wow64 | FBroVip.wsv:1819 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 置FormFactors | FBroVip.wsv:1825 | 已覆盖 | browser_fingerprint_ua `MCP_Server_VIP.wsv:1738` | — |
| 取UserAgent | FBroVip.wsv:1832 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 读取用途：页面内 `navigator.userAgent` 更真实；MCP 无 UA 读回工具 |
| 取AcceptLanguage | FBroVip.wsv:1840 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取Platform | FBroVip.wsv:1849 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取HighPlatform | FBroVip.wsv:1857 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | `navigator.userAgentData.platform` |
| 取Brands | FBroVip.wsv:1865 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取FullVersionList | FBroVip.wsv:1871 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取FullVersion | FBroVip.wsv:1879 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取PlatformVersion | FBroVip.wsv:1888 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取Architecture | FBroVip.wsv:1897 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取Model | FBroVip.wsv:1906 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取Mobile | FBroVip.wsv:1915 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取Bitness | FBroVip.wsv:1922 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取Wow64 | FBroVip.wsv:1931 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |
| 取FormFactors | FBroVip.wsv:1937 | 等价覆盖 | browser_execute_js `MCP_Server_Core.wsv:285` | 同上 |

**§4 计数**：已覆盖 14 / 等价覆盖 14 / 真缺口 0 / N/A 2 = 30。

---

## 5. 小结

### 5.1 计数

| 范围 | 方法数 | 已覆盖 | 等价覆盖 | 真缺口 | N/A |
|---|---|---|---|---|---|
| §1 `类_FBrowserVIP_控制器`（FBroVip.wsv L189–L1356） | 117 | 101 | 11 | **1** | 4 |
| §2.1 `类_FBrowser_应用事件` | 32 | 25 | 0 | 0 | 7 |
| §2.2 `类_FBrowser_浏览器事件` | 90 | 76 | 12 | 0 | 2 |
| §2.3 `类_FBrowser_JS交互事件` | 4 | 0 | 2 | 0 | 2 |
| §2.4 `类_FBrowser_资源处理器` | 8 | 6 | 0 | 0 | 2 |
| §2.5 `类_FBrowser_资源过滤器` | 6 | 0 | 4 | 0 | 2 |
| §2.6 `类_FBrowser_服务器事件` | 10 | 0 | 0 | 0 | 10 |
| §2.7 `类_FBrowser_开发者消息事件` | 7 | 5 | 0 | 0 | 2 |
| §2.8 `类_FBrowser_URL请求事件` | 9 | 6 | 0 | **1** | 2 |
| §3 FBroLib 事件注册/指针类 | 11 | 0 | 0 | 0 | 11 |
| §4 附录 `类_FBrowserVIP_UA数据` | 30 | 14 | 14 | 0 | 2 |
| **合计** | **324** | **233** | **43** | **2** | **46** |

### 5.2 真缺口清单（按价值排序，共 2 条，另有 1 条"工具存在但被刻意禁用"）

1. **`类_FBrowserVIP_控制器.高级_创建标签浏览器`**（`FBroVip.wsv:1201`）
   - 签名（照抄源码）：`方法 高级_创建标签浏览器 <公开 注释 = "VIP高级功能，需赞助后才能使用，谷歌模式下才可以使用，" 注释 = "在当前谷歌UI界面创建一个新的Tab标签浏览器，" 注释 = "设置了浏览器事件后即可和创建浏览器一样控制该标签浏览器">`；参数：`地址 <类型 = 文本型 注释 = "可以为空，为空会获取当前浏览器的地址">`、`序号 <类型 = 整数 注释 = "UI上需要插入的序号位置，设置为-1为在末尾添加" @默认值 = -1>`、`是否激活 <类型 = 逻辑型 @默认值 = 假>`、`额外信息 <类型 = 类_FBrowser_字典值 @默认值 = 空对象>`、`浏览器事件 <类型 = 类_FBrowser_事件智能指针>`、`禁用事件 <类型 = FBrowser_禁用事件 @默认值 = 空对象>`、`标识 <类型 = 文本型 @默认值 = "">`。
   - 对 AI 代理的价值：在同一浏览器窗口内开新标签页并**用同一事件通道**控制它（类库注释：设置浏览器事件后即可像创建浏览器一样控制），适合"多标签并行抓取/对比同一站点"场景，且不必新建窗口。
   - 实现风险：**中高**。① 类库限定"谷歌模式下才可以使用"，本项目是控制台程序、无 GUI 管理窗口（`MCP_Server_System.wsv:14-18` 守卫文案自述）；② 现有 `browser_create_tab` 分支（`MCP_Server_System.wsv:16`，命令号 1141 注册于 `MCP_Server.wsv:1300`）**刻意返回失败**，是项目的有意决策，改动前需先确认"谷歌UI模式"在本项目启动参数下是否成立；③ 要配套把新标签浏览器挂进 `浏览器容器.浏览器数组`（参考 `MCP_BrowserEvents.wsv:79-83`），否则其事件不会进入本项目事件流；④ 与既有能力重叠度有限（`browser_create` 建新窗口/后台浏览器），不算重复造轮子，但收益小于风险，建议**先只做只读探测**（如 `browser_startup_args list` 确认是否 Chrome UI 模式）再决定。

2. **`类_FBrowser_URL请求事件.上传进度`**（`FBroEventControl.wsv:2314`）
   - 签名（照抄源码）：`方法 上传进度 <公开` +（下一行）`参数 当前 <类型 = 整数>` / `参数 总数 <类型 = 整数>`（同族 `下载进度` 在 `FBroEventControl.wsv:2329` 的注释为"|当前|表示呼叫前接收到的字节数，|total|是预期的响应总大小（如果不确定，则为-1）"）。
   - 对 AI 代理的价值：`browser_create_url_request`（POST + body，`MCP_Server.wsv:11106`）上传大 body（如 multipart 上传、大 JSON）时判断进度/是否卡死；当前只能拿"完成/超时"。
   - 实现风险：**低**。纯回调补一个 `@虚拟方法 = 可覆盖`（对照 `MCP_Callbacks.wsv:876 下载进度` 的写法）即可，不新增线程/不重启、不碰 CDP；也不重复造轮子（CDP 无法观测"未经页面"的自建请求上传进度）。属"低成本可补"，优先级高于第 1 条。

> 补充说明（不列为真缺口，但建议主代理记录）：`高级_发送触摸事件`/`高级_发送键盘事件`/`高级_发送鼠标事件`（`FBroVip.wsv:866/932/1032`）虽然核心能力已被 CDP 路径等价覆盖，但**参数面更窄**：类库支持的多触点数组+修饰符、`clickCount`/`pointerType`、`keyIdentifier`/`code`/`isSystemKey`/`nativeVirtualKeyCode`/`autoRepeat` 在 MCP 工具上没有出口。若遇到"必须伪造完整原生事件字段"的反爬场景，可按需补 3 个"原始事件"工具（代价：内核级注入会让本会话 CDP 通道失效，**只在确知要牺牲 CDP 时使用**）。

### 5.3 "看起来是缺口、其实是等价覆盖"的误报清单（20 条，供主代理减少返工）

1. **全部 55 个 `指纹_虚拟*` 方法**（`FBroVip.wsv:225-609`）→ `browser_vip_fingerprint_*`（`MCP_Server_VIP.wsv:673-1054`）+ `browser_fingerprint_*`（`MCP_Server_VIP.wsv:357-787`）+ `browser_fingerprint` action=set_batch（`MCP_Server_Core.wsv:2306`）。名字不同不代表缺口。
2. **`内核开关_禁用Console*` 14 个方法**（`FBroVip.wsv:1219-1312`）→ 单工具 `browser_vip_disable_console`（`MCP_Server_VIP.wsv:1868`），多布尔开关一次下发（`MCP_Server_VIP.wsv:1878-1891`）。
3. **`指纹_虚拟BatteryManager*` 4 个方法**（`FBroVip.wsv:529-551`）→ 单工具 `browser_vip_fingerprint_battery`（`MCP_Server_VIP.wsv:1040`）。
4. **`指纹_虚拟AudioInput/VideoInput/AudioOutput设备` 3 个方法**（`FBroVip.wsv:557-581`）→ 单工具 `browser_vip_fingerprint_media_devices`（`MCP_Server_VIP.wsv:1054`），`target` 选择设备类别（`MCP_Server_VIP.wsv:1125-1133`）。
5. **`指纹_虚拟屏幕分辨率/可用高度和宽度/colorDepth/pixelDepth` 4 个方法**（`FBroVip.wsv:396-422`）→ 单工具 `browser_vip_fingerprint_screen`（`MCP_Server_VIP.wsv:1000`，字段 height/width/avail_h/avail_w/depth/pixel_depth）。
6. **`指纹_虚拟Product/ProductSub/Vendor/VendorSub` 4 个方法**（`FBroVip.wsv:225-273`）→ `browser_vip_fingerprint_product`（`MCP_Server_VIP.wsv:1026`）+ 两个独立小工具（`MCP_Server_VIP.wsv:638/655`）。
7. **`指纹_虚拟HardwareConcurrency`+`DeviceMemory`**（`FBroVip.wsv:279/291`）→ 单工具 `browser_vip_fingerprint_hardware`（`MCP_Server_VIP.wsv:1014`）。
8. **`指纹_虚拟Webglvendor`/`Webglrenderer`**（`FBroVip.wsv:438/446`）→ 单工具 `browser_fingerprint_webgl_vendor`（`MCP_Server_VIP.wsv:422`，同分支设两者）。
9. **Canvas/WebGL/Audio 随机+定值 6 个方法**（`FBroVip.wsv:297-340`）→ 6 个独立工具（`MCP_Server_VIP.wsv:928/940/952/673/690/707`）。
10. **`指纹_取调用计数`/`指纹_清空调用计数`/`清理数据`**（`FBroVip.wsv:211/216/205`）→ `browser_fingerprint` action=count/clear_count/clear（`MCP_Server_Core.wsv:2306`，描述 `MCP_Server.wsv:11054`）。
11. **`高级触摸_按下/放开/移动`**（`FBroVip.wsv:876/887/898`）→ `browser_touch_press/release/move`（`MCP_Server_Core.wsv:6397/6430/6463`）。**注意**：这三个工具**默认走 CDP**（不破会话），只有显式 `kernel:true` 才落到 VIP 内核注入（`MCP_Server_Core.wsv:6407-6423`）——"没直接看到 VIP 调用"不等于缺口。
12. **`高级触摸_单击`**（`FBroVip.wsv:920`）→ press+release 组合（同上两分支）；仅少一个"单击延时"参数。
13. **`高级_设置触发鼠标触摸事件`**（`FBroVip.wsv:623`）→ `browser_vip_touch_emulation` mode=mouse（`MCP_Server_VIP.wsv:1686`）走 CDP `Emulation.setEmitTouchEventsForMouse`；内核级仿真则由 `指纹_启用触摸事件`（`MCP_Server_VIP.wsv:1732`）承担。
14. **`过滤器_修改内容`/`替换资源_数据`/`替换资源_文件`/`取消修改内容`/`取消替换资源` 5 个方法**（`FBroVip.wsv:1134-1194`）→ `browser_intercept`（`MCP_Server_Core.wsv:2563`，action=modify/replace_data/replace_file/block/line_replace/unmodify/unreplace/clear；描述 `MCP_Server.wsv:11056`）。项目**刻意**不走 VIP 过滤器（源码注释 `MCP_BrowserEvents.wsv:390`："手写资源篡改…不依赖VIP官方过滤器"）。唯一真实差异：VIP 版可改"响应协议头"+全局作用域，手写通道只改 body——如需响应头改写，用通用 `browser_cdp_call`（`MCP_Server_Core.wsv:4870`，Fetch 域）而不是新造工具。
15. **`高级_发送键盘/鼠标/触摸事件` 3 个原始全参方法**（`FBroVip.wsv:866/932/1032`）→ `browser_key_event`（`MCP_Server_Core.wsv:1008`）+ `browser_mouse_click/move/wheel`（`:892/966/1415`）+ `browser_touch_*`（`:6397/6430/6463`），另有 `browser_vip_key_input/type`（`MCP_Server_VIP.wsv:1167/1195`）。差距只在"更细的原生事件字段"（见 §5.2 补充说明）。
16. **`类_FBrowser_应用事件.注册自定义方案`/`类_FBrowser_资源处理器` 全族**（`FBroEventControl.wsv:294/1878-1925`）→ `browser_kernel_scheme`（`MCP_Kernel.wsv:80`）+ `类_MCP_方案资源处理器`（`MCP_Kernel.wsv:1859`）；初始化期的方案声明在 `main.wsv:367-375`。
17. **`类_FBrowser_资源过滤器` 全族**（`FBroEventControl.wsv:1981-2007`）→ `browser_intercept`/`browser_inject` 驱动的 `类_MCP_篡改过滤器`（`MCP_Callbacks.wsv:1085`）/`类_MCP_缓存过滤器`（`:1010`）。这是实现细节，不是"少了可注册回调"。
18. **`类_FBrowser_服务器事件` 全 8 个事件**（`FBroEventControl.wsv:2083-2162`）→ **MCP 自己的 HTTP/WS 传输层**（`MCP_Server.wsv:248`、`:9619`；覆盖 `MCP_Server_HTTP.wsv:9-325`）。它**不该**被做成工具（自指、且 `MCP_Server.wsv:441` 注明该事件循环单线程，重入会卡死）。需要本地内容服务请用 `browser_kernel_scheme`。
19. **`类_FBrowser_应用事件` 的 `渲染_*` / `渲染_VIP_WebSocket客户端_*` 共 25 个方法**（`FBroEventControl.wsv:305-431`）→ 覆盖+入库代码**都已就位**（`main.wsv:418-898`，含 `app_v8_exception`（MAIN:363）、`app_render_*` 等），但**本机该族不产生记录**（`main.wsv:944-955` 自述 + `browser_event` 的 app_ 分支内置诚实告知 `MCP_Server_Core.wsv:4929-4939`）。**"接线存在"不等于"事件可用"**——主代理不要按"已覆盖=可查"来写文档；相关需求请改用 `browser_event` 的浏览器事件族（本机有效）+ `browser_execute_js`/`browser_collect console_get`/`browser_network`，主进程侧用 CDP 类工具。
20. **`类_FBrowser_事件智能指针` 全 9 个方法 + `FBrowser_初始化`/`FBrowser_关闭` + `类_FBrowserVIP_控制器.取浏览器/是否为空/置空/逐字分割/指纹_虚拟内核功能`** → 基础设施/私有/弃用（详见 §1、§3）。其中 `指纹_虚拟内核功能` 是类库**自标弃用**且**无 `<公开>`** 的方法，等价能力是 `内核开关_设置CSS/Web/前端V8内核`（`MCP_Server_VIP.wsv:1219/1248/1277`）。

### 5.4 复核入口速查

| 结论类型 | 一键复核命令（DSH grep 工具） |
|---|---|
| VIP 工具分支全表 | `否则 \(方法名 == "browser_` on `src/MCP_Server_VIP.wsv` → 71 处 |
| 核心工具分支全表 | `否则 \(方法名 == "browser_` on `src/MCP_Server_Core.wsv` → 157 处 |
| 事件覆盖点 | `@虚拟方法 = 可覆盖` on `src/*.wsv` → 本项目 166 处（BE 90 + MAIN 30 + Callbacks 26 + Kernel 6 + HTTP 8 + …） |
| 事件入库管道 | `记录监控事件 \(` on `src/MCP_BrowserEvents.wsv` → 66 处；`记录浏览器事件`/`记录应用事件` on `src/MCP_Server.wsv:8077/8096` |
| app_* 不可用自述 | `app_` 于 `src/main.wsv`（L944-955 注释）+ `src/MCP_Server_Core.wsv:4929-4939` |
