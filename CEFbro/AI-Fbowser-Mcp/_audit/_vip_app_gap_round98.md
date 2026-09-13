# 类_FBrowserVIP_控制器 / 类_FBrowser_应用事件 —— 类库 ↔ MCP 缺口分诊（round98）

> 纯静态分析报告。**未编译、未调用任何 MCP 工具、未发 HTTP、未启停任何进程。**
> 所有结论均为「源码文本证据」级别，不含任何「已验证 / 已测试」断言。

## 0. 取证口径（先说方法与误差边界）

### 0.1 输入文件（实际打开的路径，均为只读）

| 用途 | 绝对路径 |
|---|---|
| VIP 控制器类库 | `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroVip.wsv` |
| 应用事件类库 | `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroEventControl.wsv` |
| 工具注册表（唯一） | `ROOT\src\MCP_Server.wsv` |
| 核心分派 | `ROOT\src\MCP_Server_Core.wsv` |
| VIP 分派 | `ROOT\src\MCP_Server_VIP.wsv` |
| 系统分派 | `ROOT\src\MCP_Server_System.wsv` |
| 逆向分派 | `ROOT\src\MCP_Server_Reverse.wsv` |
| 启动类 / 初始化事件重写 | `ROOT\src\main.wsv` |
| 浏览器事件重写 | `ROOT\src\MCP_BrowserEvents.wsv` |
| 程序集 HTTP 收尾 | `ROOT\src\MCP_Server_HTTP.wsv` |

> `ROOT` = `C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp`
> **无任何「找不到文件」错误**：上述 10 个路径全部打开成功。类库目录实测含 8 个文件（FBroCallback / FBroConst / FBroDataType / FBroEventControl / FBroHelp / FBroLib / FBroValue / FBroVip）。
> `*.~vbak.wsv` 为备份文件，仅作交叉验证，**不作为判定依据**。

### 0.2 方法抽取规则

- 只取 `^\s{4}方法\s` / `^\s{4}参数\s`（类体内 4 空格缩进）声明行，`#` 开头行、`//` 注释行、`@` 内嵌 C++ 行一律不参与计数。
- 类边界实测：
  - `类 类_FBrowserVIP_控制器` 起于 `FBroVip.wsv:175`，止于 `FBroVip.wsv:1362`（下一顶层类 `类_FBrowserVIP_WebSocket客户端` 起于 `:1363`）。
  - `类 类_FBrowser_应用事件` 起于 `FBroEventControl.wsv:5`，止于 `FBroEventControl.wsv:433`（下一顶层类 `类_FBrowser_浏览器事件` 起于 `:434`）。
- 已实测：`FBroEventControl.wsv` 第 14–231 行中「非注释非空」的行仅 3 行（`:14 {`、`:15 @ _FBRO_SHOW_CLASS_TYPE(...)`、`:16 }`），即该段确为 `类_清理` 的方法体 + 大段 `# @begin/# @end` C++ 内嵌说明，**不存在被漏掉的方法**。

### 0.3 已注册工具清单

在 `MCP_Server.wsv` 中以 `添加工具JSON ("` 精确计数（含超长描述行）：**实测 313 条**，与任务描述的「约 313 个」一致。
另：`MCP_Server.wsv` 中另有 `命令注册表.置整数值 ("...")` 别名表（如 `:1323 browser_vip_fingerprint_ssl`、`:899 browser.fingerprint`），属别名/编号表，**不等于新增工具**，故未计入 313。

### 0.4 「已覆盖」的判定门槛（防误报）

满足以下**任一**才判「已覆盖」，**绝不仅凭工具名与中文方法名相似**：

1. `src\*.wsv` 中 grep 到**该类库方法的直接调用**（`xxx.方法名 (...)`）；或
2. `src\*.wsv` 中有明确等价语义的通道（如 `browser_intercept` 的 action 与类库过滤器语义对应），且给出 `file:line` 原文；或
3. 类库方法自身即「底层实现/私有助手」，其上层封装已被第 1 条命中。

判不准的一律写入「5. 我无法确定的」，不硬判。

---

## 1. 摘要

| 类 | 声明方法数 | 已覆盖 | **候选真缺口** | 不确定（部分覆盖） | 不适用 | 覆盖率（已覆盖/总） |
|---|---|---|---|---|---|---|
| `类_FBrowser_应用事件` | **32** | **30** | **0** | 0 | 2（生命周期方法，非可覆盖事件） | 30/30 = 100% |
| `类_FBrowserVIP_控制器` | **117** | **101** | **11** | 4 | 1（非公开私有助手） | 101/117 ≈ 86.3% |

补充说明：

- `类_FBrowser_应用事件` 的 30 个可覆盖事件，**全部**在 `main.wsv` 的 `类_MCP_初始化事件`（`main.wsv:272`，声明 `基础类 = 类_FBrowser_应用事件`）中被 `@虚拟方法 = 可覆盖` 重写，并多数经 `记录应用监控事件/记录应用事件渲染侧` 汇入 MCP 事件日志；该日志由工具 `browser_event`（`MCP_Server_Core.wsv:4480`）的 `action=event_app_enable / event_all_enable / get / clear`（`MCP_Server_Core.wsv:3621-3625 / 3606-3619 / 3643`）开关与读取。因此该类**无候选真缺口**。
- VIP 控制器的 11 个候选缺口里，有 3 个属于「同一族方法的补充变体」（`高级_执行JS_主框架/全部框架/框架序号`），2 个属于「同族撤销接口」（`过滤器_取消修改内容/取消替换资源`），其余 6 个为独立能力。**没有任何一条是靠名字猜出来的。**

---

## 2. `类_FBrowser_应用事件` 逐方法表（32 行）

依据：`FBroEventControl.wsv:5–433` 抽取声明；覆盖依据统一在 `main.wsv` 的 `类_MCP_初始化事件`（`:272`）内。

