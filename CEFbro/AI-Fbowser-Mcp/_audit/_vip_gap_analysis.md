# VIP 控制器 API × MCP 工具 —— 能力缺口审计（只读静态分析）

审计对象：`类_FBrowserVIP_控制器`（权威定义 `资料/类库/FBrowser浏览器/FBroVip.wsv` 第 175–1361 行；类声明原文 FBroVip.wsv:175 `类 类_FBrowserVIP_控制器 <公开 注释 = "VIP功能，需要赞助后才能使用">`）与项目 `src/` 实际暴露的 MCP 工具。

本文件由静态阅读生成，**未编译、未运行、未调用任何 MCP 工具**；所有"实现建议"均为未验证草案，需另行验证。

## 0. 审计方法与判定口径

### 0.1 权威定义与规模

- 权威文件：`C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroVip.wsv`（1948 行）。
- 控制器类边界：`类 类_FBrowserVIP_控制器`（FBroVip.wsv:175）→ 类结束 `}`（FBroVip.wsv:1361）。
- 该类内 `方法` 声明共 **117** 条：`<公开>` 115 条 + 无 `<公开>` 限定（私有）2 条 —— `指纹_虚拟内核功能`（FBroVip.wsv:508，声明原文 `方法 指纹_虚拟内核功能 <注释 = "弃用，VIP功能，需要赞助后才能使用，通过内核版本号虚拟当前浏览器内核，"`，**无** `公开` 标记）与 `逐字分割`（FBroVip.wsv:1006，声明原文 `方法 逐字分割`，**无** `公开` 标记）。
- 与任务所述"约 102 个方法"的差异可精确对上：上一次扫描的产物 `_audit\_cg2_cands.json` 中 `类_FBrowserVIP_控制器` 候选恰为 **102** 条，它遗漏了 15 条 —— 类管道 3 条（`是否为空`/`置空`/`取浏览器`）、`WebSocket_启用拦截` 1 条、`开发者消息_*` 4 条、`过滤器_*` 7 条（117 = 102 + 15）。本审计把 117 条全部纳入。

### 0.2 搜索方式（可复现）

- 对每条方法名，在 `src/**/*.wsv`（**排除** 16 个 `*~vbak*` 备份文件与 `_audit/` 下的副本）执行正则 `\.<方法名>\s*\(`，命中即"真实调用点"；再以"该行是否以 `//` 或 `#` 开头"剔除注释里的同名出现（全库仅 `是否为空` 有 2 处纯注释命中：MCP_Server.wsv:8244、MCP_Server_HTTP.wsv:14）。
- 覆盖工具名不靠猜：对每个调用点向上回扫（上限 600 行）取**最近的** `方法名 == "xxx"` 分派分支即工具名；对 action 型分派器（`browser_fingerprint`/`browser_intercept`/`browser_antidetect_presets` 等）再在"工具分支行 → 调用行"区间内取最近的 `action == "yyy"`。
- 实搜文件（16 个）：main.wsv, MCP_BrowserEvents.wsv, MCP_Callbacks.wsv, MCP_Constants.wsv, MCP_Kernel.wsv, MCP_ResponseBuilders.wsv, MCP_Server.wsv, MCP_Server_Core.wsv, MCP_Server_Form.wsv, MCP_Server_HTTP.wsv, MCP_Server_Reverse.wsv, MCP_Server_System.wsv, MCP_Server_Utils.wsv, MCP_Server_VIP.wsv, MCP_Server_Workflow.wsv, MCP_Stdio.wsv。
- 工具清单来源：`MCP_Server.wsv` 中 `添加工具JSON ("工具名", ...)` 共 **313** 处，去重后 **313** 个工具名。

### 0.3 判定口径（本文件统一使用）

| 判定 | 含义 |
| --- | --- |
| **COVERED** | 某个 MCP 工具（或某工具的一个 action 分支/参数）**直接调用了**该同名类方法 |
| **REACHABLE-INDIRECTLY** | 无专属工具调用该同名方法，但存在一条**可点名的**既有通路（另一工具的 action、两个既有工具的组合、或某个具体 CDP 方法经 `browser_cdp_call` 透传）。CDP 通路一律标注"未核实" |
| **REAL GAP** | 既无专属工具、也无任何可点名的既有通路。若理论上仅剩 `browser_cdp_call` 通用透传一条路，行内显式写出并标注未核实 |
| **NOT-APPLICABLE** | 类管道方法、私有方法、或类库自身标注弃用/对本架构无意义 |
| **CREATION-TIME-ONLY** | 只能在创建浏览器时设定。**本控制器 117 条方法中没有任何一条属于此类**，论证见第 3 节 |

> 注释列说明：把该方法 `方法` 声明行及其后续声明行（直到 `参数`/`{` 为止）中所有 `注释 = "..."` 属性按出现顺序用 ` / ` 连接，即"方法注释 + 参数注释"原文；无 `注释` 属性的方法直接引其声明原文。

## 1. 主表：`类_FBrowserVIP_控制器` 全部 117 个方法