| 类库方法（声明行） | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `类_初始化`（FBroEventControl.wsv:7） | 不适用 | 方法体 `@ type_ = InitEventType;`（`:9`）；未标 `@虚拟方法 = 可覆盖` | 基类生命周期钩子，非事件，不需要重写 |
| `类_清理`（FBroEventControl.wsv:13） | 不适用 | 方法体 `@ _FBRO_SHOW_CLASS_TYPE(...)`（`:15`）；未标可覆盖 | 同上 |
| `请求环境初始化完毕`（:232） | 已覆盖 | `main.wsv:465 方法 请求环境初始化完毕 <公开 @虚拟方法 = 可覆盖>` | 事件重写存在；由 `browser_event` 事件通道可观测 |
| `扩展插件_创建成功`（:240） | 已覆盖 | `main.wsv:604 方法 扩展插件_创建成功 <公开 @虚拟方法 = 可覆盖>` | 同上 |
| `扩展插件_创建失败`（:247） | 已覆盖 | `main.wsv:618 方法 扩展插件_创建失败 <公开 @虚拟方法 = 可覆盖>` | 同上 |
| `扩展插件_载入成功`（:256） | 已覆盖 | `main.wsv:636 方法 扩展插件_载入成功 <公开 @虚拟方法 = 可覆盖>` | 同上 |
| `扩展插件_卸载成功`（:263） | 已覆盖 | `main.wsv:650 方法 扩展插件_卸载成功 <公开 @虚拟方法 = 可覆盖>` | 同上 |
| `获取默认事件`（:272） | 已覆盖 | `main.wsv:795 方法 获取默认事件 <公开 @虚拟方法 = 可覆盖>`，体内 `:805 默认事件指针.创建 (类_MCP_浏览器事件)` `:806 用户额外配置.置事件 (默认事件指针)` | **实质性重写**：把 MCP 的浏览器事件类挂到每个默认浏览器上 |
| `执行关闭完毕`（:282） | 已覆盖 | `main.wsv:311 方法 执行关闭完毕 <公开 @虚拟方法 = 可覆盖>`，体内 `:315 是否结束程序.值 = 真` | 实质性重写（关闭时结束进程） |
| `即将处理命令行`（:290） | 已覆盖 | `main.wsv:475 方法 即将处理命令行 <公开 @虚拟方法 = 可覆盖>`，体内 `:486 记录应用监控事件 ("app_startup_cmdline", ...)` | 汇入应用事件日志 |
| `注册自定义方案`（:294） | 已覆盖 | `main.wsv:337 方法 注册自定义方案 <公开 @虚拟方法 = 可覆盖>`，体内 `:343 方案.添加自定义方案 ("mcp", 1)` | 实质性重写（注册 `mcp:` scheme） |
| `浏览器_初始化完毕`（:297） | 已覆盖 | `main.wsv:285 方法 浏览器_初始化完毕 <公开 @虚拟方法 = 可覆盖>`，体内 `:287 MCP命令服务器.启动MCP服务器 ()` | **关键路径**：MCP 服务器即由此事件启动 |
| `浏览器_即将启动子进程`（:299） | 已覆盖 | `main.wsv:489 方法 浏览器_即将启动子进程 <公开 @虚拟方法 = 可覆盖>`，体内 `:496 记录应用监控事件 ("app_startup_child_process", "")` | 汇入应用事件日志 |
| `浏览器_即将启动消息调度`（:302） | 已覆盖 | `main.wsv:499 方法 浏览器_即将启动消息调度 <公开 @虚拟方法 = 可覆盖>`，体内 `:509 记录应用监控事件 ("app_startup_message_pump", ...)` | 汇入应用事件日志 |
| `渲染_即将初始化WebKit`（:305） | 已覆盖 | `main.wsv:512 方法 渲染_即将初始化WebKit <公开 @虚拟方法 = 可覆盖>` | 重写存在（渲染进程侧） |
| `渲染_浏览器创建`（:307） | 已覆盖 | `main.wsv:416 方法 渲染_浏览器创建 <公开 @虚拟方法 = 可覆盖>` | 重写存在 |
| `渲染_即将销毁浏览器`（:311） | 已覆盖 | `main.wsv:426 方法 渲染_即将销毁浏览器 <公开 @虚拟方法 = 可覆盖>` | 重写存在 |
| `渲染_即将创建V8环境`（:314） | 已覆盖 | `main.wsv:521 方法 渲染_即将创建V8环境 <公开 @虚拟方法 = 可覆盖>`，体内 `:531 记录应用事件渲染侧 (框架, "app_render_v8_context_created", "")` | 渲染侧事件日志 |
| `渲染_即将释放V8环境`（:319） | 已覆盖 | `main.wsv:388 方法 渲染_即将释放V8环境 <公开 @虚拟方法 = 可覆盖>` | 重写存在 |
| `渲染_即将捕获异常`（:324） | 已覆盖 | `main.wsv:318 方法 渲染_即将捕获异常 <公开 @虚拟方法 = 可覆盖>`，体内 `:327 数据.加入整数成员 ("browser_id", 浏览器.取ID ())` | 实质性重写（上报 JS 异常） |
| `渲染_焦点节点改变`（:331） | 已覆盖 | `main.wsv:347 方法 渲染_焦点节点改变 <公开 @虚拟方法 = 可覆盖>` | 重写存在 |
| `渲染_收到消息`（:336） | 已覆盖 | `main.wsv:534 方法 渲染_收到消息 <公开 @虚拟方法 = 可覆盖>`，体内 `:548 记录应用事件渲染侧 (框架, "app_render_message_received", ...)` | 渲染侧事件日志 |
| `渲染_载入状态被改变`（:345） | 已覆盖 | `main.wsv:553 方法 渲染_载入状态被改变 <公开 @虚拟方法 = 可覆盖>`，体内 `:569 记录应用事件渲染侧_按浏览器 (浏览器, "app_render_loading_state", ...)` | 渲染侧事件日志 |
| `渲染_载入开始`（:351） | 已覆盖 | `main.wsv:572 方法 渲染_载入开始 <公开 @虚拟方法 = 可覆盖>`，体内 `:585 记录应用事件渲染侧 (框架, "app_render_load_start", ...)` | 渲染侧事件日志 |
| `渲染_载入结束`（:356） | 已覆盖 | `main.wsv:588 方法 渲染_载入结束 <公开 @虚拟方法 = 可覆盖>`，体内 `:601 记录应用事件渲染侧 (框架, "app_render_load_end", ...)` | 渲染侧事件日志 |
| `渲染_载入错误`（:361） | 已覆盖 | `main.wsv:400 方法 渲染_载入错误 <公开 @虚拟方法 = 可覆盖>`，参数含 `:403 错误代码` `:405 失败地址` | 重写存在 |
| `进程间消息_收到主进程消息`（:371） | 已覆盖 | `main.wsv:441 方法 进程间消息_收到主进程消息 <公开 @虚拟方法 = 可覆盖>`，体内 `:457 注入代码 = "(function(){var q=window.__mcp_ipc_queue;...` | **实质性重写**：落到 `window.__mcp_ipc_queue`，配合 `browser_ipc_*` 工具 |
| `渲染_VIP_WebSocket客户端_创建`（:380） | 已覆盖 | `main.wsv:664 方法 渲染_VIP_WebSocket客户端_创建 <公开 @虚拟方法 = 可覆盖>`，体内 `:674 记录应用事件渲染侧 (框架, "app_render_ws_created", "")` | 渲染侧 WS 审计 |
| `渲染_VIP_WebSocket客户端_关闭`（:388） | 已覆盖 | `main.wsv:677 方法 渲染_VIP_WebSocket客户端_关闭 <公开 @虚拟方法 = 可覆盖>`，体内 `:687 "app_render_ws_closed"` | 渲染侧 WS 审计 |
| `渲染_VIP_WebSocket客户端_连接服务器`（:398） | 已覆盖 | `main.wsv:690 方法 渲染_VIP_WebSocket客户端_连接服务器 <公开 @虚拟方法 = 可覆盖>`，体内 `:706 "app_render_ws_connect"`；参数含 `url`/`protocols` 可改 | 重写存在（可重定向 WS 地址） |
| `渲染_VIP_WebSocket客户端_接收数据`（:408） | 已覆盖 | `main.wsv:709 方法 渲染_VIP_WebSocket客户端_接收数据 <公开 @虚拟方法 = 可覆盖>`，体内 `:721 "app_render_ws_recv"` | 重写存在 |
| `渲染_VIP_WebSocket客户端_发送数据`（:420） | 已覆盖 | `main.wsv:726 方法 渲染_VIP_WebSocket客户端_发送数据 <公开 @虚拟方法 = 可覆盖>`，体内 `:738 "app_render_ws_send"` | 重写存在 |

**该类小结：候选真缺口 0。** 唯一「弱一点」的是：5 个 WebSocket 客户端事件虽然被重写，但只做了事件记录（`app_render_ws_*`），未在事件里实现「按 URL 选择性阻断/篡改 WS 帧」的策略入口——但这属于**策略层缺口**，不属于「类库方法未暴露」，故不计为候选缺口，仅在此备注。

---

## 3. `类_FBrowserVIP_控制器` 逐方法表（117 行）

### 3.1 基础设施 / 生命周期（3 项）

| 类库方法（声明行） | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `是否为空`（FBroVip.wsv:189） | 已覆盖 | 全项目守卫调用，如 `MCP_Server_VIP.wsv:22 如果 (vip_ctrl.是否为空 () == 假)`、`MCP_Server_Core.wsv:2189` | 基建，无工具语义 |
| `置空`（:194） | 已覆盖 | `MCP_Server.wsv:1614 持久CDP观察者.置空 ()`、`:1809`、`:1848`；`MCP_Server_HTTP.wsv:30 MCP服务器实例.置空 ()` | 基建，无工具语义 |
| `取浏览器`（:199） | **候选缺口** | grep `\.取浏览器 \(\)` 在 `src\*.wsv`（非备份）**0 命中** | 反查方向冗余：已有 `browser_get_main_browser`（`MCP_Server_Core.wsv:5694`）、`browser_get_id`（`:1293`）。优先级最低 |

### 3.2 清理 / 调用计数（3 项）

| 类库方法 | 判定 | 覆盖工具或依据 | 备注 |
|---|---|---|---|
| `清理数据`（:205） | 已覆盖 | 工具 `browser_fingerprint`（`MCP_Server_Core.wsv:2179`）；`MCP_Server_Core.wsv:2193 vip_ctrl.清理数据 ()`（action=clear，`:2191`） | 全量清空 VIP 参数 |
| `指纹_清空调用计数`（:211） | **候选缺口** | grep `指纹_清空调用计数` 0 命中 | 只有「读计数」没有「重置计数」；`browser_fingerprint` 只有 `action=count`（`MCP_Server_Core.wsv:2196-2199`） |
| `指纹_取调用计数`（:216） | 已覆盖 | `MCP_Server_Core.wsv:2198 返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))` | `browser_fingerprint action=count` |

### 3.3 `指纹_虚拟*` 族（51 项）

| 类库方法 | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `指纹_虚拟ProductSub`（:225） | 已覆盖 | `MCP_Server_VIP.wsv:645 vip_ctrl.指纹_虚拟ProductSub (...)`；工具 `browser_fingerprint_product_sub` | |
| `指纹_虚拟Vendor`（:231） | 已覆盖 | `MCP_Server_VIP.wsv:1031 vipProd.指纹_虚拟Vendor (...)`；`MCP_Server_Core.wsv:2347`；工具 `browser_vip_fingerprint_product` | |
| `指纹_虚拟VendorSub`（:237） | 已覆盖 | `MCP_Server_VIP.wsv:662`、`:1032`；工具 `browser_fingerprint_vendor_sub` | |
| `指纹_虚拟UserAgent`（:243） | 已覆盖 | `MCP_Server_VIP.wsv:1629 vipUA.指纹_虚拟UserAgent (ua_data)`；`MCP_Server.wsv:2069`；工具 `browser_fingerprint_ua` | |
| `指纹_虚拟Languages`（:249） | 已覆盖 | `MCP_Server_VIP.wsv:412 vip_ctrl.指纹_虚拟Languages (langText)`（复位用 `:409`）；工具 `browser_fingerprint_languages` | |
| `指纹_虚拟AppCodeName`（:255） | 已覆盖 | `MCP_Server_VIP.wsv:611`；工具 `browser_fingerprint_appcodename` | |
| `指纹_虚拟AppName`（:261） | 已覆盖 | `MCP_Server_VIP.wsv:381`；工具 `browser_fingerprint_appname` | |
| `指纹_虚拟AppVersion`（:267） | 已覆盖 | `MCP_Server_VIP.wsv:628`；工具 `browser_fingerprint_appversion` | |
| `指纹_虚拟Product`（:273） | 已覆盖 | `MCP_Server_VIP.wsv:1029`；`MCP_Server_Core.wsv:2353`；工具 `browser_vip_fingerprint_product` | |
| `指纹_虚拟HardwareConcurrency`（:279） | 已覆盖 | `MCP_Server_VIP.wsv:1017`；`MCP_Server_Core.wsv:2378`、`:6922`；工具 `browser_vip_fingerprint_hardware` | |
| `指纹_虚拟CookieEnabled`（:285） | 已覆盖 | `MCP_Server_VIP.wsv:554`；工具 `browser_fingerprint_cookie_enabled` | |
| `指纹_虚拟DeviceMemory`（:291） | 已覆盖 | `MCP_Server_VIP.wsv:1018`；`MCP_Server_Core.wsv:2384`、`:6923`；工具 `browser_vip_fingerprint_hardware` | |
| `指纹_虚拟Canvas_随机`（:297） | 已覆盖 | `MCP_Server_VIP.wsv:932 canvas随机值 = vipCanvas.指纹_虚拟Canvas_随机 (...)`；`MCP_Server_Core.wsv:2214`、`:6902`；工具 `browser_vip_fingerprint_canvas` | 返回值为随机种子文本 |
| `指纹_虚拟WebGL_随机`（:308） | 已覆盖 | `MCP_Server_VIP.wsv:944`；`MCP_Server_Core.wsv:2231`、`:6903`；工具 `browser_vip_fingerprint_webgl` | |
| `指纹_虚拟Audio_随机`（:318） | 已覆盖 | `MCP_Server_VIP.wsv:956`；`MCP_Server_Core.wsv:2248`、`:6904`；工具 `browser_vip_fingerprint_audio` | |
| `指纹_虚拟Canvas_定值`（:328） | 已覆盖 | `MCP_Server_VIP.wsv:680`；工具 `browser_vip_fingerprint_canvas_fixed` | |
| `指纹_虚拟WebGL_定值`（:334） | 已覆盖 | `MCP_Server_VIP.wsv:697`；工具 `browser_vip_fingerprint_webgl_fixed` | |
| `指纹_虚拟Audio_定值`（:340） | 已覆盖 | `MCP_Server_VIP.wsv:714`；工具 `browser_vip_fingerprint_audio_fixed` | |
| `指纹_虚拟Plugins`（:346） | 已覆盖 | `MCP_Server_VIP.wsv:364`；工具 `browser_fingerprint_plugins` | |
| `指纹_虚拟JavaEnabled`（:353） | 已覆盖 | `MCP_Server_VIP.wsv:571`；工具 `browser_fingerprint_java_enabled` | |
| `指纹_虚拟Webdriver`（:359） | 已覆盖 | `MCP_Server_Core.wsv:2392 vip_ctrl.指纹_虚拟Webdriver (MCP命令服务器.yyjson取逻辑 (配置解析, "webdriver"))`（位于 `:2326 否则 (action == "set_batch")` 分支）；另有 `MCP_Server.wsv:2079` | 无独立工具，作为 `browser_fingerprint` 的 `set_batch.webdriver` 子参数暴露 |
| `指纹_虚拟OnLine`（:365） | 已覆盖 | `MCP_Server_VIP.wsv:593`；工具 `browser_fingerprint_online` | |
| `指纹_虚拟Canvas字体指纹`（:371） | 已覆盖 | `MCP_Server_VIP.wsv:536`、`:980`、`:482`；工具 `browser_vip_fingerprint_canvas_font`、`browser_font_randomize` | |
| `指纹_虚拟CSS字体指纹`（:378） | 已覆盖 | `MCP_Server_VIP.wsv:535 vip_ctrl.指纹_虚拟CSS字体指纹 (frFonts, frW, frH)`、`:967`、`:481`；工具 `browser_vip_fingerprint_font`、`browser_font_randomize` | |
| `指纹_虚拟屏幕XY`（:387） | 已覆盖 | `MCP_Server_VIP.wsv:784`；`MCP_Server_Core.wsv:6918`；工具 `browser_fingerprint_screen_xy` | |
| `指纹_虚拟屏幕分辨率`（:396） | 已覆盖 | `MCP_Server_VIP.wsv:1003`；`MCP_Server_Core.wsv:2401`；工具 `browser_vip_fingerprint_screen` | |
| `指纹_虚拟屏幕可用高度和宽度`（:405） | 已覆盖 | `MCP_Server_VIP.wsv:1004`；`MCP_Server_Core.wsv:2408`；工具 `browser_vip_fingerprint_screen` | |
| `指纹_虚拟屏幕pixelDepth`（:414） | 已覆盖 | `MCP_Server_VIP.wsv:1006`；工具 `browser_vip_fingerprint_screen` | |
| `指纹_虚拟屏幕colorDepth`（:422） | 已覆盖 | `MCP_Server_VIP.wsv:1005`；工具 `browser_vip_fingerprint_screen` | |
| `指纹_虚拟DevicePixelRatio`（:430） | 已覆盖 | `MCP_Server_VIP.wsv:749`；`MCP_Server_Core.wsv:6920`；工具 `browser_fingerprint_pixel_ratio` | |
| `指纹_虚拟Webglvendor`（:438） | 已覆盖 | `MCP_Server_VIP.wsv:438`；`MCP_Server_Core.wsv:2365`；工具 `browser_fingerprint_webgl_vendor` | |
| `指纹_虚拟Webglrenderer`（:446） | 已覆盖 | `MCP_Server_VIP.wsv:441`；`MCP_Server_Core.wsv:2371`；工具 `browser_fingerprint_webgl_vendor` | 与上一行共用同一工具（value2 语义） |
| `指纹_虚拟Rect`（:454） | 已覆盖 | `MCP_Server_VIP.wsv:732`；`MCP_Server_Core.wsv:6919`；工具 `browser_vip_fingerprint_rect` | |
| `指纹_虚拟WebrtcIP`（:465） | 已覆盖 | `MCP_Server_VIP.wsv:859 vip1.指纹_虚拟WebrtcIP (...)`；`MCP_Server_Core.wsv:2295`、`:6939`；工具 `browser_vip_fingerprint_webrtc` | |
| `指纹_虚拟Date时区`（:479） | 已覆盖 | `MCP_Server_VIP.wsv:870`；`MCP_Server_Core.wsv:2309`、`:6925`；工具 `browser_vip_fingerprint_timezone` | |
| `指纹_虚拟Viewport`（:491） | 已覆盖 | `MCP_Server_VIP.wsv:992 vipVP.指纹_虚拟Viewport (top, left, height, width)`（`:991` 注释已按官方签名校正）；工具 `browser_vip_fingerprint_viewport` | |
| `指纹_启用触摸事件`（:500） | 已覆盖 | `MCP_Server_VIP.wsv:766`、`:1566 vipTouch.指纹_启用触摸事件 (...)`；`MCP_Server_Core.wsv:6943`；工具 `browser_fingerprint_touch_enable`（`MCP_Server.wsv:9837`）、`browser_vip_touch_emulation`（`MCP_Server.wsv:9904`） | |
| `指纹_虚拟内核功能`（:508） | **候选缺口** | grep `指纹_虚拟内核功能` 在 `src\*.wsv` **0 命中** | 类库自身标注 **「弃用」**（`:508 注释 = "弃用，VIP功能..."`），且能力已被 `内核开关_设置CSS内核/Web内核/V8内核` 三工具替代（均见下）→ 建议**不做** |
| `指纹_设置SSL加密套件`（:517） | 已覆盖 | `MCP_Server_VIP.wsv:920`；`MCP_Server_Core.wsv:2323`；工具 `browser_vip_fingerprint_ssl`（`MCP_Server.wsv:9885`） | |
| `指纹_虚拟BatteryManagerCharging`（:529） | 已覆盖 | `MCP_Server_VIP.wsv:1043 vipBat.指纹_虚拟BatteryManagerCharging (...)`；工具 `browser_vip_fingerprint_battery`（`MCP_Server.wsv:9894`） | |
| `指纹_虚拟BatteryManagerChargingTime`（:535） | 已覆盖 | `MCP_Server_VIP.wsv:1045`；工具 `browser_vip_fingerprint_battery` | |
| `指纹_虚拟BatteryManagerDischargingTime`（:543） | 已覆盖 | `MCP_Server_VIP.wsv:1046`；工具 `browser_vip_fingerprint_battery` | |
| `指纹_虚拟BatteryManagerLevel`（:551） | 已覆盖 | `MCP_Server_VIP.wsv:1044`；工具 `browser_vip_fingerprint_battery` | |
| `指纹_虚拟AudioInput设备`（:557） | **不确定（部分覆盖）** | `MCP_Server_VIP.wsv:1061 vipMD.指纹_虚拟AudioInput设备 (MCP命令服务器.yyjson取整数 (参数JSON, "type"))`；工具 `browser_vip_fingerprint_media_devices`（`MCP_Server.wsv:9895`） | `类型` 已覆盖；类库第二参 `媒体硬件清单 <类型 = FBrowser_媒体硬件数组 @默认值 = 空对象>`（`:559-561`）**src 未传** → 「添加/覆盖具体硬件明细」这半个能力未暴露 |
| `指纹_虚拟VideoInput设备`（:569） | **不确定（部分覆盖）** | `MCP_Server_VIP.wsv:1069`（同样只传 type）；工具 `browser_vip_fingerprint_media_devices` | 同上，`媒体硬件清单`（`:571-573`）未暴露 |
| `指纹_虚拟AudioOutput设备`（:581） | **不确定（部分覆盖）** | `MCP_Server_VIP.wsv:1065`（同样只传 type）；工具 `browser_vip_fingerprint_media_devices` | 同上，`媒体硬件清单`（`:583-585`）未暴露 |
| `指纹_虚拟定位`（:595） | 已覆盖 | `MCP_Server_VIP.wsv:900 vipGeo.指纹_虚拟定位 (geoLng, geoLat, geoAcc, -10000, -1, -1, -1)`；`MCP_Server_Core.wsv:2304`、`:6941`；工具 `browser_vip_fingerprint_geolocation` | 可选参（海拔/方向/速度）固定用官方默认值 |
| `指纹_虚拟屏幕方向`（:609） | 已覆盖 | `MCP_Server_VIP.wsv:1667 vipOrient.指纹_虚拟屏幕方向 (orient_enum, angle_int)`；工具 `browser_vip_orientation`（`MCP_Server.wsv:9907`） | |