| # | 方法 | 中文注释（原文引用） | `src/` 调用点 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `是否为空` (公开) | （无 `注释` 属性；声明原文：`方法 是否为空 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`） | 477 处同名匹配，其中作用于 VIP 控制器实例（`vip*.是否为空 (`）的 86 处（如 MCP_Server_VIP.wsv:1413） | NOT-APPLICABLE：类管道判空方法，被当作每个 VIP 分支的守卫使用（MCP_Server_VIP.wsv:1413 原文 `如果 (vipCtrl.是否为空 () == 假)`），本身无需工具 |
| 2 | `置空` (公开) | "手动置空当前类包含的cef类指针，置空后该类将无法使用，如没有其他引用将自动释放cef类指针的资源数据" | 5 处同名匹配，其中作用于 VIP 控制器实例（`vip*.是否为空 (`）的 0 处（如 MCP_Server_VIP.wsv:1413） | NOT-APPLICABLE：类管道方法；对 VIP 控制器实例无任何调用点（同名 5 处均属其它对象） |
| 3 | `取浏览器` (公开) | "取出当前控制器对应的浏览器，如果不存在或者已经关闭将返回空" | **0 hits** | NOT-APPLICABLE：**0 hits**。项目用 `MCP命令服务器.取主浏览器 ()` 与 `FBrowser_浏览器_通过ID取浏览器 (...)`（MCP_Server_Core.wsv:623 原文 `closeBrowser = FBrowser_浏览器_通过ID取浏览器 (closeID)`）取代 |
| 4 | `清理数据` (公开) | "清理全部VIP设置的参数，包括指纹、代理、wss、debugger、isTrusted相关参数数据" | MCP_Server_Core.wsv:2193 | COVERED：browser_fingerprint action=clear |
| 5 | `指纹_清空调用计数` (公开) | （无 `注释` 属性；声明原文：`方法 指纹_清空调用计数 <公开>`） | **0 hits** | **REAL GAP**：**0 hits**。类库侧计数器只有读没有复位入口（读的那半在 MCP_Server_Core.wsv:2198 `返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))`） |
| 6 | `指纹_取调用计数` (公开) | "获取对应指纹被调用的次数，有的数据被调用不一定是为了指纹，仅供参考，返回类型为一个json文本" | MCP_Server_Core.wsv:2198 | COVERED：browser_fingerprint action=count |
| 7 | `指纹_虚拟ProductSub` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:645、MCP_Server_VIP.wsv:1030 | COVERED：browser_fingerprint_product_sub、browser_vip_fingerprint_product |
| 8 | `指纹_虚拟Vendor` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2347、MCP_Server_VIP.wsv:1031 | COVERED：browser_fingerprint action=set_batch、browser_vip_fingerprint_product |
| 9 | `指纹_虚拟VendorSub` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:662、MCP_Server_VIP.wsv:1032 | COVERED：browser_fingerprint_vendor_sub、browser_vip_fingerprint_product |
| 10 | `指纹_虚拟UserAgent` (公开) | "虚拟用户标识，在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / UA数据" | MCP_Server.wsv:2069、MCP_Server_Core.wsv:2341（共 4 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=set_batch、browser_fingerprint_ua；**另有创建时自动应用**（`应用持久配置到浏览器`，MCP_Server.wsv:2013，由 MCP_BrowserEvents.wsv:89 在浏览器创建事件中调用） |
| 11 | `指纹_虚拟Languages` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2359、MCP_Server_VIP.wsv:409（共 3 处） | COVERED：browser_fingerprint action=set_batch、browser_fingerprint_languages |
| 12 | `指纹_虚拟AppCodeName` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:611 | COVERED：browser_fingerprint_appcodename |
| 13 | `指纹_虚拟AppName` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:381 | COVERED：browser_fingerprint_appname |
| 14 | `指纹_虚拟AppVersion` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:628 | COVERED：browser_fingerprint_appversion |
| 15 | `指纹_虚拟Product` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2353、MCP_Server_VIP.wsv:1029 | COVERED：browser_fingerprint action=set_batch、browser_vip_fingerprint_product |
| 16 | `指纹_虚拟HardwareConcurrency` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2378、MCP_Server_Core.wsv:6922（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=set_batch、browser_vip_fingerprint_hardware |
| 17 | `指纹_虚拟CookieEnabled` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:554 | COVERED：browser_fingerprint_cookie_enabled |
| 18 | `指纹_虚拟DeviceMemory` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2384、MCP_Server_Core.wsv:6923（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=set_batch、browser_vip_fingerprint_hardware |
| 19 | `指纹_虚拟Canvas_随机` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2214、MCP_Server_Core.wsv:6902（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=canvas_random、browser_vip_fingerprint_canvas |
| 20 | `指纹_虚拟WebGL_随机` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2231、MCP_Server_Core.wsv:6903（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=webgl_random、browser_vip_fingerprint_webgl |
| 21 | `指纹_虚拟Audio_随机` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 最好不低于100个" | MCP_Server_Core.wsv:2248、MCP_Server_Core.wsv:6904（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=audio_random、browser_vip_fingerprint_audio |
| 22 | `指纹_虚拟Canvas_定值` (公开) | "随机值和定值不能同时使用,在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 单个噪点格式：x:y:r:g:b:a，多个数据以,隔开，x和y是噪点坐标，rgba为噪点颜色值，都为正整数值;注意：文本不能太长，太长可能会崩，最好元素个数在100以下" | MCP_Server_VIP.wsv:680 | COVERED：browser_vip_fingerprint_canvas_fixed |
| 23 | `指纹_虚拟WebGL_定值` (公开) | "随机值和定值不能同时使用,在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 单个噪点格式:x:y, 多个以,隔开，x和y是噪点坐标,为1以下小数值，可为负数;注意：文本不能太长，太长可能会崩，最好元素个数在100以下" | MCP_Server_VIP.wsv:697 | COVERED：browser_vip_fingerprint_webgl_fixed |
| 24 | `指纹_虚拟Audio_定值` (公开) | "随机值和定值不能同时使用,在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 注意：文本不能太长，太长可能会崩，最好元素个数在1000以下" | MCP_Server_VIP.wsv:714 | COVERED：browser_vip_fingerprint_audio_fixed |
| 25 | `指纹_虚拟Plugins` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 0未不修改，1为添加，2为覆盖" | MCP_Server_VIP.wsv:364 | COVERED：browser_fingerprint_plugins |
| 26 | `指纹_虚拟JavaEnabled` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:571 | COVERED：browser_fingerprint_java_enabled |
| 27 | `指纹_虚拟Webdriver` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server.wsv:2079、MCP_Server_Core.wsv:2392 | COVERED：browser_fingerprint action=set_batch；**另有创建时自动应用**（`应用持久配置到浏览器`，MCP_Server.wsv:2013，由 MCP_BrowserEvents.wsv:89 在浏览器创建事件中调用） |
| 28 | `指纹_虚拟OnLine` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:593 | COVERED：browser_fingerprint_online |
| 29 | `指纹_虚拟Canvas字体指纹` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:482、MCP_Server_VIP.wsv:536（共 3 处） | COVERED：browser_font_randomize、browser_vip_fingerprint_canvas_font |
| 30 | `指纹_虚拟CSS字体指纹` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:481、MCP_Server_VIP.wsv:535（共 3 处） | COVERED：browser_font_randomize、browser_vip_fingerprint_font |
| 31 | `指纹_虚拟屏幕XY` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:6918、MCP_Server_VIP.wsv:784 | COVERED：browser_antidetect_presets、browser_fingerprint_screen_xy |
| 32 | `指纹_虚拟屏幕分辨率` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2401、MCP_Server_VIP.wsv:1003 | COVERED：browser_fingerprint action=set_batch、browser_vip_fingerprint_screen |
| 33 | `指纹_虚拟屏幕可用高度和宽度` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2408、MCP_Server_VIP.wsv:1004 | COVERED：browser_fingerprint action=set_batch、browser_vip_fingerprint_screen |
| 34 | `指纹_虚拟屏幕pixelDepth` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 如果是模拟手机环境，这个值要设置大于1，否则可能会被检测" | MCP_Server_VIP.wsv:1006 | COVERED：browser_vip_fingerprint_screen |
| 35 | `指纹_虚拟屏幕colorDepth` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 如果是模拟手机环境，这个值要设置大于1，否则可能会被检测" | MCP_Server_VIP.wsv:1005 | COVERED：browser_vip_fingerprint_screen |
| 36 | `指纹_虚拟DevicePixelRatio` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:6920、MCP_Server_VIP.wsv:749 | COVERED：browser_antidetect_presets、browser_fingerprint_pixel_ratio |
| 37 | `指纹_虚拟Webglvendor` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2365、MCP_Server_VIP.wsv:438 | COVERED：browser_fingerprint action=set_batch、browser_fingerprint_webgl_vendor |
| 38 | `指纹_虚拟Webglrenderer` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:2371、MCP_Server_VIP.wsv:441 | COVERED：browser_fingerprint action=set_batch、browser_fingerprint_webgl_vendor |
| 39 | `指纹_虚拟Rect` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:6919、MCP_Server_VIP.wsv:732 | COVERED：browser_antidetect_presets、browser_vip_fingerprint_rect |
| 40 | `指纹_虚拟WebrtcIP` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 外网地址,设置为“”则为不修改,要和代理保持一致" | MCP_Server_Core.wsv:2295、MCP_Server_Core.wsv:6939（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=webrtc、browser_vip_fingerprint_webrtc |
| 41 | `指纹_虚拟Date时区` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 因时区环境特殊，同域名网页刷新不支持直接更换，只有当域名变更重新加载或新建浏览器时候才能真正的修改成功，请注意！！" | MCP_Server_Core.wsv:2309、MCP_Server_Core.wsv:6925（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=timezone、browser_vip_fingerprint_timezone |
| 42 | `指纹_虚拟Viewport` (公开) | "虚拟window.visualViewport值，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:992 | COVERED：browser_vip_fingerprint_viewport |
| 43 | `指纹_启用触摸事件` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_Core.wsv:6943、MCP_Server_VIP.wsv:766（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint_touch_enable、browser_vip_touch_emulation |
| 44 | `指纹_虚拟内核功能` (私有) | "弃用，VIP功能，需要赞助后才能使用，通过内核版本号虚拟当前浏览器内核， / 设置后会关闭超过内核版本号的相关JS和CSS功能，达到模拟当前设置内核版本的效果，防止部分网站通过抓取内核功能判断出真实的内核版本号； / 注意： / 1.如果设置后网页显示不正常说明网页并不兼容你当前设置的内核版本，请重新设置； / 2.不支持单进程模式，使用单进程模式会变为全局环境，浏览器单独设置无效 / 建议设置范围为116-86,要和UA保持一致" | **0 hits** | NOT-APPLICABLE：**0 hits**；该方法未被 `<公开>` 限定（私有），且注释首词为"弃用"；其功能已由 `内核开关_设置CSS内核`/`设置Web内核`/`设置V8内核` 取代（三者均有工具） |
| 45 | `指纹_设置SSL加密套件` (公开) | "VIP功能，需要赞助后才能使用,用于TLS指纹，通过此设置即可控制对应的TLS协议，以达到修改TLS指纹的效果； / 注意：协议如果设置错误可能会导致网页无法打开或者某些功能异常； / 参考：TLS版本,不设置默认为1.2到1.3" | MCP_Server_Core.wsv:2323、MCP_Server_VIP.wsv:920 | COVERED：browser_fingerprint action=ssl、browser_vip_fingerprint_ssl |
| 46 | `指纹_虚拟BatteryManagerCharging` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:1043 | COVERED：browser_vip_fingerprint_battery |
| 47 | `指纹_虚拟BatteryManagerChargingTime` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:1045 | COVERED：browser_vip_fingerprint_battery |
| 48 | `指纹_虚拟BatteryManagerDischargingTime` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:1046 | COVERED：browser_vip_fingerprint_battery |
| 49 | `指纹_虚拟BatteryManagerLevel` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用" | MCP_Server_VIP.wsv:1044 | COVERED：browser_vip_fingerprint_battery |
| 50 | `指纹_虚拟AudioInput设备` (公开) | "VIP功能，需要赞助后才能使用，虚拟媒体输出设备硬件信息，如播放设备等信息，注意虚拟媒体设备可能会照成浏览器声音或麦克风异常无法获取到真实设备 / 0为清空，1为添加，2为覆盖,如果为0，下面修改数据设不设置都不会生效" | MCP_Server_VIP.wsv:1061 | COVERED：browser_vip_fingerprint_media_devices |
| 51 | `指纹_虚拟VideoInput设备` (公开) | "VIP功能，需要赞助后才能使用，虚拟媒体输出设备硬件信息，如播放设备等信息，注意虚拟媒体设备可能会照成浏览器声音或麦克风异常无法获取到真实设备 / 0为清空，1为添加，2为覆盖,如果为0，下面修改数据设不设置都不会生效" | MCP_Server_VIP.wsv:1069 | COVERED：browser_vip_fingerprint_media_devices |
| 52 | `指纹_虚拟AudioOutput设备` (公开) | "VIP功能，需要赞助后才能使用，虚拟媒体输出设备硬件信息，如播放设备等信息，注意虚拟媒体设备可能会照成浏览器声音或麦克风异常无法获取到真实设备 / 0为清空，1为添加，2为覆盖,如果为0，下面修改数据设不设置都不会生效" | MCP_Server_VIP.wsv:1065 | COVERED：browser_vip_fingerprint_media_devices |
| 53 | `指纹_虚拟定位` (公开) | "虚拟Geolocation经纬度值，不设置此值默认CEF是获取不到经纬度的，本命令值支持实时设置； / 注意：如还有通过外网IP判断定位，则要配合代理和webrtc一起使用， / 可通过navigator.geolocation.getCurrentPosition(function(t){console.log(t);})命令查看是否设置成功 / longitude" | MCP_Server_Core.wsv:2304、MCP_Server_Core.wsv:6941（共 3 处） | COVERED：browser_antidetect_presets、browser_fingerprint action=geolocation、browser_vip_fingerprint_geolocation |
| 54 | `指纹_虚拟屏幕方向` (公开) | "VIP功能，需赞助后才能使用，用于手机模式下虚拟屏幕为横屏或者竖屏，配合分辨率窗口大小一起使用 / 设置方向类型，横屏或竖屏；参考:屏幕方向类型.，通过window.screen.orientation.type验证" | MCP_Server_VIP.wsv:1645 | COVERED：browser_vip_orientation |
| 55 | `WebSocket_启用拦截` (公开) | （无 `注释` 属性；声明原文：`方法 WebSocket_启用拦截 <公开>`） | MCP_Server_Core.wsv:2461、MCP_Server_VIP.wsv:30 | COVERED：browser_intercept action=ws_hook、browser_vip_websocket_intercept |
| 56 | `高级_设置触发鼠标触摸事件` (公开) | "在浏览器载入完成后调用,VIP功能，需要赞助后才能使用" | **0 hits** | **REAL GAP**：**0 hits**。它**不等于**已有工具覆盖的 `指纹_启用触摸事件`：后者底层 `FBroHsVIPControl_SetTouchEventEmulationEnabled`（FBroVip.wsv:504），本方法底层 `FBroHsVIPControl_SetEmitTouchEventsForMouse`（FBroVip.wsv:627）。唯一可能通路是 `browser_cdp_call` 透传 CDP `Emulation.setEmitTouchEventsForMouse`（**未核实**） |
| 57 | `高级_设置代理` (公开) | "设置当前浏览器代理，在\"浏览器_即将导航\"或\"浏览器_创建完毕\"事件中设置，也可在其他地方设置，但刷新后才会生效； / 配合独立缓存一起使用设置的代理也会成为独立，否则还是全局，如果需要认证则需要设置账号密码； / 带账号密码的S5代理，需赞助会员才可使用 / 注意：因为设置代理利用的首选项功能，如果启用了保留用户首选项，关闭的时候就要使用清理代理功能，否则可能再次打开浏览器还是使用的之前的代理，但又未手动设置账号密码或代理已经关闭而导致代理失败网页无法显示 / 要区分大小写，不要有空格，否则地址错误将会设置失败" | MCP_Server_Core.wsv:1392、MCP_Server_VIP.wsv:60 | COVERED：browser_set_proxy、browser_set_s5_proxy |
| 58 | `高级_清空代理` (公开) | （无 `注释` 属性；声明原文：`方法 高级_清空代理 <公开>`） | MCP_Server_Core.wsv:1425、MCP_Server_VIP.wsv:177 | COVERED：browser_clear_proxy、browser_vip_clear_s5_proxy |
| 59 | `开发者消息_发送消息` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 英文名：SendDevToolsMessage 说明：Send a method call message over the DevTools protocol / See the DevTools protocol documentation at https://chromedevtools.github.io/devtools-protocol/ / for details of supported methods and the expected \"params\" dictionary contents. / \|message\| will be copied if necessary. This method will return true if / called on the UI thread and the message was successfully submitted for / validation, otherwise false. Validation will be applied asynchronously and / any messages that fail due to formatting errors or missing parameters may / be discarded without notification. Prefer ExecuteDevToolsMethod if a more / structured approach to message formatting is desired. /  / Every valid method call will result in an asynchronous method result or / error message that references the sent message \"id\". Event messages are / received while notifications are enabled (for example, between method calls / for \"Page.enable\" and \"Page.disable\"). All received messages will be / delivered to the observer(s) registered with AddDevToolsMessageObserver. / See CefDevToolsMessageObserver::OnDevToolsMessage documentation for details / of received message contents. /  / Usage of the SendDevToolsMessage, ExecuteDevToolsMethod and / AddDevToolsMessageObserver methods does not require an active DevTools / front-end or remote-debugging session. Other active DevTools sessions will / continue to function independently. However, any modification of global / browser state by one session may not be reflected in the UI of other / sessions. /  / Communication with the DevTools front-end (when displayed) can be logged / for development purposes by passing the / `--devtools-protocol-log-file=<path>` command-line flag. / " | MCP_Server_VIP.wsv:1262 | COVERED：browser_vip_send_devtools_msg |
| 60 | `开发者消息_执行方法` (公开) | "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用 / 英文名：ExecuteDevToolsMethod 说明：Execute a method call over the DevTools protocol. / This is a more structured version of SendDevToolsMessage； / This method will return the assigned message ID if called on the UI thread and the message was successfully submitted for validation, otherwise 0. / See the SendDevToolsMessage documentation for additional usage information." | MCP_Server.wsv:1645 | COVERED：经 CDP 通道 helper —— `执行CDP命令_带参数`（MCP_Server.wsv:1601/1645 位于该 helper 体内），该 helper 由 `browser_debugger_evaluate`（MCP_Server_Core.wsv:4906）、`browser_network_body`（MCP_Server_Core.wsv:4632）等 CDP 工具调用；观察者注册/注销另有显式工具 `browser_vip_enable_inspector`（MCP_Server_VIP.wsv:236 注册、241 注销）与 `browser_vip_enable_devtools_observer`（MCP_Server_VIP.wsv:1548 注册、1553 注销），注销路径还由 `确保CDP观察者已注册`/`注销CDP观察者` 在创建事件（MCP_BrowserEvents.wsv:97）与关闭流程（main.wsv:246、MCP_Server.wsv:8559）中调用 |
| 61 | `开发者消息_启用监管者事件` (公开) | "启用后，事件中的开发者消息才会有效,创建成功返回真，已创建或者创建失败返回假 / 异步获取数据或者触发响应事件的回调，数据反馈或者事件响应会触发回调中对应的方法。" | MCP_Server.wsv:1601、MCP_Server.wsv:1798 | COVERED：经 CDP 通道 helper —— `执行CDP命令_带参数`（MCP_Server.wsv:1601/1645 位于该 helper 体内），该 helper 由 `browser_debugger_evaluate`（MCP_Server_Core.wsv:4906）、`browser_network_body`（MCP_Server_Core.wsv:4632）等 CDP 工具调用；观察者注册/注销另有显式工具 `browser_vip_enable_inspector`（MCP_Server_VIP.wsv:236 注册、241 注销）与 `browser_vip_enable_devtools_observer`（MCP_Server_VIP.wsv:1548 注册、1553 注销），注销路径还由 `确保CDP观察者已注册`/`注销CDP观察者` 在创建事件（MCP_BrowserEvents.wsv:97）与关闭流程（main.wsv:246、MCP_Server.wsv:8559）中调用 |
| 62 | `开发者消息_关闭监管者事件` (公开) | （无 `注释` 属性；声明原文：`方法 开发者消息_关闭监管者事件 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`） | MCP_BrowserEvents.wsv:283、MCP_Server.wsv:1838 | COVERED：经 CDP 通道 helper —— `执行CDP命令_带参数`（MCP_Server.wsv:1601/1645 位于该 helper 体内），该 helper 由 `browser_debugger_evaluate`（MCP_Server_Core.wsv:4906）、`browser_network_body`（MCP_Server_Core.wsv:4632）等 CDP 工具调用；观察者注册/注销另有显式工具 `browser_vip_enable_inspector`（MCP_Server_VIP.wsv:236 注册、241 注销）与 `browser_vip_enable_devtools_observer`（MCP_Server_VIP.wsv:1548 注册、1553 注销），注销路径还由 `确保CDP观察者已注册`/`注销CDP观察者` 在创建事件（MCP_BrowserEvents.wsv:97）与关闭流程（main.wsv:246、MCP_Server.wsv:8559）中调用 |
| 63 | `高级_网页截图` (公开) | "执行截图后，数据在回调类\"类_FBrowser通用回调\"中的\"数据回调\"获取，可通过继承实现自定义回调类，执行成功返回标识ID，执行失败返回0 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / 图像压缩格式(默认为png)，取值范围:jpeg、png、webp" | MCP_Server_Core.wsv:2671 | COVERED：browser_screenshot |
| 64 | `高级_启用执行环境` (公开) | "执行高级JS功能之前需要先启用执行环境，否则无效，一个浏览器执行一次就行，如果关闭了需要重新开启才会有效，使用完毕后设置假关闭执行环境 / 真启用，假关闭" | MCP_Server_VIP.wsv:271 | COVERED：browser_vip_enable_js_env |
| 65 | `高级_取当前环境ID清单` (公开) | " VIP高级功能，需赞助后才能使用，执行\"高级_启用执行环境\"启用后生效， / 返回值为文本列表值，值为环境ID文本数据,如果网站还在加载获取的清单值也会因为加载状态的不同而不同" | MCP_Server_VIP.wsv:293 | COVERED：browser_vip_get_js_env_ids |
| 66 | `高级_执行JS` (公开) | "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，执行JS代码，数据在回调类\"类_FBrowserVIP_通用回调\"中的\"数据回调\"获取，可通过继承实现自定义回调类 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / expression" | MCP_Server_VIP.wsv:1430 | COVERED：browser_vip_execute_js_context |
| 67 | `高级_执行JS_框架ID` (公开) | "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，通过框架ID执行JS，框架ID只能通过\"VIP_高级_取当前环境ID清单\"获取中的frameID获取，不同于浏览器获取的框架ID / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / expression，如果js语法或者逻辑存在错误，回调也会返回成功，错误信息可以在回调返回的JSON值中查看" | MCP_Server_VIP.wsv:1426 | COVERED：browser_vip_execute_js_context |
| 68 | `高级_执行JS_主框架` (公开) | "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，在主框架/顶级框架执行JS / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / expression，如果js语法或者逻辑存在错误，回调也会返回成功，错误信息可以在回调返回的JSON值中查看" | **0 hits** | **REAL GAP**：**0 hits**。`browser_vip_execute_js_context` 只有 `context_id`/`frame_id` 两个参数（MCP_Server_VIP.wsv:1415-1431），无"主框架"语义；近似做法要客户端先调 `browser_vip_get_js_env_ids` 再假定主框架的 contextId（类库注释称首次加载主框架为 1，FBroVip.wsv:757），属未文档化约定 |
| 69 | `高级_执行JS_全部框架` (公开) | "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，在当前所有框架里面都执行JS代码，所有框架都会执行一遍，回调会被多次调取 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / expression，如果js语法或者逻辑存在错误，回调也会返回成功，错误信息可以在回调返回的JSON值中查看" | **0 hits** | **REAL GAP**：**0 hits**。可用的近似通路是客户端对 `browser_vip_get_js_env_ids` 返回的每个 id 逐个调 `browser_vip_execute_js_context`（多调用、失去"所有框架各执行一遍"的原子语义，且类库注明回调会被多次调取，FBroVip.wsv:821）；另一条是 `browser_cdp_call` 透传 `Runtime.evaluate`（**未核实**） |
| 70 | `高级_执行JS_框架序号` (公开) | "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，通过框架ID执行JS，框架ID只能通过\"VIP_高级_取当前环境ID清单\"获取中的frameID获取，不同于浏览器获取的框架ID / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / expression，如果js语法或者逻辑存在错误，回调也会返回成功，错误信息可以在回调返回的JSON值中查看" | **0 hits** | **REAL GAP**：**0 hits**。任何工具都没暴露"框架序号 → contextId"的映射；类库自身也警告 FBroVip.wsv:847 `注意这个序号和开发者工具显示的序号和浏览器取出的框架顺序不一定一样` |
| 71 | `高级_发送触摸事件` (公开) | "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件 / touchStart=0,touchMove=1,touchCancel=2,touchEnd=3，第一次执行要先touchStart,执行完操作后touchEnd" | **0 hits** | **REAL GAP**：**0 hits**。`browser_touch_press/move/release` 只调 `高级触摸_按下/移动/放开`（MCP_Server_Core.wsv:5300/5366/5333），项目自带的 CDP 派发把触点写死为单点 `"radiusX":1,"radiusY":1,"force":1,"id":0`（MCP_Server.wsv:3267），故多点触摸、压力、半径、旋转角不可达；只剩 `browser_cdp_call` 透传 `Input.dispatchTouchEvent`（**未核实**） |
| 72 | `高级触摸_按下` (公开) | "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件" | MCP_Server_Core.wsv:5300 | COVERED：browser_touch_press |
| 73 | `高级触摸_放开` (公开) | "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件" | MCP_Server_Core.wsv:5333 | COVERED：browser_touch_release |
| 74 | `高级触摸_移动` (公开) | "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件" | MCP_Server_Core.wsv:5366 | COVERED：browser_touch_move |
| 75 | `高级触摸_取消` (公开) | "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件" | MCP_Server_VIP.wsv:328 | COVERED：browser_vip_touch_cancel |
| 76 | `高级触摸_单击` (公开) | "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件" | **0 hits** | REACHABLE-INDIRECTLY：`browser_touch_press` + `browser_touch_release` 两次调用即可组合（类库实现本身就是 按下→延时→放开，FBroVip.wsv:925-927）；取消用 `browser_vip_touch_cancel`（MCP_Server_VIP.wsv:328） |
| 77 | `高级_发送键盘事件` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送键盘事件，支持后台操作 / type:Type of the key event.Allowed Values: keyDown, keyUp, rawKeyDown, char." | **0 hits** | REACHABLE-INDIRECTLY：其 5 个封装 `高级键盘_*` 均已暴露（`browser_vip_key_press`/`release`/`click`/`input`/`type`，MCP_Server_VIP.wsv:136/159/1096/1124/1147），另有原生/CDP 路径 `browser_key_event`（MCP_Server_Core.wsv:918） |
| 78 | `高级键盘_按下` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送键盘事件，支持后台操作" | MCP_Server_Core.wsv:918、MCP_Server_VIP.wsv:136 | COVERED：browser_key_event、browser_vip_key_press |
| 79 | `高级键盘_放开` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送键盘事件，支持后台操作" | MCP_Server_Core.wsv:923、MCP_Server_VIP.wsv:159 | COVERED：browser_key_event、browser_vip_key_release |
| 80 | `高级键盘_单击` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送键盘事件，支持后台操作" | MCP_Server_Core.wsv:928、MCP_Server_VIP.wsv:1096 | COVERED：browser_key_event、browser_vip_key_click |
| 81 | `高级键盘_输入字符` (公开) | "模拟输入单个字，只能输入一个字，可输入中文，VIP高级功能，需赞助后才能使用，向浏览器发送键盘事件，支持后台操作 / 输入文本，可以是中文，但只能输入一个字，否则会出错" | MCP_Server_VIP.wsv:1124 | COVERED：browser_vip_key_input |
| 82 | `逐字分割` (私有) | （无 `注释` 属性；声明原文：`方法 逐字分割`） | **0 hits** | NOT-APPLICABLE：**0 hits**；私有辅助方法（无 `<公开>`），仅被类内 `高级键盘_输入文本` 调用，而后者的工具 `browser_vip_key_type` 已存在 |
| 83 | `高级键盘_输入文本` (公开) | "模拟输入连续的文本，可以是中文，VIP高级功能，需赞助后才能使用，向浏览器发送键盘事件，支持后台操作 / 输入文本，可以是中文，连续的文本" | MCP_Server_VIP.wsv:1147 | COVERED：browser_vip_key_type |
| 84 | `高级_发送鼠标事件` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送鼠标事件，支持后台发送 / type:Type of the mouse event.Allowed Values: mousePressed, mouseReleased, mouseMoved, mouseWheel." | **0 hits** | REACHABLE-INDIRECTLY：其 5 个封装 `高级鼠标_*` 已由 `browser_vip_mouse_press/release`（MCP_Server_VIP.wsv:802/819）与 `browser_mouse_move/wheel/click`（MCP_Server_Core.wsv:883/1348/841）覆盖；本方法本体只剩一条"刻意绕开"的注释说明（MCP_Server.wsv:3187 `// 根因(实测): 内核级鼠标注入(高级鼠标_* → 高级_发送鼠标事件)会让 **CDP 通道整体失效**`） |
| 85 | `高级鼠标_按下` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送鼠标事件，支持后台发送，不占用鼠标" | MCP_Server_VIP.wsv:802 | COVERED：browser_vip_mouse_press |
| 86 | `高级鼠标_放开` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送鼠标事件，支持后台发送，不占用鼠标" | MCP_Server_VIP.wsv:819 | COVERED：browser_vip_mouse_release |
| 87 | `高级鼠标_移动` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送鼠标事件，支持后台发送，不占用鼠标" | MCP_Server_Core.wsv:883、MCP_Server_VIP.wsv:113 | COVERED：browser_mouse_move、browser_vip_mouse_move |
| 88 | `高级鼠标_滚轮滚动` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送鼠标事件，支持后台发送，不占用鼠标" | MCP_Server_Core.wsv:1348、MCP_Server_VIP.wsv:845 | COVERED：browser_mouse_wheel、browser_vip_mouse_wheel |
| 89 | `高级鼠标_单击` (公开) | "VIP高级功能，需赞助后才能使用，向浏览器发送鼠标事件，支持后台发送，不占用鼠标" | MCP_Server_Core.wsv:841、MCP_Server_VIP.wsv:91 | COVERED：browser_mouse_click、browser_vip_mouse_click |
| 90 | `过滤器_修改内容` (公开) | "VIP高级功能，需赞助后才能使用，非VIP用户可通过资源过滤器自行分包处理，此功能更方便更快； / 对目标地址通过匹配目标文本修改内容，在资源加载前设置，浏览器创建后设置，如果\"浏览器_获取资源过滤器\"事件中返回真自定义拦截此设置将不会生效； / 如果同一个目标存在多个需要修改的数据，多次调用本方法即可，但要注意目标地址和匹配模式要保持一致，否则可能会出错 / 地址匹配模式，参考：VIP过滤器地址." | **0 hits** | REACHABLE-INDIRECTLY：`browser_intercept` 的 `modify` 动作覆盖同一用户能力，但项目刻意不走 VIP 过滤器（MCP_Callbacks.wsv:963 `# 手写资源篡改过滤器 — 不依赖VIP官方过滤器, 基于FBrowser资源过滤器(ResponseFilter)事件通道`）。能力差：手写版 url 一律子串匹配、无正则（工具描述原文 MCP_Server.wsv:9687 `url一律按子串匹配, 无正则模式`），而 VIP 有 `VIP过滤器地址.正则匹配`（FBroConst.wsv:606）与 4 种替换模式（FBroConst.wsv:594-597） |
| 91 | `过滤器_取消修改内容` (公开) | "在资源加载前设置，取消当前浏览器设置的对应目标地址的修改内容 / 和之前设置的目标地址一一对应" | **0 hits** | REACHABLE-INDIRECTLY：`browser_intercept` 的 `uncache`/`clear` 覆盖"按 url 撤销"（MCP_Server.wsv:9687 列出 `uncache/clear`）；注意作用域差异 —— VIP 版按控制器（=浏览器）对象隔离，手写版的规则字段是**服务器级全局**（MCP_Server.wsv:361 `变量 资源替换规则 <公开 静态 类型 = 文本型 值 = "" ...>`） |
| 92 | `过滤器_取消全部修改内容` (公开) | "在资源加载前设置，取消当前浏览器设置的对应目标地址的修改内容" | MCP_Server.wsv:8514 | REACHABLE-INDIRECTLY：唯一调用点在维护辅助方法 `清理VIP拦截资源`（MCP_Server.wsv:8514，方法体见 8500-8516），该方法仅被 MCP_Server.wsv:8561 调用，**不是任何工具的分派分支**；对应用户能力由 `browser_intercept action=clear` 提供（MCP_Server_Core.wsv:2452 原文 `返回 (MCP_响应构建.命令成功 (命令ID, "所有拦截规则已清除(手写过滤器通道)"))`） |
| 93 | `过滤器_替换资源_数据` (公开) | "VIP高级功能，需赞助后才能使用，非VIP用户可通过资源处理器自行分包处理，此功能更方便更快； / 用数据直接将整体链接资源替换，在资源加载前设置，也可在浏览器创建后设置，如果\"浏览器_获取资源处理器\"事件中返回真自定义资源此设置将不会生效 / 地址匹配模式，参考：VIP过滤器地址." | **0 hits** | REACHABLE-INDIRECTLY：`browser_intercept action=replace_data` 覆盖（MCP_Server.wsv:9687） |
| 94 | `过滤器_替换资源_文件` (公开) | "VIP高级功能，需赞助后才能使用，非VIP用户可通过资源处理器自行分包处理，此功能更方便更快； / 用本地文件直接将整体链接资源替换，在资源加载前设置，也可在浏览器创建后设置，如果\"浏览器_获取资源处理器\"事件中返回真自定义资源此设置将不会生效 / 地址匹配模式，参考：VIP过滤器地址." | **0 hits** | REACHABLE-INDIRECTLY：`browser_intercept action=replace_file` 覆盖，但项目注明其仅适用于文本类资源（MCP_Callbacks.wsv:966 `# 注: replace_file 经UTF8文本转换, 仅适用于文本类资源(JS/CSS/HTML/JSON等)`），而 VIP 版可替换任意字节集/文件 |
| 95 | `过滤器_取消替换资源` (公开) | "在资源加载前设置，取消当前浏览器设置的对应目标地址的替换资源 / 和之前设置的目标地址一一对应" | **0 hits** | REACHABLE-INDIRECTLY：`browser_intercept action=uncache`（MCP_Server.wsv:9687 列出 `cache/uncache`）覆盖 |
| 96 | `过滤器_取消全部替换资源` (公开) | "在资源加载前设置，取消当前浏览器设置的所有替换的资源" | MCP_Server.wsv:8515 | REACHABLE-INDIRECTLY：同 `过滤器_取消全部修改内容`，唯一调用点在 `清理VIP拦截资源`（MCP_Server.wsv:8515），非工具分支；能力由 `browser_intercept action=clear` 提供 |
| 97 | `高级_创建标签浏览器` (公开) | "VIP高级功能，需赞助后才能使用，谷歌模式下才可以使用， / 在当前谷歌UI界面创建一个新的Tab标签浏览器， / 设置了浏览器事件后即可和创建浏览器一样控制该标签浏览器 / 可以为空，为空会获取当前浏览器的地址" | **0 hits** | **REAL GAP（且属项目政策性拒绝）**：**0 hits**。分发器存在对应分支但**恒定失败** —— MCP_Server_System.wsv:18 原文 `返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 远程创建标签页已禁用 | 原因: 本工具**刻意不实现**(项目未开放远程建标签页入口) ...`；该名仍在命令注册表（MCP_Server.wsv:1141 `命令注册表.置整数值 ("browser_create_tab", 1141)`）但**未登记为工具**。替代品 `browser_create` 是新建独立浏览器窗口，不等价。唯一可能是 `browser_cdp_call` 透传 `Target.createTarget`（**未核实**） |
| 98 | `内核开关_禁用ConsoleDebug` (公开) | "VIP功能，需赞助后才能使用，禁用console.debug功能防止检测到开发者工具 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1693 | COVERED：browser_vip_disable_console |
| 99 | `内核开关_禁用ConsoleWarn` (公开) | "VIP功能，需赞助后才能使用，禁用console.warn功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1691 | COVERED：browser_vip_disable_console |
| 100 | `内核开关_禁用ConsoleError` (公开) | "VIP功能，需赞助后才能使用，禁用console.error功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1692 | COVERED：browser_vip_disable_console |
| 101 | `内核开关_禁用ConsoleInfo` (公开) | "VIP功能，需赞助后才能使用，禁用console.info功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1694 | COVERED：browser_vip_disable_console |
| 102 | `内核开关_禁用ConsoleLog` (公开) | "VIP功能，需赞助后才能使用，禁用console.log功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1690 | COVERED：browser_vip_disable_console |
| 103 | `内核开关_禁用ConsoleAssert` (公开) | "VIP功能，需赞助后才能使用，禁用console.assert功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1697 | COVERED：browser_vip_disable_console |
| 104 | `内核开关_禁用ConsoleDir` (公开) | "VIP功能，需赞助后才能使用，禁用console.dir功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1698 | COVERED：browser_vip_disable_console |
| 105 | `内核开关_禁用ConsoleTable` (公开) | "VIP功能，需赞助后才能使用，禁用console.table功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1699 | COVERED：browser_vip_disable_console |
| 106 | `内核开关_禁用ConsoleGroup` (公开) | "VIP功能，需赞助后才能使用，禁用console.group功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1702 | COVERED：browser_vip_disable_console |
| 107 | `内核开关_禁用ConsoleTime` (公开) | "VIP功能，需赞助后才能使用，禁用console.time功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1700 | COVERED：browser_vip_disable_console |
| 108 | `内核开关_禁用ConsoleProfile` (公开) | "VIP功能，需赞助后才能使用，禁用console.profile功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1703 | COVERED：browser_vip_disable_console |
| 109 | `内核开关_禁用ConsoleCount` (公开) | "VIP功能，需赞助后才能使用，禁用console.count功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1701 | COVERED：browser_vip_disable_console |
| 110 | `内核开关_禁用ConsoleTrace` (公开) | "VIP功能，需赞助后才能使用，禁用console.trace功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1695 | COVERED：browser_vip_disable_console |
| 111 | `内核开关_禁用ConsoleClear` (公开) | "VIP功能，需赞助后才能使用，禁用console.debug功能防止检测到开发者工具，只是禁止该功能的执行返回输出，实际依然可调用 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1696 | COVERED：browser_vip_disable_console |
| 112 | `内核开关_禁用Performance检测` (公开) | "VIP功能需赞助后才可使用，不会直接关闭Performance功能，只会影响now，mark，measure用于检测执行速度的返回值（返回值将变成你所设置的最小值到最大值范围内的一个随机值），防止被探测到在调试网页，打了断点或者hook了函数，原理可自行百度 / 为真为禁用，假为不禁用" | MCP_Server_VIP.wsv:1704 | COVERED：browser_vip_disable_console |
| 113 | `内核开关_设置CSS内核` (公开) | "VIP功能需赞助后才可使用，通过对应的内核版本号，结合谷歌功能关闭对应版本添加或删除的功能，达到模拟对应内核的效果，注意：如使用后出现网页异常说明你设置的内核不兼容当前网页 / 支持设置值为135到116" | MCP_Server_VIP.wsv:1177 | COVERED：browser_vip_set_css_version |
| 114 | `内核开关_设置Web内核` (公开) | "VIP功能需赞助后才可使用，同“内核开关_设置CSS内核”功能，通过版本号关闭和添加浏览器对应功能API，达到模拟对应内核的效果，注意：如使用后出现网页异常说明你设置的内核不兼容当前网页 / 支持设置值为135到116" | MCP_Server_VIP.wsv:1206 | COVERED：browser_vip_set_web_version |
| 115 | `内核开关_设置V8内核` (公开) | "VIP功能需赞助后才可使用，同“内核开关_设置CSS内核”功能，通过版本号关闭和添加浏览器V8对应功能API，达到模拟对应内核的效果，注意：如使用后出现网页异常说明你设置的内核不兼容当前网页 / 支持设置值为135到116" | MCP_Server_VIP.wsv:1235 | COVERED：browser_vip_set_v8_version |
| 116 | `内核开关_禁用Debugger` (公开) | "原名：高级_禁用Debugger，VIP功能，需要赞助后才能使用，禁用当前浏览器的debugger断点功能，禁用后开发者工具断点功能任然可以使用，方便调试 / 为真为禁用，假为不禁用" | MCP_Server.wsv:1758、MCP_Server.wsv:2056（共 4 处） | COVERED：browser_antidetect_presets、browser_vip_disable_debugger；**另有创建时自动应用**（`应用持久配置到浏览器`，MCP_Server.wsv:2013，由 MCP_BrowserEvents.wsv:89 在浏览器创建事件中调用）；调试器族工具入口还会**反向清除**它（`确保Debugger可用`，MCP_Server.wsv:1741-1758） |
| 117 | `内核开关_设置EventIsTrusted` (公开) | "原名：事件_虚拟isTrusted / 是否信任，event.isTrusted 参考资料：https://blog.csdn.net/weixin_39871162/article/details/111605327" | MCP_Server_VIP.wsv:1723 | COVERED：browser_vip_set_is_trusted |

> 判定列中的 `(公开)`/`(私有)` 取自类库声明行是否带 `<公开>` 标记。


## 2. 补充：`FBroVip.wsv` 中另三个 VIP 类

任务指定的权威口径是控制器类，但下列两个类与控制器工具**直接耦合**（`指纹_虚拟UserAgent` 的入参就是 `类_FBrowserVIP_UA数据`；`browser_vip_dom_*` 走的是 `类_FBrowserVIP_开发者DOM`），故一并审计。**注意**：`是否为空`/`置空`/`创建`/`取地址`/`关闭`/`是否相同` 等通用名与全库其它类同名，命中数**不能**静态归属到这些类，故一律按"管道/非本类"处理。

### 2.1 `类_FBrowserVIP_UA数据`（FBroVip.wsv:1722-1948）

该类被 `指纹_虚拟UserAgent` 消费（FBroVip.wsv:243-247：`方法 指纹_虚拟UserAgent <公开 注释 = "虚拟用户标识，在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用">` / `参数 userAgent <类型 = 类_FBrowserVIP_UA数据 注释 = "UA数据">`）。

| 方法 | 中文注释（原文引用） | `src/` 调用点 | 判定 |
| --- | --- | --- | --- |
| `是否为空` (公开) | （无 `注释` 属性；声明原文：`方法 是否为空 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`） | 477 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：类管道方法；同名匹配散布全库，无法静态归属到本类 |
| `创建` (公开) | （无 `注释` 属性；声明原文：`方法 创建 <公开>`） | 63 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：类实例构造方法，无需工具 |
| `置UserAgent` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgent，在浏览器创建成功事件中或刷新前调用" | MCP_Server.wsv:2068、MCP_Server_Core.wsv:2340（共 4 处） | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1582）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6929）、`browser_reverse_setup`→`应用持久配置到浏览器`（MCP_Server.wsv:2068） |
| `置AcceptLanguage` (公开) | "VIP指纹功能，需要赞助后才能使用；对应Accept-Language，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6931、MCP_Server_VIP.wsv:1591 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1591）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6931） |
| `置Platform` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.platform，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6930、MCP_Server_VIP.wsv:1586 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1586）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6930） |
| `置HighPlatform` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.platform，在浏览器创建成功事件中或刷新前调用" | MCP_Server_VIP.wsv:1587 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1587，与 `置Platform` 同源写入） |
| `置Brands` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.brands，在浏览器创建成功事件中或刷新前调用 / 双文本第一个值是brand，第二个值是version" | **0 hits** | **REAL GAP**：0 hits。`browser_fingerprint_ua` 的 schema 只列 ua/platform/accept_lang/mobile/architecture/bitness/model/wow64（MCP_Server.wsv:9868），**没有 brands**。理论兜底：`browser_cdp_call` 透传 `Emulation.setUserAgentOverride` 的 `userAgentMetadata.brands`（**未核实**） |
| `置FullVersionList` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.fullVersionList，在浏览器创建成功事件中或刷新前调用 / 双文本第一个值是brand，第二个值是version" | **0 hits** | **REAL GAP**：0 hits；同上，理论兜底 `userAgentMetadata.fullVersionList`（**未核实**） |
| `置FullVersion` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.fullVersion，在浏览器创建成功事件中或刷新前调用" | **0 hits** | **REAL GAP**：0 hits；同上，理论兜底 `userAgentMetadata.fullVersion`（**未核实**） |
| `置PlatformVersion` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.platformVersion，在浏览器创建成功事件中或刷新前调用" | **0 hits** | **REAL GAP**：0 hits；同上，理论兜底 `userAgentMetadata.platformVersion`（**未核实**） |
| `置Architecture` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.architecture，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6933、MCP_Server_VIP.wsv:1595 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1595）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6933） |
| `置Model` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.model，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6935、MCP_Server_VIP.wsv:1603 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1603）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6935） |
| `置Mobile` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.mobile，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6932、MCP_Server_VIP.wsv:1605 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1605）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6932） |
| `置Bitness` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.bitness，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6934、MCP_Server_VIP.wsv:1599 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1599）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6934） |
| `置Wow64` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.wow64，在浏览器创建成功事件中或刷新前调用" | MCP_Server_Core.wsv:6936、MCP_Server_VIP.wsv:1606 | COVERED：`browser_fingerprint_ua`（MCP_Server_VIP.wsv:1606）、`browser_antidetect_presets`（MCP_Server_Core.wsv:6936） |
| `置FormFactors` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.formFactors，在浏览器创建成功事件中或刷新前调用" | **0 hits** | **REAL GAP**：0 hits；CDP `userAgentMetadata` 结构体通常不含 formFactors，故可能**连 CDP 兜底也没有**（未能静态确定，见第 5 节） |
| `取UserAgent` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgent，在浏览器创建成功事件中或刷新前调用" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取AcceptLanguage` (公开) | "VIP指纹功能，需要赞助后才能使用；对应Accept-Language，在浏览器创建成功事件中或刷新前调用 / acceptLanguage" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Platform` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.platform，在浏览器创建成功事件中或刷新前调用" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取HighPlatform` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.platform，在浏览器创建成功事件中或刷新前调用" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Brands` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.brands，在浏览器创建成功事件中或刷新前调用" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取FullVersionList` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.fullVersionList，在浏览器创建成功事件中或刷新前调用 / fullVersionList" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取FullVersion` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.fullVersion，在浏览器创建成功事件中或刷新前调用 / fullVersion" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取PlatformVersion` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.platformVersion，在浏览器创建成功事件中或刷新前调用 / platformVersion" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Architecture` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.architecture，在浏览器创建成功事件中或刷新前调用 / architecture" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Model` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.model，在浏览器创建成功事件中或刷新前调用 / model" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Mobile` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.mobile，在浏览器创建成功事件中或刷新前调用 / mobile" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Bitness` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.bitness，在浏览器创建成功事件中或刷新前调用 / bitness" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取Wow64` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.wow64，在浏览器创建成功事件中或刷新前调用" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |
| `取FormFactors` (公开) | "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.formFactors，在浏览器创建成功事件中或刷新前调用 / formFactors" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；但"校验伪装是否生效"这一用途可由 `browser_evaluate` 直读 `navigator.userAgentData.*`（读页面实时值，比类库内部回读更贴近实际效果） |

### 2.2 `类_FBrowserVIP_开发者DOM`（FBroVip.wsv:1466-1721）

| 方法 | 中文注释（原文引用） | `src/` 调用点 | 判定 |
| --- | --- | --- | --- |
| `是否为空` (公开) | "为空返回真，不为空返回假" | 477 处同名匹配（无法静态归属） | NOT-APPLICABLE：类管道方法 |
| `置空` (公开) | "手动置空当前类包含的cef类指针，置空后该类将无法使用，如没有其他引用将自动释放cef类指针的资源数据" | 5 处同名匹配（无法静态归属） | NOT-APPLICABLE：类管道方法 |
| `启用` (公开) | "Enables DOM agent for the given page. / includeWhitespace:Whether to include whitespaces in the children array of returned Nodes." | MCP_Server_VIP.wsv:1445 | COVERED：`browser_vip_dom_get_document`（MCP_Server_VIP.wsv:1445） |
| `禁用` (公开) | "Enables DOM agent for the given page." | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_cdp_call` 透传 `DOM.disable`（**未核实**） |
| `置焦点元素` (公开) | "focusElement，nodeID必须是Element才会有效,执行失败或者错误信息可在开发者事件中获取" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_fill_focus`（原生聚焦）与 `browser_cdp_call`→`DOM.focus`（**未核实**）可覆盖 |
| `移除节点属性` (公开) | "removeAttribute / 移除节点\"attributes\"中的属性名,使用之前必选先枚举DOM获取到节点ID才会有效,移除属性后，可通过枚举DOM查看是否移除成功 / 执行失败或者错误信息可在开发者事件中获取 / nodeID" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_execute_js` / `browser_dom_set_html` / CDP `DOM.removeAttribute`（**未核实**）可覆盖 |
| `移除节点` (公开) | "removeNode / 移除当前节点已经当前节点下的子节点都会被删除,使用之前必选先枚举DOM获取到节点ID才会有效，不能是根节点, / 执行失败或者错误信息可在开发者事件中获取 / nodeID" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_execute_js` / CDP `DOM.removeNode`（**未核实**）可覆盖 |
| `置节点属性文本` (公开) | "setAttributesAsText / 使用之前必选先枚举DOM获取到节点ID才会有效,执行失败或者错误信息可在开发者事件中获取 / nodeID" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_fill_attr_set` / `browser_execute_js` 可覆盖 |
| `置节点属性值` (公开) | "setAttributeValue / 使用之前必选先枚举DOM获取到节点ID才会有效,执行失败或者错误信息可在开发者事件中获取 / nodeID" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_fill_attr_set` / `browser_execute_js` 可覆盖 |
| `置节点值` (公开) | "setNodeValue / Can only set value of text nodes / 使用之前必选先枚举DOM获取到节点ID才会有效,执行失败或者错误信息可在开发者事件中获取 / nodeID" | **0 hits** | REACHABLE-INDIRECTLY：`browser_dom_set_value` / `browser_execute_js` 可覆盖 |
| `置节点源码` (公开) | "setOuterHTML / 使用之前必选先枚举DOM获取到节点ID才会有效,执行失败或者错误信息可在开发者事件中获取 / nodeID" | **0 hits** | REACHABLE-INDIRECTLY：`browser_dom_set_html`（MCP_Server.wsv:9679）可覆盖 |
| `清除查找` (公开) | "清除通过预查找文本查找的数据，释放资源,执行失败或者错误信息可在开发者事件中获取 / searchId" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_stop_find` 走浏览器自身的停止查找通道 |
| `枚举DOM` (公开) | "getDocument,同步方法不能在事件中使用，否则可能会卡事件造成浏览器异常 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / depth" | MCP_Server_VIP.wsv:1461 | COVERED：`browser_vip_dom_get_document`（MCP_Server_VIP.wsv:1461） |
| `取节点属性` (公开) | "getAttributes,使用之前必选先枚举DOM获取到节点ID才会有效,节点必须是\"nodeType\": 1类型及Element类型 / 同步方法不能在事件中使用，否则可能会卡事件造成浏览器异常 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活；" | **0 hits** | REACHABLE-INDIRECTLY：`browser_dom_query`(attribute 参数) / `browser_fill_attr_get` 可覆盖 |
| `取节点源码` (公开) | "getOuterHTML,使用之前必选先枚举DOM获取到节点ID才会有效 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / nodeId" | **0 hits** | REACHABLE-INDIRECTLY：`browser_dom_inner_html` / `browser_execute_js` 可覆盖 |
| `取节点_查询选择器` (公开) | "querySelector,返回查找出来的节点ID,使用之前必选先枚举DOM获取到节点ID才会有效 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / nodeId" | **0 hits** | REACHABLE-INDIRECTLY：`browser_dom_query` / `browser_execute_js` 可覆盖 |
| `取全部节点_查询选择器` (公开) | "querySelectorAll,返回查找出来的全部节点ID,返回值保存在返回值，使用之前必选先枚举DOM获取到节点ID才会有效 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / nodeId" | **0 hits** | REACHABLE-INDIRECTLY：`browser_execute_js`(querySelectorAll) 可覆盖 |
| `置节点名` (公开) | "返回设置后新节点ID,nodeID必须是Element才会有效,成功将会在回调中返回修改后的新节点ID / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / nodeId" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；`browser_execute_js` 重建节点可近似；CDP `DOM.setNodeName`（**未核实**） |
| `取节点容器` (公开) | "getContainerForNode：根据容器查询条件返回给定节点的容器。如果给定了containerName，它将查找最近的具有匹配名称的容器；否则，它将找到最近的容器，而不管其容器名称。,未测试 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / nodeId" | **0 hits** | REACHABLE-INDIRECTLY：无同名调用；类库注释自称 `未测试`（FBroVip.wsv:1666）；`browser_execute_js` 的 closest() 可近似 |
| `预查找文本` (公开) | "返回数据{\"searchId\":\"4868.1\",\"resultCount\":1} searchId为查找id，resultCount为查找到的数量 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / nodeId" | MCP_Server_VIP.wsv:1495 | COVERED：`browser_vip_dom_search`（MCP_Server_VIP.wsv:1495） |
| `取查找文本` (公开) | "通过\"预查找文本\"的searchId获取到查找的数据,数据存放在\"返回值\"参数中， / 使用之前必选先枚举DOM获取到节点ID才会返回有效的ID值，不然全是0 / 注意：静态回调和动态回调只能设置一个，优先静态回调有效；采用动态回调可实现回调的动态多态操作，更加灵活； / searchId" | MCP_Server_VIP.wsv:1485 | COVERED：`browser_vip_dom_search`（MCP_Server_VIP.wsv:1485） |