### 3.4 WebSocket / 代理 / 开发者消息 / 截图 / 执行环境（15 项）

| 类库方法 | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `WebSocket_启用拦截`（:617） | 已覆盖 | `MCP_Server_VIP.wsv:30 vip_ctrl.WebSocket_启用拦截 ()`（工具 `browser_vip_websocket_intercept`，`MCP_Server.wsv:9774`）；另一入口 `MCP_Server_Core.wsv:2461`（`browser_intercept action=ws_hook`，`:2451`） | |
| `高级_设置触发鼠标触摸事件`（:623） | **候选缺口** | grep `高级_设置触发鼠标触摸事件` / `SetEmitTouchEventsForMouse` 在 `src\*.wsv` **0 命中** | 独立能力：把真实鼠标事件**转译成触摸事件**，并选 `MOBILE(0)/DESKTOP(1)` 模式（`:625`）。现有 `browser_vip_touch_emulation` 只做 `指纹_启用触摸事件`（开关 + 最大触点数），**不等价** |
| `高级_设置代理`（:630） | 已覆盖 | `MCP_Server_VIP.wsv:60 vip_ctrl.高级_设置代理 (address, ...username, ...password)`；`MCP_Server_Core.wsv:1392`；工具 `browser_set_s5_proxy`（`MCP_Server.wsv:9813`） | 工具未暴露第 4 参 `关闭S5错误提示`（默认假） |
| `高级_清空代理`（:644） | 已覆盖 | `MCP_Server_VIP.wsv:177 vip_ctrl.高级_清空代理 ()`；`MCP_Server_Core.wsv:1425`；工具 `browser_vip_clear_s5_proxy`（`MCP_Server.wsv:9814`） | |
| `开发者消息_发送消息`（:651） | 已覆盖 | `MCP_Server_VIP.wsv:1262 vip_ctrl.开发者消息_发送消息 (devJson)`；工具 `browser_vip_send_devtools_msg`（`MCP_Server.wsv:9844`） | |
| `开发者消息_执行方法`（:682） | 已覆盖 | `MCP_Server.wsv:1645 vip_ctrl.开发者消息_执行方法 (cdpMsgId, cdpMethod, params_dict)`（CDP 通道核心）；工具 `browser_cdp`（`MCP_Server_Core.wsv:4603`）、`browser_cdp_call`（`:4463`） | 被 `browser_reverse_*` 全家共用 |
| `开发者消息_启用监管者事件`（:697） | 已覆盖 | `MCP_Server.wsv:1601 重注册结果 = vip_ctrl.开发者消息_启用监管者事件 (持久CDP观察者)`、`:1798`；工具 `browser_debugger_enable`（`MCP_Server_Core.wsv:5209`）、`browser_vip_enable_devtools_observer` | |
| `开发者消息_关闭监管者事件`（:710） | 已覆盖 | `MCP_Server.wsv:1838 关闭结果 = vip_ctrl.开发者消息_关闭监管者事件 ()`；`MCP_BrowserEvents.wsv:283 closeVip.开发者消息_关闭监管者事件 ()` | 浏览器关闭时自动注销 |
| `高级_网页截图`（:717） | 已覆盖 | `MCP_Server_Core.wsv:2671 vip_ctrl.高级_网页截图 (fmt, 80, 截图大小, 假, 假, 截图回调)`；工具 `browser_screenshot`（`MCP_Server.wsv:9726`） | 质量固定 80；`是否表面/是否包括视窗以外` 固定假 |
| `高级_启用执行环境`（:738） | 已覆盖 | `MCP_Server_VIP.wsv:271 vip_ctrl.高级_启用执行环境 (...)`；工具 `browser_vip_enable_js_env`（`MCP_Server.wsv:9869`） | |
| `高级_取当前环境ID清单`（:745） | 已覆盖 | `MCP_Server_VIP.wsv:293 ids = vip_ctrl.高级_取当前环境ID清单 ()`；工具 `browser_vip_get_js_env_ids`（`MCP_Server.wsv:9870`） | |
| `高级_执行JS`（:753） | 已覆盖 | `MCP_Server_VIP.wsv:1430 vipCtrl.高级_执行JS (jsCode, ctxID, 真, 假, 真, ..., VIPJS回调)`；工具 `browser_vip_execute_js_context`（`MCP_Server.wsv:9900`） | |
| `高级_执行JS_框架ID`（:777） | 已覆盖 | `MCP_Server_VIP.wsv:1426 vipCtrl.高级_执行JS_框架ID (jsCode, frmID, ...)`；工具 `browser_vip_execute_js_context`（同工具 `frame_id` 分支） | |
| `高级_执行JS_主框架`（:800） | **候选缺口** | grep `高级_执行JS_主框架` 在 `src\*.wsv` **0 命中** | 类库实现为 `FBroHsVIPControl_RuntimeEvaluate_FrameID(...,1,0,"",...)`（`:818`）→ **无需先取 contextId 即可在主/顶级框架执行**，省一次 `browser_vip_get_js_env_ids` 往返 |
| `高级_执行JS_全部框架`（:821） | **候选缺口** | grep `高级_执行JS_全部框架` 在 `src\*.wsv` **0 命中** | 一次调用在**当前全部框架**执行同一段 JS，回调被多次触发 → 适合 iframe 大面积探针/埋点，现需先 `browser_get_frames` 再逐个执行 |
| `高级_执行JS_框架序号`（:843） | **候选缺口** | grep `高级_执行JS_框架序号` 在 `src\*.wsv` **0 命中** | 按**框架加载序号**（0 起）执行，与 `框架ID`/`环境ID` 是两套定位方式；类库注释提示序号可能与本项目 `browser_get_frames` 的顺序不一致（`:847`），做之前需先核对 |