### 2.3 `类_FBrowserVIP_WebSocket客户端`（FBroVip.wsv:1363-1465）

类声明原文 FBroVip.wsv:1363：`类 类_FBrowserVIP_WebSocket客户端 <公开 注释 = "只能在渲染进程中执行，VIP功能，需赞助后才能使用">`。本项目是浏览器进程侧服务，且自身已实测记录该族事件不会派发 —— MCP_Server_Core.wsv:3539 原文 `本族事件同属渲染进程事件(渲染_VIP_WebSocket客户端_*), 在本架构下不会被派发, app_render_ws_* **不会产生记录**`。故除管道方法外全部 NOT-APPLICABLE。注：main.wsv:664-736 的 `渲染_VIP_WebSocket客户端_创建/关闭/连接服务器/接收数据/发送数据` 是**事件重写方法**，不是对本类方法的调用。

| 方法 | 中文注释（原文引用） | `src/` 调用点 | 判定 |
| --- | --- | --- | --- |
| `是否为空` (公开) | （无 `注释` 属性；声明原文：`方法 是否为空 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`） | 477 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：类管道方法 |
| `置空` (公开) | "手动置空当前类包含的cef类指针，置空后该类将无法使用，如没有其他引用将自动释放cef类指针的资源数据" | 5 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：类管道方法 |
| `是否相同` (公开) | （无 `注释` 属性；声明原文：`方法 是否相同 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`） | 1 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：同名命中属其它类，非本类调用 |
| `连接` (公开) | （无 `注释` 属性；声明原文：`方法 连接 <公开 @禁止流程检查 = 真>`） | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |
| `关闭` (公开) | （无 `注释` 属性；声明原文：`方法 关闭 <公开 @禁止流程检查 = 真>`） | 2 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：同名命中属其它类，非本类调用 |
| `销毁` (公开) | （无 `注释` 属性；声明原文：`方法 销毁 <公开 @禁止流程检查 = 真>`） | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |
| `取地址` (公开) | "只能在渲染进程中执行" | 44 处同名匹配（无法静态归属到本类） | NOT-APPLICABLE：同名命中属其它类，非本类调用 |
| `取协议` (公开) | "只能在渲染进程中执行" | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |
| `取插件` (公开) | "只能在渲染进程中执行" | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |
| `取数据类型` (公开) | "只能在渲染进程中执行" | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |
| `发送文本` (公开) | "只能在渲染进程中执行" | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |
| `发送数据` (公开) | "只能在渲染进程中执行" | **0 hits** | NOT-APPLICABLE：渲染进程专用（FBroVip.wsv:1363），且本项目实测该族事件不会被派发（MCP_Server_Core.wsv:3539） |

## 3. 创建时设定（CREATION-TIME-ONLY）专项核查 —— 结论：VIP 控制器没有任何一条属于此类

任务要求：若某类方法是"只能在创建浏览器时设定"，必须明确说明而不是当成工具缺口。核查结论与证据如下。

1. **项目的"待创建"握手只传三样东西**，与 VIP 指纹无关。
   - `browser_create` 分派体（MCP_Server_Core.wsv:520-598）只写 `待创建URL`（556 行 `MCP命令服务器.待创建URL = 握手URL`）、`待创建标识`（555 行 `MCP命令服务器.待创建标识 = 标识参数`）、以及后台模式用的 `__BG__` 前缀（540 行 `握手URL = "__BG__" + url`）。
   - UI 线程侧消费（main.wsv:212-231）原文：`FBrowser_创建后台浏览器 (bgUrl, 浏览器配置, , , 浏览器事件, , MCP命令服务器.待创建标识)` / `FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, , , 浏览器事件, , MCP命令服务器.待创建标识)`。
   - 全库检索 `待创建` 只命中上述字段与 `__SHUTDOWN__` 关闭标记（MCP_Server_System.wsv:144），**没有任何 VIP 控制器方法调用**出现在创建路径里。
2. **唯一在"创建时自动应用"的 VIP 调用只有 3 个方法**，且三者都有运行期工具。
   - `方法 应用持久配置到浏览器 <公开 静态 @输出名 = "ApplyPersistentConfigToBrowser" @强制输出 = 真>`（MCP_Server.wsv:2013），由浏览器创建事件回调 `MCP命令服务器.应用持久配置到浏览器 (浏览器)`（MCP_BrowserEvents.wsv:89）与 `browser_reverse_setup`（MCP_Server_Core.wsv:6984）调用。
   - 它内部只调 `内核开关_禁用Debugger`（MCP_Server.wsv:2056）、`指纹_虚拟UserAgent`（MCP_Server.wsv:2069）、`指纹_虚拟Webdriver`（MCP_Server.wsv:2079）；这三个方法同时有运行期工具 `browser_vip_disable_debugger`、`browser_fingerprint_ua`、`browser_antidetect_presets`。故它们是"创建时自动 + 运行期可设"的**双重通路**，不是创建时限定。