### 3.5 触摸 / 键盘 / 鼠标（19 项）

| 类库方法 | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `高级_发送触摸事件`（:866） | 已覆盖（底层） | 类库内部被 `高级触摸_*` 调用，如 `FBroVip.wsv:883 高级_发送触摸事件 (0, 触摸事件, )`；src 用其封装 | 完整 CDP 参数面（`FBrowser_VIP触摸事件` + 修饰符）未单独暴露，见「5. 不确定」 |
| `高级触摸_按下`（:876） | 已覆盖 | `MCP_Server_Core.wsv:5300 vip.高级触摸_按下 (touchX, touchY)`；工具 `browser_touch_press`（`MCP_Server.wsv:9750`） | 缺省走 CDP，`kernel:true` 才走本通道 |
| `高级触摸_放开`（:887） | 已覆盖 | `MCP_Server_Core.wsv:5333 vip.高级触摸_放开 (touchX, touchY)`；工具 `browser_touch_release`（`MCP_Server.wsv:9751`） | |
| `高级触摸_移动`（:898） | 已覆盖 | `MCP_Server_Core.wsv:5366 vip.高级触摸_移动 (touchX, touchY)`；工具 `browser_touch_move`（`MCP_Server.wsv:9752`） | |
| `高级触摸_取消`（:909） | 已覆盖 | `MCP_Server_VIP.wsv:328 vip_ctrl.高级触摸_取消 (...)`；工具 `browser_vip_touch_cancel`（`MCP_Server.wsv:9873`） | 工具描述已明确「会让 CDP 通道失效」 |
| `高级触摸_单击`（:920） | **候选缺口** | grep `高级触摸_单击` 在 `src\*.wsv` **0 命中** | 类库实现 = `高级触摸_按下 → WaitUserTimer(单击延时) → 高级触摸_放开`（`:925-927`）。可用 press+release 组合替代，但**没有单工具** → 低优先 |
| `高级_发送键盘事件`（:932） | 已覆盖（底层） | `FBroVip.wsv:974 高级_发送键盘事件 ("keyDown", ...)`、`:983`、`:1002`（被 `高级键盘_*` 调用）；src 用其封装 | 完整 key 参数面（`code`/`key`/修饰文本…）未单独暴露 |
| `高级键盘_按下`（:969） | 已覆盖 | `MCP_Server_Core.wsv:918 vip_ctrl.高级键盘_按下 (key)`；`MCP_Server_VIP.wsv:136`；工具 `browser_key_event`（`MCP_Server_Core.wsv:897`）、`browser_vip_key_press`（`MCP_Server_VIP.wsv:120`） | |
| `高级键盘_放开`（:978） | 已覆盖 | `MCP_Server_Core.wsv:923`；`MCP_Server_VIP.wsv:159`；工具 `browser_vip_key_release`（`MCP_Server_VIP.wsv:143`） | |
| `高级键盘_单击`（:987） | 已覆盖 | `MCP_Server_Core.wsv:928 vip_ctrl.高级键盘_单击 (key)`；`MCP_Server_VIP.wsv:1096`；工具 `browser_vip_key_click`（`MCP_Server_VIP.wsv:1080`） | |
| `高级键盘_输入字符`（:999） | 已覆盖 | `MCP_Server_VIP.wsv:1124 vip_ctrl.高级键盘_输入字符 (charInput)`；工具 `browser_vip_key_input`（`MCP_Server_VIP.wsv:1103`） | |
| `逐字分割`（:1006） | 不适用 | 无 `<公开>` 修饰 = **类内私有**；仅被 `FBroVip.wsv:1020 逐字分割 (文本, listData)` 调用 | 私有助手，无工具语义 |
| `高级键盘_输入文本`（:1015） | 已覆盖 | `MCP_Server_VIP.wsv:1147 vip_ctrl.高级键盘_输入文本 (typeText)`；工具 `browser_vip_key_type`（`MCP_Server_VIP.wsv:1131`） | 第 2 参 `逐字输入延时` 未暴露（默认 0） |
| `高级_发送鼠标事件`（:1032） | 已覆盖（底层） | `FBroVip.wsv:1081 高级_发送鼠标事件 ("mousePressed", ...)`（被 `高级鼠标_*` 调用）；src 用其封装 | 见「5. 不确定」 |
| `高级鼠标_按下`（:1062） | 已覆盖 | `MCP_Server_VIP.wsv:802 vip_ctrl.高级鼠标_按下 (...)`；工具 `browser_vip_mouse_press`（`MCP_Server_VIP.wsv:792`） | |
| `高级鼠标_放开`（:1084） | 已覆盖 | `MCP_Server_VIP.wsv:819 vip_ctrl.高级鼠标_放开 (...)`；工具 `browser_vip_mouse_release`（`MCP_Server_VIP.wsv:809`） | |
| `高级鼠标_移动`（:1106） | 已覆盖 | `MCP_Server_VIP.wsv:113 vip_ctrl.高级鼠标_移动 (...)`；`MCP_Server_Core.wsv:883`；工具 `browser_vip_mouse_move`、`browser_mouse_move` | |
| `高级鼠标_滚轮滚动`（:1113） | 已覆盖 | `MCP_Server_VIP.wsv:845`；`MCP_Server_Core.wsv:1348`；工具 `browser_vip_mouse_wheel`（`MCP_Server_VIP.wsv:826`）、`browser_mouse_wheel` | |
| `高级鼠标_单击`（:1122） | 已覆盖 | `MCP_Server_VIP.wsv:91 vip_ctrl.高级鼠标_单击 (...)`；`MCP_Server_Core.wsv:841`；工具 `browser_vip_mouse_click`、`browser_mouse_click` | |