3. **类库里确实存在"只能创建时设置"的项，但不是 VIP 控制器方法**：浏览器"用户标识(tag)"。工具自身描述原文（MCP_Server.wsv:9623）`可选: 用户标识(类库只支持**创建时**设置, 无运行期设置接口)`。它属于 `类_FBrowser_浏览器` 的创建参数，不在本次审计的 117 条方法内。
4. **类库对绝大多数 `指纹_*` 的时机要求是"创建成功事件中或刷新前"，即运行期可调**。原文（FBroVip.wsv:225）`方法 指纹_虚拟ProductSub <公开 注释 = "在浏览器创建成功事件中或刷新前调用，此为VIP功能，需赞助后才能使用">`；项目也正是这样用的（如 `vip_ctrl.指纹_虚拟Webglvendor (val)`，MCP_Server_Core.wsv:2365，并统一以 `MCP_响应构建.响应_需要刷新 (...)` 要求刷新后生效，如 MCP_Server_VIP.wsv:993）。

## 4. REAL GAP 排名表（按用户价值从高到低）

> 下列全部为**静态分析结论**，**任何一条都未经验证/未编译/未运行**。第 4.1-4.4 属于 `类_FBrowserVIP_UA数据`（控制器 `指纹_虚拟UserAgent` 的入参类），第 4.5 起属于 `类_FBrowserVIP_控制器`；已在每行标注所属类。

### 4.1 `置Brands` —— UA-CH brands（价值最高）

- 类库签名（FBroVip.wsv:1771-1775）：
  - `方法 置Brands <公开 注释 = "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.brands，在浏览器创建成功事件中或刷新前调用">`
  - `参数 brands <类型 = FBrowser_双文本数组 注释 = "双文本第一个值是brand，第二个值是version">`
- 它会新增的能力：让 `navigator.userAgentData.brands` 与已伪装的 `navigator.userAgent` 自洽。现代反爬（Cloudflare/DataDome/Akamai 一类）普遍**交叉校验** UA 字符串与 UA-CH（`brands`/`fullVersionList`/`platformVersion`）。
- 现状风险点：项目已经暴露 8 个 UA 字段（MCP_Server.wsv:9868 的 schema：`ua, platform, accept_lang, mobile, architecture, bitness, model, wow64`），却恰好漏掉 UA-CH 里最常被校验的这几项 —— **只改 UA 字符串而不改 UA-CH，比完全不伪装更容易被识别为自动化**。这是本次审计里价值最高的一条。
- 最小实现草图（**未验证**）：
  1. 工具 schema：在 MCP_Server.wsv:9868 的 `browser_fingerprint_ua` 属性表里追加 4 个可选属性（例：`brands` 文本，取值形如 `"Chromium|143,Google Chrome|143,Not?A_Brand|24"`；也可用 JSON 数组文本）。
  2. 构造 `FBrowser_双文本数组`：`变量 arr <类型 = FBrowser_双文本数组>` → `arr.创建 ()` → 对每个 brand 造一个 `FBrowser_双文本`（字段 `name`/`value`，见 FBroDataType.wsv:778-805）→ `arr.加入成员 (成员)`（FBroDataType.wsv:839-843，底层 `FBroDoubleString_Add`）。**同库既有用例**：MCP_Server.wsv:7507-7521 就在用 `头数组.到数组首 ()` / `取当前位置数据 ()` / `当前头.name` / `当前头.value` 读这种数组，可照抄其字段访问方式。
  3. 分派：在 `browser_fingerprint_ua` 分支（MCP_Server_VIP.wsv:1572-1611）内，紧接着 `ua_data.置Platform (...)` 一带追加 `如果 (brands文本 != "") { ... ua_data.置Brands (arr) }`，位置必须在 `vipUA.指纹_虚拟UserAgent (ua_data)`（MCP_Server_VIP.wsv:1607）**之前**。
  4. ⚠️ **已知坑（需验证）**：项目在多处注明 YYJSON 数组成员嵌套会崩（MCP_Server.wsv:3257-3258 原文 `// touchPoints 是"数组套对象"的嵌套结构, 而本项目实测 YYJSON对象类.加入数组成员/加入成员 嵌套多层会触发 0xC0000005`）。因此 brands 的 **schema 若用"数组套对象"**很可能触雷，建议用**扁平文本**（如 `brand|version,brand|version`）自行切分。
- 理论兜底：`browser_cdp_call` 透传 `Emulation.setUserAgentOverride` 的 `userAgentMetadata.brands`（**未核实**）。

### 4.2 `置FullVersionList` —— UA-CH fullVersionList

- 类库签名（FBroVip.wsv:1777-1781）：`方法 置FullVersionList <公开 注释 = "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.fullVersionList，在浏览器创建成功事件中或刷新前调用">` / `参数 fullVersionList <类型 = FBrowser_双文本数组 注释 = "双文本第一个值是brand，第二个值是version">`
- 新增能力：给出**完整版本号**（`143.0.7499.170`）而非主版本（`143`）。多数 UA-CH 校验会比对 `fullVersionList` 的版本与 UA 字符串里的 `Chrome/xxx` 是否同源。
- 实现草图：与 4.1 完全同构（同一个 `FBrowser_双文本数组` 可复用，仅换成 `ua_data.置FullVersionList (arr)`）。
- 理论兜底：`Emulation.setUserAgentOverride` → `userAgentMetadata.fullVersionList`（**未核实**）。

### 4.3 `置PlatformVersion` —— UA-CH platformVersion

- 类库签名（FBroVip.wsv:1789-1793）：`方法 置PlatformVersion <公开 注释 = "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.platformVersion，在浏览器创建成功事件中或刷新前调用">` / `参数 platformVersion <类型 = 文本型>`
- 新增能力：`navigator.userAgentData.platformVersion`（Windows 上形如 `15.0.0`）。项目已有 `置Platform`/`置HighPlatform`（`Win32`）但没有版本号；`platform="Win32"` + `platformVersion=""` 的组合是 UA-CH 指纹里非常显眼的矛盾。
- 实现草图：纯文本，最省事 —— 在 MCP_Server_VIP.wsv:1589 一带追加 `如果 (...平台版本 != "") { ua_data.置PlatformVersion (...) }`，schema 加一个文本属性即可。
- 理论兜底：`Emulation.setUserAgentOverride` → `userAgentMetadata.platformVersion`（**未核实**）。

### 4.4 `置FullVersion` —— UA-CH fullVersion（单值）

- 类库签名（FBroVip.wsv:1783-1787）：`方法 置FullVersion <公开 注释 = "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.fullVersion，在浏览器创建成功事件中或刷新前调用">` / `参数 fullVersion <类型 = 文本型>`
- 新增能力：`navigator.userAgentData.fullVersion` 单值（部分老脚本只读这个字段）。
- 实现草图：同 4.3，一行文本赋值。
- 理论兜底：`Emulation.setUserAgentOverride` → `userAgentMetadata.fullVersion`（**未核实**）。

### 4.5 `高级_设置触发鼠标触摸事件` —— 鼠标事件转触摸（移动端仿真）

- 类库签名（FBroVip.wsv:623-628）：
  - `方法 高级_设置触发鼠标触摸事件 <公开 注释 = "在浏览器载入完成后调用,VIP功能，需要赞助后才能使用">`
  - `参数 启用 <类型 = 逻辑型>` / `参数 配置 <类型 = 整数 注释 = "默认为0，0为MOBILE模式，1为DESKTOP模式" @默认值 = 0>`
  - 底层：`FBroHsVIPControl_SetEmitTouchEventsForMouse(m_class,@<启用>,@<配置>)`（FBroVip.wsv:627）
- 新增能力：让**普通鼠标输入**在页面侧产生 touch 事件。与已有 `browser_fingerprint_touch_enable` / `browser_vip_touch_emulation`（底层 `指纹_启用触摸事件` → `FBroHsVIPControl_SetTouchEventEmulationEnabled`，FBroVip.wsv:504）**不是同一个东西**：后者只开启触摸仿真能力与最大触点数，不会把鼠标事件翻译成触摸事件。缺了它，"移动端页面"往往识别出桌面鼠标轨迹，且依赖 touchstart 的交互（滑动验证、地图、轮播）不会响应。
- 现状：**0 hits**，全库连 `触发鼠标`/`EmitTouch` 字样都搜不到。
- 最小实现草图（**未验证**）：
  1. 位置：VIP 族分派器 `MCP_Server_VIP.wsv` 内新开一个分支（与 `browser_vip_touch_emulation` 同一文件、同一风格；可紧邻 MCP_Server_VIP.wsv:1564-1570 的触摸仿真分支）。
  2. 取控制器复用既有范式：`变量 vip_touch <类型 = 类_FBrowserVIP_控制器>` / `vip_touch = MCP命令服务器.取VIP控制器 ()` / `如果 (vip_touch.是否为空 () == 假)`（照抄 MCP_Server_VIP.wsv:1564-1566）。
  3. 调用 `vip_touch.高级_设置触发鼠标触摸事件 (启用, 配置)`，随后按项目惯例返回 `MCP_响应构建.响应_需要刷新 (命令ID, ...)`（范式见 MCP_Server_VIP.wsv:993）。
  4. 注册：在 MCP_Server.wsv 的 VIP 注册段（约 9781-9870，即 `browser_vip_touch_cancel`/`browser_vip_touch_emulation` 一带，MCP_Server.wsv:9835、9866）加一行 `添加工具JSON ("browser_vip_emit_touch_for_mouse", "VIP: 把鼠标事件转为触摸事件(mobile/desktop)", 多属性Schema文本 (属性项JSON ("enable", "boolean", "启用") + "," + 属性项JSON ("configuration", "integer", "0=MOBILE(默认) / 1=DESKTOP"), ""))`，并同步补 `命令注册表.置整数值 ("browser_vip_emit_touch_for_mouse", <分派行号>)`（范式见 MCP_Server.wsv:1148-1149 成对注册 `browser.xxx` / `browser_xxx`）。
- 理论兜底：CDP `Emulation.setEmitTouchEventsForMouse`（参数名与类库注释的 MOBILE/DESKTOP 语义完全对应）经 `browser_cdp_call` 透传（**未核实**）。

### 4.6 `指纹_清空调用计数` —— 指纹探测计数复位

- 类库签名（FBroVip.wsv:211-214）：`方法 指纹_清空调用计数 <公开>`，方法体 `@ if(@<FBrowser初始化控制.是否为VIP> && !IsEmpty()) FBroHsVIPControl_ClearFingerCount(m_class);`
- 新增能力：把"某指纹被读取了多少次"的计数归零。这是一个**反检测审计**能力：先复位，再让页面跑一段，然后用现有的 `browser_fingerprint action=count`（MCP_Server_Core.wsv:2198）读回，就能知道**这一轮**页面探测了哪些指纹维度 —— 现在是"自浏览器创建以来的累计值"，无法区分轮次。
- 现状：**0 hits**（全库搜 `指纹_清空调用计数` 无任何出现），而它的配对读方法有工具。
- 最小实现草图（**未验证**）：在 MCP_Server_Core.wsv:2196-2199 的 `action == "count"` 分支旁加一个 `否则 (action == "count_clear")` 分支，体为 `vip_ctrl.指纹_清空调用计数 ()` + `返回 (MCP_响应构建.命令成功 (命令ID, "指纹调用计数已复位"))`；并在 MCP_Server.wsv:9686 的 `browser_fingerprint` action 枚举文本里追加 `count_clear`（该枚举是给模型看的描述文本，现为 `canvas_random/webgl_random/audio_random/audio_param/webrtc/geolocation/timezone/ssl/ua/set_batch/count/clear`）。
- 兜底：无。这是类库侧进程内状态，CDP 无法复位（见第 5 节的不确定项：`清理数据` 是否会顺带复位，未能静态确定）。

### 4.7 `高级_创建标签浏览器` —— 同浏览器内新建标签页（**项目已明确拒绝，需先改策略**）

- 类库签名（FBroVip.wsv:1201-1216）：`方法 高级_创建标签浏览器 <公开 注释 = "VIP高级功能，需赞助后才能使用，谷歌模式下才可以使用，" 注释 = "在当前谷歌UI界面创建一个新的Tab标签浏览器，" 注释 = "设置了浏览器事件后即可和创建浏览器一样控制该标签浏览器">`，参数 `地址`、`序号`（默认 -1）、`是否激活`、`额外信息`、`浏览器事件`、`禁用事件`、`标识`；底层 `FBroHsVIPControl_AddTabAt (...)`（FBroVip.wsv:1215）。
- 新增能力：在**同一个浏览器进程/窗口**里开新标签，并可像创建浏览器一样挂完整浏览器事件。现有替代品都不等价：`browser_create` 是**新开独立浏览器窗口**（还可能受 `浏览器实例最大数量` 限制，MCP_Server_Core.wsv:543），`browser_navigate` 会丢弃当前页。
- 现状：**0 hits**；且 MCP_Server_System.wsv:16-19 是**刻意的恒失败分支**（`browser_create_tab`），原文 `⛔ 远程创建标签页已禁用 | 原因: 本工具**刻意不实现**(项目未开放远程建标签页入口)`。名字仍在命令注册表（MCP_Server.wsv:1141）但不在 313 个工具里。
- 最小实现草图（**未验证**，且**必须先由人决定是否推翻现有策略**）：把 MCP_Server_System.wsv:16-19 的恒失败分支改成真实实现 —— 取控制器（`MCP命令服务器.取主浏览器 ()` → `.取VIP控制器 ()`），按 MCP_Server_VIP.wsv:1421-1423 的范式创建事件智能指针（`变量 浏览器事件 <类型 = 类_FBrowser_事件智能指针>` / `浏览器事件.创建 (类_...)`），再调 `高级_创建标签浏览器 (地址, 序号, 是否激活, 额外信息, 浏览器事件, 禁用事件, 标识)`；同时把该名从"命令注册表有、工具表无"补齐为一等工具。
- 理论兜底：`browser_cdp_call` 透传 `Target.createTarget`（**未核实**；项目 CDP 是经 DevTools 消息观察者附着到单个浏览器，能否新建 target 未知）。

### 4.8 `高级_执行JS_主框架` —— 指定"主框架"执行 JS

- 类库签名（FBroVip.wsv:800-819）：`方法 高级_执行JS_主框架 <公开 注释 = "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，在主框架/顶级框架执行JS">`，参数 `JS文本`、`包含命令行API`、`静默`、`用户手势`、`超时`、`禁用断点`、`repl模式`、`通用回调`；底层走 `FBroHsVIPControl_RuntimeEvaluate_FrameID(...,1,0,"",...)`（FBroVip.wsv:818，模式位 1=主框架、2=全部框架、3=按序号）。
- 新增能力：无需知道 contextId 就定位主框架；现有 `browser_vip_execute_js_context`（MCP_Server_VIP.wsv:1405-1437）只有 `context_id` 与 `frame_id`，主框架语义没暴露。
- 最小实现草图（**未验证**）：在该工具分支里加一个 `mode` 文本参数（`auto`/`main`/`all`/`index`），`main` → `vipCtrl.高级_执行JS_主框架 (jsCode, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)`，回调对象与异步任务 ID 完全复用现有代码（MCP_Server_VIP.wsv:1419-1423），返回也沿用 `MCP命令服务器.命令成功_异步 (...)`（1432 行）。
- 近似兜底：客户端先用 `browser_vip_get_js_env_ids`（MCP_Server_VIP.wsv:282-316，返回 contextId 数组，代码注释 306 行原文 `// 输出完整ID清单(供 browser_vip_execute_js_context 使用)`）取清单，再假定首个为主框架 —— 属未文档化约定，故未按"已覆盖"处理。

### 4.9 `高级_执行JS_全部框架`

- 类库签名（FBroVip.wsv:821-841）：`方法 高级_执行JS_全部框架 <公开 注释 = "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，在当前所有框架里面都执行JS代码，所有框架都会执行一遍，回调会被多次调取">`；底层模式位 2（FBroVip.wsv:839）。
- 新增能力：一次调用把 JS 注入**所有**框架（绕过 iframe 逐个定位的麻烦），这是抓取嵌套 iframe 页面、批量 hook 的常用能力。
- 最小实现草图（**未验证**）：同 4.8 加 `mode=all` → `vipCtrl.高级_执行JS_全部框架 (jsCode, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)`。⚠️ 设计注意：类库注明"回调会被多次调取"（FBroVip.wsv:821），而项目的异步任务模型是"一个 task_id 一个结果"（`生成异步任务ID` + `mcp_result` 查询），需要额外聚合多次回调或改用"只记录最后一次/计数"的返回约定 —— 这一点**未确定**，见第 5 节。
- 近似兜底：客户端对 `browser_vip_get_js_env_ids` 的每个 id 循环调 `browser_vip_execute_js_context`（失去原子语义、且框架没有 JS 上下文时会漏）。

### 4.10 `高级_发送触摸事件` —— 多点/带压力半径的原始触摸事件

- 类库签名（FBroVip.wsv:866-874）：`方法 高级_发送触摸事件 <公开 注释 = "VIP高级功能，需赞助后才能使用，可不启用触摸模式发送触摸事件">`，参数 `类型 <类型 = 整数 注释 = "touchStart=0,touchMove=1,touchCancel=2,touchEnd=3，第一次执行要先touchStart，执行完操作后touchEnd">`、`触摸事件 <类型 = FBrowser_VIP触摸事件>`、`修饰符`。
- `FBrowser_VIP触摸事件` 的完整字段（FBroDataType.wsv:1472-1480）：`横坐标`、`纵坐标`、`横半径 <值 = 1>`、`纵半径 <值 = 1>`、`旋转角度 <值 = 0>`、`压力 <值 = 1>`、`id`。
- 新增能力：多点触控（不同 `id` 的多个触点同时按下）、显式 `radiusX/radiusY/rotationAngle/force`。缺这些，双指缩放、长按压力手势、"触控面积异常=机器人"一类检测过不去。
- 现状：**0 hits**；项目自己的 CDP 触摸派发把参数写死（MCP_Server.wsv:3267 原文 `参文本 = "{\"type\":\"" + 触摸类型 + "\",\"touchPoints\":[{\"x\":" + 到文本 (横坐标) + ",\"y\":" + 到文本 (纵坐标) + ",\"radiusX\":1,\"radiusY\":1,\"force\":1,\"id\":0}]}"`），`browser_touch_press/move/release` 也只调单点封装（MCP_Server_Core.wsv:5300/5333/5366）。
- 最小实现草图（**未验证**，二选一）：
  - **走 VIP**：新增 `browser_vip_touch_dispatch`，参数 `type`(整数→类库枚举)、`x`、`y`、`radius_x`、`radius_y`、`rotation`、`force`、`id`；构造 `变量 触摸事件 <类型 = FBrowser_VIP触摸事件>` 并逐字段赋值（范式见 FBroVip.wsv:880-883 内部实现），再 `vip.高级_发送触摸事件 (类型, 触摸事件, 0)`；注册位置同 4.5。
  - **走 CDP（不破坏会话，推荐）**：把 MCP_Server.wsv:3252-3274 的 `CDP派发触摸点一次` 扩展为接受 radiusX/radiusY/force/id 与"多触点数组"，按其注释的既定做法**纯文本拼接**构造 `touchPoints`（避免 YYJSON 嵌套崩溃，见 MCP_Server.wsv:3257-3258）。