### 3.6 过滤器（资源篡改，7 项）

| 类库方法 | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `过滤器_修改内容`（:1134） | 已覆盖（语义等效，非 VIP 通道） | 工具 `browser_intercept`（`MCP_Server_Core.wsv:2426`）`action=modify`：`:2550 MCP命令服务器.添加资源替换规则 (action, url, search_text, replace_text, "", "")` | 走**手写 ResponseFilter**（工具描述原文「不依赖VIP」）。差异：VIP 版支持 `匹配模式`（完全匹配/前缀…）与 `替换模式`（插入/修改），手写版只有 URL 子串匹配 + 纯替换 |
| `过滤器_取消修改内容`（:1147） | **候选缺口** | grep `过滤器_取消修改内容` 在 `src\*.wsv` **0 命中**；`browser_intercept` 的 action 列表（`MCP_Server_Core.wsv:2610`）只有 `clear`（**全清**，`:2434-2449`），**无按 URL 单条撤销** | 真实缺口：只能全清不能撤一条，长会话里改错一条就得重建全部规则 |
| `过滤器_取消全部修改内容`（:1155） | 已覆盖（仅内部清理） | `MCP_Server.wsv:8552 vip_ctrl.过滤器_取消全部修改内容 ()`，位于 `:8538 方法 清理VIP拦截资源`，唯一调用点 `:8599 清理VIP拦截资源 ()`（在 `:8580 方法 关闭MCP服务器` 内） | **无工具入口**，只在服务关闭时执行。注意 `browser_intercept action=clear` 只清手写通道状态（`:2437-2448`），**不清 VIP 过滤器状态** |
| `过滤器_替换资源_数据`（:1162） | 已覆盖（语义等效，非 VIP 通道） | `browser_intercept action=replace_data`：`MCP_Server_Core.wsv:2561 MCP命令服务器.添加资源替换规则 (action, url, "", replace_data_text, "", "")` | `替换的数据 <类型 = 字节集类>` 是**二进制**；手写通道 `:2558` 用 `yyjson取文本`，故**只支持文本体**（工具描述亦写明「需文本类文件」） |
| `过滤器_替换资源_文件`（:1174） | 已覆盖（语义等效，非 VIP 通道） | `browser_intercept action=replace_file`：`MCP_Server_Core.wsv:2582 MCP命令服务器.添加资源替换规则 (action, url, "", "", file_path, "")`（含 `:2575 文件是否存在` 校验） | 同上：文本文件 |
| `过滤器_取消替换资源`（:1186） | **候选缺口** | grep `过滤器_取消替换资源` 在 `src\*.wsv` **0 命中**；`clear` 是全清 | 与 `过滤器_取消修改内容` 同族缺口 |
| `过滤器_取消全部替换资源`（:1194） | 已覆盖（仅内部清理） | `MCP_Server.wsv:8553 vip_ctrl.过滤器_取消全部替换资源 ()`（同一 `清理VIP拦截资源`） | 同「仅内部清理」 |

### 3.7 标签浏览器 / 内核开关（21 项）