- 理论兜底：`browser_cdp_call` 透传 `Input.dispatchTouchEvent`（**未核实**）。

### 4.11 `高级_执行JS_框架序号`

- 类库签名（FBroVip.wsv:843-864）：`方法 高级_执行JS_框架序号 <公开 ...>` / `参数 框架序号 <类型 = 整数 注释 = "浏览器依次加载框架的序号，一般第一个为主框架，序号从0开始，超出框架个数将会执行失败，" 注释 = "注意这个序号和开发者工具显示的序号和浏览器取出的框架顺序不一定一样">`；底层模式位 3。
- 新增能力：按加载序号定位框架。**注意类库自己就说顺序不可靠**，因此用户价值低。
- 最小实现草图（未验证）：同 4.8 加 `mode=index` + `frame_index` 参数。若要可靠，需要类库之外另行建立"序号→frameId"映射，属额外工作。
- 近似兜底：`browser_vip_get_js_env_ids` 的顺序 + `browser_get_frames`（MCP_Server.wsv:9662 工具）交叉推断，**不可靠**。

### 4.12 `置FormFactors` —— 价值最低

- 类库签名（FBroVip.wsv:1825-1830）：`方法 置FormFactors <公开 注释 = "VIP指纹功能，需要赞助后才能使用；对应navigator.userAgentData.formFactors，在浏览器创建成功事件中或刷新前调用">` / `参数 formFactors <类型 = FBrowser_文本数组>`
- 新增能力：`navigator.userAgentData.formFactors`（桌面浏览器通常该字段**不存在**）。仅对少数严格的 UA-CH 校验有意义；桌面伪装场景下"不设置"往往才是正确行为。
- 最小实现草图（未验证）：用 `FBrowser_文本数组`（`创建()`/`加入成员(文本型)`，FBroDataType.wsv:984/996-1000）+ `ua_data.置FormFactors (arr)`，其余同 4.1 的挂接方式。注意：错误地暴露该字段本身可能成为指纹特征，建议默认不设。

## 5. 明确列出：我无法静态确定的事项

以下都是**本次只读静态分析无法定论**的点。凡在正文里写了"未核实""可能"，根源都在此。

1. **`browser_cdp_call` 能否真的打通我点名的那些 CDP 方法**。所有 CDP 兜底（`Emulation.setEmitTouchEventsForMouse`、`Emulation.setUserAgentOverride`、`Target.createTarget`、`Input.dispatchTouchEvent`、`DOM.*`）都只是"协议上存在该方法"，本项目的 CDP 是经 DevTools 消息观察者附着到单个浏览器的（观察者注册见 MCP_Server.wsv:1599-1601），而项目自己记录了附着切换会永久破坏 CDP 通道（MCP_Server.wsv:1616 一带的失败文案 `本会话不支持切换到 browser_id=... —— 实测切换附着会**永久破坏** CDP 通道(需重启进程才能恢复)`）。**未运行任何命令，故一律标注未核实。**
2. **`清理数据` 是否会顺带复位指纹调用计数**。类库注释只写 `清理全部VIP设置的参数，包括指纹、代理、wss、debugger、isTrusted相关参数数据`（FBroVip.wsv:205），**未提"调用计数"**；底层是 `FBroHsVIPControl_ClearAllData`（FBroVip.wsv:207），其是否包含 `ClearFingerCount` 无从静态判断。若包含，则第 4.6 条的缺口语义要重新表述。
3. **CDP `userAgentMetadata` 是否含 `formFactors`**，决定第 4.12 条是否连理论兜底都没有。
4. **给 brands/fullVersionList 设计 schema 的安全形状**。项目记录过 YYJSON 嵌套数组崩溃（MCP_Server.wsv:3257-3258 的 `0xC0000005` 注释），因此"数组套对象"的 schema 是否可用、还是必须用扁平文本，需要实机验证；本审计无法判定。
5. **`置Brands`/`置FullVersionList`/`置FullVersion`/`置PlatformVersion` 生效时机**：类库统一写"在浏览器创建成功事件中或刷新前调用"，但设置后是否**必须刷新**（以及 UA-CH 是否缓存）静态不可知。
6. **`过滤器_取消全部修改内容`/`过滤器_取消全部替换资源` 到底有没有东西可取消**。全库从未调用 7 个 `过滤器_*` 写方法中的任何一个，因此 MCP_Server.wsv:8514-8515 这两行看起来是在清理一个从未被创建的状态；但类库内部是否会在别处挂 VIP 过滤器，我无法从 `src/` 判定（`src/` 内没有证据）。
7. **手写过滤器的作用域**。我只证明了规则字段是**服务器级全局**（MCP_Server.wsv:360-361 的 `变量 导航拦截规则` / `变量 资源替换规则` 均为 `<公开 静态>`），未逐行追踪 `浏览器_获取资源过滤器` 事件是否按浏览器分流，因此"VIP 过滤器是按浏览器对象隔离、手写版不是"这一差异，只有字段声明层面的证据，没有事件层的完整证据链。
8. **`命令注册表.置整数值 ("名字", N)` 里 N 的确切语义**。我只读到成对写法（MCP_Server.wsv:1148-1149），未验证 N 是分派表下标还是源行号，故第 4 条实现草图里对该参数只写"同步补注册"，未给具体数字。
9. **`指纹_取调用计数` 返回 JSON 的实际结构**。类库只写 `返回类型为一个json文本`（FBroVip.wsv:216），项目直接把它塞进 `构建简单JSON ("count", ...)`（MCP_Server_Core.wsv:2198）；"计数复位后能否用它做差分审计"依赖该 JSON 的具体形状，未验证。
10. **`高级_执行JS_全部框架` 的多回调能否被项目"一个 task_id 一个结果"的异步模型承载**（类库注明"回调会被多次调取"，FBroVip.wsv:821）。这是设计问题，需要先定返回契约。
11. **`是否为空` 的同名匹配是否全部归属正确**。我用 `vip\w*\.是否为空 (` 的前缀启发式得到 87 处 VIP 实例调用；若有命名不含 `vip` 的控制器变量，会被漏计（不影响结论，它本就是管道方法）。
12. **VIP 授权状态对上述所有方法的影响**。类库里几乎每个方法体都以 `if(@<FBrowser初始化控制.是否为VIP> && !IsEmpty())` 开头（例：FBroVip.wsv:627、228、234），即**非 VIP 授权下这些方法静默 no-op**。我未审计授权判定逻辑，也未验证本机授权状态。
13. **313 个工具中是否存在运行期不可达（死注册）的条目**。本审计只顺带发现反例一例：`browser_create_tab` 在 `命令注册表` 内（MCP_Server.wsv:1141）但不在工具表内。系统性的"注册表 vs 工具表"对账未做。
14. **上一轮扫描的结论我一律不作为证据**。只借用了 `_audit\_cg2_cands.json` 的 102 条候选名单做数量对账（第 0.1 节），其判定、`_classlib_gap*.md`、`_cg2_verdict.json` 等均未被引用为依据。

## 6. 附录

### 6.1 判定汇总

| 类别 | `类_FBrowserVIP_控制器`(117) | `类_FBrowserVIP_UA数据`(30) | `类_FBrowserVIP_开发者DOM`(21) | `类_FBrowserVIP_WebSocket客户端`(12) |
| --- | --- | --- | --- | --- |
| COVERED | 95 | 9 | 4 | 0 |
| REACHABLE-INDIRECTLY | 10 | 14（全部 getter） | 15 | 0 |
| **REAL GAP** | **7** | **5** | 0 | 0 |
| NOT-APPLICABLE | 5 | 2 | 2 | 12 |
| CREATION-TIME-ONLY | 0 | 0 | 0 | 0 |

控制器类的 7 个 REAL GAP：`高级_创建标签浏览器`、`高级_发送触摸事件`、`高级_设置触发鼠标触摸事件`、`高级_执行JS_主框架`、`高级_执行JS_全部框架`、`高级_执行JS_框架序号`、`指纹_清空调用计数`。
UA数据类的 5 个 REAL GAP：`置Brands`、`置FullVersionList`、`置FullVersion`、`置PlatformVersion`、`置FormFactors`。
控制器类的 10 个 REACHABLE-INDIRECTLY 全部集中在两族：`过滤器_*`（7 条，走 `browser_intercept` 手写过滤器）与 `高级_发送鼠标/键盘/触摸_单击`（3 条，走各自已暴露的封装或两次工具组合）。

### 6.2 工具清单口径

- 登记处：`MCP_Server.wsv`，形如 `添加工具JSON ("工具名", "描述", <schema>)`；本次统计到 313 处、去重 313 个（无重复名）。
- 与 VIP 控制器直接相关的工具族：`browser_vip_*`（含 `browser_vip_fingerprint_*`）、`browser_fingerprint_*`、`browser_antidetect_presets`、`browser_font_randomize`、`browser_touch_*`、`browser_mouse_*`、`browser_key_event`、`browser_intercept`、`browser_cdp_call`、`browser_reverse_setup`、`browser_evaluate`。
- 公共请求级参数 `browser_id` **不需要**在各自工具 schema 里声明（工具描述原文 MCP_Server.wsv:9626 `browser_id 是请求级公共参数, 无需在单个工具 schema 里声明`）。注意：VIP 族分派器几乎都走 `MCP命令服务器.取VIP控制器 ()`（主浏览器），因此**同一个工具对非主浏览器未必生效** —— 这属于作用域问题，不是本文的"方法缺口"，故未逐条计入判定。
- 通用入口（判定时按任务要求降级处理，不视为 COVERED）：`browser_cdp_call`（完整 CDP 透传，MCP_Server.wsv:9822）、`browser_execute_js` / `browser_evaluate`、`browser_inject`、`browser_intercept` 的 action 参数。

### 6.3 复现本文结论的检索式（PowerShell，只读）

    # 1) 抽出控制器类全部方法名
    $all = Get-Content -LiteralPath '<类库>\FBroVip.wsv' -Encoding UTF8
    $all[174..1360] | Select-String -Pattern '^\s*方法\s+(\S+)'

    # 2) 对每个方法名在全库非备份源码里找真实调用点（注释行需人工剔除）
    Get-ChildItem -LiteralPath '<项目>\src' -Recurse -File -Filter *.wsv |
      Where-Object { $_.Name -notlike '*~vbak*' } |
      Select-String -Pattern ('\.' + [regex]::Escape($方法名) + '\s*\(') -Encoding UTF8

    # 3) 定位覆盖工具：从调用点向上找最近的 方法名 == "xxx" 分支
    #    （action 型分派器再取"分支行→调用行"之间最近的 action == "yyy"）

提醒：读 `.wsv` 必须带 `-Encoding UTF8`，否则 PowerShell 5.1 默认编码下中文正则全部失配（会得到"0 hits"的假结论）。

### 6.4 免责声明

本文全部结论来自静态阅读 `src/*.wsv` 与类库 `FBroVip.wsv`/`FBroDataType.wsv`/`FBroConst.wsv`。**未编译、未启动、未调用任何 MCP 工具、未做任何运行时验证**；第 4 节所有实现草图均为草案，需要主代理另行验证后才可采纳，尤其是 `FBrowser_双文本数组` 的构造（已知 YYJSON 嵌套崩溃风险）与任何依赖 CDP 兜底的路径。