| 类库方法 | 判定 | 覆盖工具或依据（file:line 原文） | 备注 |
|---|---|---|---|
| `高级_创建标签浏览器`（:1201） | **候选缺口（项目已刻意禁用）** | `MCP_Server_System.wsv:16 如果 (方法名 == "browser_create_tab")` → `:18 返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 远程创建标签页已禁用 | 原因: 本工具**刻意不实现**..."))` | 工具**已注册但恒返回失败**。类库方法本身可用（`地址/序号/是否激活/额外信息/浏览器事件/标识`），缺的是「谷歌模式下于现有 UI 新建 Tab 并接管」这条真实能力。**是否解除禁用属产品决策，不是技术阻塞** |
| `内核开关_禁用ConsoleDebug`（:1219） | 已覆盖 | `MCP_Server_VIP.wsv:1715 vip.内核开关_禁用ConsoleDebug (...)`；工具 `browser_vip_disable_console`（`MCP_Server.wsv:9881`） | |
| `内核开关_禁用ConsoleWarn`（:1226） | 已覆盖 | `MCP_Server_VIP.wsv:1713`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleError`（:1232） | 已覆盖 | `MCP_Server_VIP.wsv:1714`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleInfo`（:1239） | 已覆盖 | `MCP_Server_VIP.wsv:1716`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleLog`（:1246） | 已覆盖 | `MCP_Server_VIP.wsv:1712`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleAssert`（:1253） | 已覆盖 | `MCP_Server_VIP.wsv:1719`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleDir`（:1260） | 已覆盖 | `MCP_Server_VIP.wsv:1720`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleTable`（:1267） | 已覆盖 | `MCP_Server_VIP.wsv:1721`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleGroup`（:1275） | 已覆盖 | `MCP_Server_VIP.wsv:1724`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleTime`（:1282） | 已覆盖 | `MCP_Server_VIP.wsv:1722`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleProfile`（:1290） | 已覆盖 | `MCP_Server_VIP.wsv:1725`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleCount`（:1297） | 已覆盖 | `MCP_Server_VIP.wsv:1723`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleTrace`（:1304） | 已覆盖 | `MCP_Server_VIP.wsv:1717`；工具 `browser_vip_disable_console` | |
| `内核开关_禁用ConsoleClear`（:1312） | 已覆盖 | `MCP_Server_VIP.wsv:1718`；工具 `browser_vip_disable_console` | 14 个 console.* 全部命中，无遗漏 |
| `内核开关_禁用Performance检测`（:1319） | **不确定（部分覆盖）** | `MCP_Server_VIP.wsv:1726 vip.内核开关_禁用Performance检测 (MCP命令服务器.yyjson取逻辑 (参数JSON, "performance"))`；工具 `browser_vip_disable_console` | 只传第 1 参；`最小值`/`最大值`（默认 0.3/1 毫秒，`:1322-1323`）未暴露。留 0 时由库内部取默认 → **是否等同默认调优，静态无法判定**，见「5.」 |
| `内核开关_设置CSS内核`（:1329） | 已覆盖 | `MCP_Server_VIP.wsv:1177 vip_ctrl.内核开关_设置CSS内核 (cssVer)`；工具 `browser_vip_set_css_version`（`MCP_Server.wsv:9841`） | |
| `内核开关_设置Web内核`（:1336） | 已覆盖 | `MCP_Server_VIP.wsv:1206 vip_ctrl.内核开关_设置Web内核 (webVer)`；工具 `browser_vip_set_web_version` | |
| `内核开关_设置V8内核`（:1342） | 已覆盖 | `MCP_Server_VIP.wsv:1235 vip_ctrl.内核开关_设置V8内核 (v8Ver)`；工具 `browser_vip_set_v8_version` | |
| `内核开关_禁用Debugger`（:1348） | 已覆盖 | `MCP_Server_VIP.wsv:346 vip_ctrl.内核开关_禁用Debugger (...)`；`MCP_Server.wsv:1758 dbgVip.内核开关_禁用Debugger (假)`、`MCP_Server_Core.wsv:6894`；工具 `browser_vip_disable_debugger`（`MCP_Server.wsv:9828`） | |
| `内核开关_设置EventIsTrusted`（:1354） | 已覆盖 | `MCP_Server_VIP.wsv:1745 vp.内核开关_设置EventIsTrusted (...)`；工具 `browser_vip_set_is_trusted`（`MCP_Server.wsv:9872`） | |

---

## 4. 候选真缺口优先级排序（11 项）

排序依据：**`能否被现有工具等价替代` × `能解锁的能力宽度` × `实现成本/风险`**。所有「为什么值得做」只描述能力，**不含实现代码**。

### T1 — `高级_设置触发鼠标触摸事件`（FBroVip.wsv:623）

- 类库签名原文：
  `方法 高级_设置触发鼠标触摸事件 <公开 注释 = "在浏览器载入完成后调用,VIP功能，需要赞助后才能使用">`
  `参数 启用 <类型 = 逻辑型>`
  `参数 配置 <类型 = 整数 注释 = "默认为0，0为MOBILE模式，1为DESKTOP模式" @默认值 = 0>`
- 建议工具名：`browser_vip_mouse_as_touch`
- 归属：`MCP_Server_VIP.wsv` → `类 MCP_VIP分派` / `分类分派_VIP操作`
- 为什么值得做：这是**唯一能把真实鼠标输入翻译成触摸事件**并选择 `MOBILE/DESKTOP` 语义的入口。现有 `browser_vip_touch_emulation` 只调 `指纹_启用触摸事件`（开关 + 最大触点数，`MCP_Server_VIP.wsv:1566`），解决的是「navigator.maxTouchPoints 像不像手机」，**不解决「点击像不像手指」**。对移动端仿真站点、鼠标行为检测（`pointerType`、`touchstart` 事件存在性）是独立且不可替代的能力。

### T2 — `过滤器_取消修改内容`（FBroVip.wsv:1147）

- 类库签名原文：
  `方法 过滤器_取消修改内容 <公开 注释 = "在资源加载前设置，取消当前浏览器设置的对应目标地址的修改内容">`
  `参数 目标地址 <类型 = 文本型 注释 = "和之前设置的目标地址一一对应">`
- 建议工具名：`browser_intercept` 新增 `action=unmodify`（或 `unreplace`）
- 归属：`MCP_Server_Core.wsv` → `类 MCP_核心分派` 的 `browser_intercept` 分支（`:2426`）
- 为什么值得做：现在**只能全清不能撤一条** —— `MCP_Server_Core.wsv:2610` 列出的 action 里只有 `clear`，而 `clear` 是整体清零（`:2444-2448`）。长会话里改错一条 URL 就必须把全部规则推倒重建，这对「边调边试」的逆向/篡改工作流是硬伤。类库已提供按 `目标地址` 精确撤销，成本极低。

### T3 — `过滤器_取消替换资源`（FBroVip.wsv:1186）

- 类库签名原文：
  `方法 过滤器_取消替换资源 <公开 注释 = "在资源加载前设置，取消当前浏览器设置的对应目标地址的替换资源">`
  `参数 目标地址 <类型 = 文本型 注释 = "和之前设置的目标地址一一对应">`
- 建议工具名：与 T2 合并进 `browser_intercept`（`action=unreplace`）
- 归属：同 T2
- 为什么值得做：与 T2 完全同构，只是作用于「整体替换」（`replace_data`/`replace_file` 建立的那一套）。两条一起做才构成完整的「按 URL 增/删」能力，单独做一条仍留半残。

### T4 — `高级_执行JS_全部框架`（FBroVip.wsv:821）

- 类库签名原文：
  `方法 高级_执行JS_全部框架 <公开 注释 = "VIP高级功能，需赞助后才能使用，执行\"VIP_高级_启用执行环境\"启用后生效，在当前所有框架里面都执行JS代码，所有框架都会执行一遍，回调会被多次调取">`
  `参数 JS文本 <类型 = 文本型>` `参数 包含命令行API` `参数 静默` `参数 用户手势` `参数 超时` `参数 禁用断点` `参数 repl模式` `参数 通用回调`
- 建议工具名：`browser_vip_execute_js_all_frames`
- 归属：`MCP_Server_VIP.wsv` → `类 MCP_VIP分派`（与 `browser_vip_execute_js_context` 并列）
- 为什么值得做：一次下发即可覆盖**当前全部 iframe/子框架**，且回调按框架多次回收 —— 对「广告 iframe 埋点、多层嵌套框架里的加密函数定位、批量 DOM 探针」是数量级上的效率提升。现有路径必须 `browser_get_frames` → 逐个 `browser_vip_execute_js_context(frame_id=...)`，每帧一次往返；且**框架在遍历期间新增/销毁时会漏帧**。

### T5 — `高级_创建标签浏览器`（FBroVip.wsv:1201）

- 类库签名原文：
  `方法 高级_创建标签浏览器 <公开 注释 = "VIP高级功能，需赞助后才能使用，谷歌模式下才可以使用，" 注释 = "在当前谷歌UI界面创建一个新的Tab标签浏览器，" 注释 = "设置了浏览器事件后即可和创建浏览器一样控制该标签浏览器">`
  `参数 地址 <类型 = 文本型 注释 = "可以为空，为空会获取当前浏览器的地址">`
  `参数 序号 <类型 = 整数 注释 = "UI上需要插入的序号位置，设置为-1为在末尾添加" @默认值 = -1>`
  `参数 是否激活 <类型 = 逻辑型 @默认值 = 假>`
  `参数 额外信息 <类型 = 类_FBrowser_字典值 @默认值 = 空对象>`
  `参数 浏览器事件 <类型 = 类_FBrowser_事件智能指针>`
  `参数 禁用事件 <类型 = FBrowser_禁用事件 @默认值 = 空对象>`
  `参数 标识 <类型 = 文本型 @默认值 = "">`
- 建议工具名：复用已注册但恒失败的 `browser_create_tab`（`MCP_Server_System.wsv:16`）
- 归属：需要**产品决策**：要么移除 `MCP_Server_System.wsv:16-19` 的硬失败分支，把实现放到 `MCP_Server_VIP.wsv` / `MCP_Server_System.wsv`；要么在文档里把「禁用」定为最终结论
- 为什么值得做：这是**唯一能在同一 CEF 实例内开新 Tab 并接管它**的入口（`browser_create` 只能另起一个独立浏览器窗口）。多标签场景（同站点多账号、A/B 对比、Cookie 隔离下的同域并行）目前无法实现。注意它需要设置浏览器事件才能被控制，与现有 `类_MCP_浏览器事件` 装配方式一致，不是新技术路线。

### 以下 6 项为低优先，建议**记录在案但不排期**

| 序 | 候选缺口（行号） | 建议工具名 | 归属 | 为什么优先级低 / 为什么仍值得记 |
|---|---|---|---|---|
| T6 | `高级_执行JS_框架序号`（:843） | `browser_vip_execute_js_frame_index` | `MCP_Server_VIP.wsv` / `类 MCP_VIP分派` | 按框架加载序号定位，与 `frame_id` 是两套坐标系，可用于**刷新后 frame_id 变化但序号稳定**的场景。但类库自身注释（`:847`）警告「序号和开发者工具/浏览器取出的框架顺序不一定一致」→ 先要实测对齐，风险高于收益 |
| T7 | `高级_执行JS_主框架`（:800） | `browser_vip_execute_js_top_frame` | 同上 | 省掉「先 `browser_vip_get_js_env_ids` 再用 contextId」的一次往返。但顶层框架在现代 SPA 里往往不是目标框架，收益有限 |
| T8 | `高级触摸_单击`（:920） | `browser_vip_touch_click` | 同上 | 类库实现就是按下 + 延时 + 放开（`:925-927`），现有 `browser_touch_press` + `browser_touch_release` 已可手工组合；仅省一次工具往返 |
| T9 | `指纹_清空调用计数`（:211） | `browser_fingerprint` 新增 `action=count_reset` | `MCP_Server_Core.wsv` / `类 MCP_核心分派` | 只影响「本浏览器指纹被读了几次」这一诊断计数的读数起点。有 `action=count`（`MCP_Server_Core.wsv:2198`）却无法清零，做 A/B 指纹组合对比时读数会互相污染 → 小改动、明确收益，但影响面窄 |
| T10 | `指纹_虚拟内核功能`（:508） | `browser_vip_set_kernel_version` | `MCP_Server_VIP.wsv` / `类 MCP_VIP分派` | **类库自己标了「弃用」**（`:508 注释 = "弃用，VIP功能..."`），能力已被 `browser_vip_set_css_version` / `set_web_version` / `set_v8_version` 三联替代（三者均已覆盖）。**建议不做**，仅因「类库有而 MCP 无」而列出 |
| T11 | `取浏览器`（:199） | 不建议新增工具 | — | 反查方向冗余：`browser_get_main_browser`（`MCP_Server_Core.wsv:5694`）、`browser_get_id`（`:1293`）、`browser_list`（`:638`）已覆盖「拿到浏览器对象/身份」的全部需求。**建议判定为不需实现** |

---

## 5. 我无法确定的（4 项 + 3 条相关说明）

> 以下条目**静态分析无法定案**，我不会硬判。每条都给出「用什么办法能定案」。

### U1. `指纹_虚拟AudioInput设备` / `指纹_虚拟VideoInput设备` / `指纹_虚拟AudioOutput设备` 的第二参 `媒体硬件清单` 是否算缺口（FBroVip.wsv:557 / :569 / :581）

- 现状证据：`MCP_Server_VIP.wsv:1061 / :1065 / :1069` **只传了 `type`**；类库第二参为
  `参数 媒体硬件清单 <类型 = FBrowser_媒体硬件数组 注释 = "硬件信息中的驱动ID和分组ID..." @默认值 = 空对象>`
  （`:559-561`），方法体为 `:565 @ if(!@<媒体硬件清单>.IsNullObject()) temp += @<媒体硬件清单>.MapToString();`
  → **传空对象时不会追加任何硬件明细**。
- 为什么不确定：工具描述写的是「type 控制动作(0清空/1添加/2覆盖)」（`MCP_Server.wsv:9895`），工具 schema 也没给 `devices`。参数 `type=1/2`（添加/覆盖）在「清单为空」时由库内部落到什么列表，**只有运行时才能看出**。因此「添加/覆盖硬件明细」这半个能力到底是「未暴露」还是「被空对象静默忽略」，我无法静态判定。
- 定案办法：① 在浏览器里读 `navigator.mediaDevices.enumerateDevices()`，对比 `type=1` 与 `type=2` 的输出差异；② 或按 `FBrowser_媒体硬件数组` 的 JSON 结构补一个 `devices` 参数并观察 enumerateDevices 是否随之改变。任一即可定案。

### U2. `内核开关_禁用Performance检测` 的最小/最大值调优（FBroVip.wsv:1319）

- 现状证据：`MCP_Server_VIP.wsv:1726` 只传第 1 参；类库
  `参数 最小值 <类型 = 小数 ... @默认值 = 0>` `参数 最大值 <类型 = 小数 ... @默认值 = 0>`（`:1322-1323`），且注释写明「默认值0.3，单位毫秒」「默认值1，单位毫秒」。
- 为什么不确定：**@默认值 = 0 与注释里的 0.3/1 自相矛盾** —— 传 0 时到底是「由库内部替换为 0.3/1」还是「真的用 0」？若是后者，则「性能定时噪声」这个反检测能力的实际强度与预期不同。这属于类库语义问题，静态读不到。
- 定案办法：在页面里跑 `performance.now()` 的间隔分布统计（大量采样后看 delta 直方图），对比「不设置」与「设置 disable=true」两种情况，即可判定噪声是否真的注入、区间是否为 0.3–1ms。

### U3. `高级_发送触摸事件` / `高级_发送键盘事件` / `高级_发送鼠标事件`（FBroVip.wsv:866 / :932 / :1032）的完整参数面是否算缺口

- 现状证据：三者都是 `<公开>`，且分别是 `高级触摸_*`（`:883`）、`高级键盘_*`（`:974/:983/:1002`）、`高级鼠标_*`（`:1081`）的底层实现；src 一律使用上层封装，**grep `高级_发送触摸事件|高级_发送键盘事件|高级_发送鼠标事件` 在非备份 `src\*.wsv` 中 0 命中**。
- 为什么不确定：上层封装已经覆盖常规用法；但底层版的完整 CDP 参数面（`FBrowser_VIP触摸事件` 的全部字段、键盘的 `code`/`key`/`windowsVirtualKeyCode`/`isSystemKey`、鼠标的 `clickCount`/`pointerType`）**没有等价工具**。这算不算「真缺口」取决于是否有「需要构造畸形/精细 CDP 输入事件」的用例 —— 而这属于需求判断，不是我能从代码里读出来的。
- 定案办法：确认是否存在「上层封装做不到」的实测用例（例如需要 `pointerType=pen`、需要 `keyIdentifier='U+0041'`）；若有，则判为缺口并给出建议工具名 `browser_vip_input_raw`；若无，判为已覆盖。

### U4. `高级触摸_单击`（:920）到底该不该补

- 现状证据：grep 0 命中，判为候选缺口（已列入 T8）。
- 为什么不确定：`browser_touch_press` + `browser_touch_release` 两个工具串起来在**功能上等价**，缺的只是「一次调用」的便利性与 50ms 默认延时的一致性。这属于「体验缺口」还是「能力缺口」，取决于使用方对往返次数的容忍度。
- 定案办法：统计真实工作流里「tap」动作的调用频率；若高频则补，低频则维持组合用法。

### 相关说明 A：`过滤器_取消全部修改内容` / `过滤器_取消全部替换资源` 的「已覆盖」是弱覆盖

两者在 `src` 里**只有一处调用**，且在服务关闭路径上（`MCP_Server.wsv:8599 清理VIP拦截资源 ()` → `:8552/:8553`）。也就是说：**没有任何工具能让用户在运行期清空 VIP 过滤器状态**。我之所以仍判「已覆盖」，是因为 MCP 从不设置 VIP 过滤器（设置侧走手写通道），所以运行期本来就没有 VIP 过滤器状态可清。**若将来 T2/T3 落地并改成走 VIP 官方过滤器通道，这两条必须同步补上工具入口。**

### 相关说明 B：`browser_intercept action=clear` 与 VIP 过滤器是两套互不干涉的状态

`MCP_Server_Core.wsv:2434-2449` 的 `clear` 只重置 `是否缓存响应 / 是否Hook资源 / 是否Hook导航 / 是否Hook音频 / 是否Hook弹窗 / 资源替换规则 / 导航拦截规则 / 音频指纹配置 / 弹窗配置`；而 VIP 过滤器状态由 `:8552/:8553` 在关闭时释放。**因此「clear 之后过滤器真的干净了」这个直觉是错的**，做 T2/T3 时必须同时理清两套状态，否则会出现「清了还在改」的幽灵现象。

---

## 6. 交付自检

- 交付文件：`ROOT\_audit\_vip_app_gap_round98.md`（本文件，UTF-8 无 BOM，`\n` 行尾）。
- **未修改任何已存在文件**：全程只使用只读操作（`read` / `grep` / `glob` / 只读 `pwsh` 读取），仅新建本文件。
- **未编译、未调用 MCP 工具、未发 HTTP、未启停进程**。
- 计数复核：`类_FBrowser_应用事件` = 32 方法（30 事件 + 2 生命周期）；`类_FBrowserVIP_控制器` = 117 方法；`MCP_Server.wsv` 注册工具 = 313。
- 无「找不到文件」错误。
