# 类库→MCP 缺口逐条复核（第 1 分片）

> 复核人：只读分析子代理（分片 1）。**纯静态交叉核对**：未编译、未运行、未调用任何 MCP/CDP 接口，因此本文**不含**"已实测/已验证"结论；
> 凡涉及运行期行为的判断，均在备注里标明**出处**（项目源码自述 / 类库注释 / 待验证推断）。

## 0. 范围与口径

**范围（本分片独占）**：技能书类库 `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroLib.wsv`（287774 字节 / 5612 行 / mtime 2026-08-28 18:08）中这三个类的**全部方法**：

| 类 | 类库行范围 | 方法数 |
|---|---|---|
| `FBrowser辅助功能` | FBroLib.wsv:377-538 | 18 |
| `类_FBrowser_浏览器` | FBroLib.wsv:539-1462 | 95 |
| `类_FBrowser_基础框架`（`类_FBrowser_框架` 的基类，其方法被框架继承，故一并覆盖） | FBroLib.wsv:1463-1573 | 13 |
| `类_FBrowser_框架` | FBroLib.wsv:1574-1732 | 17 |
| **合计** | | **143** |

**排除（他人负责，本文不涉及）**：菜单/快捷键相关；`FBroVip.wsv`；`FBroEventControl.wsv`；`FBroValue.wsv`/`FBroDataType.wsv`/`FBroCallback.wsv` 的方法。

**判定取值**：`已覆盖`（同名同义工具直接接了该类库方法）／`等价覆盖`（用别的类库方法或 CDP 达到同一能力，**需两步或语义有偏移时在备注中标出**）／`真缺口`／`N/A`（基础设施/回调/枚举/内部辅助，或类库自注不可用于本架构）。

**MCP 工具面基准**：`src/MCP_Server.wsv` 的 `添加工具JSON` 共 **321** 个工具（本次快照**静态计数**：`grep '添加工具JSON ("'` 命中 321 次；注册块在 `MCP_Server.wsv:10829-11184` 一带）。分派分支静态计数：`MCP_Server_Core.wsv`(164) / `MCP_Server_VIP.wsv`(72) / `MCP_Server_Reverse.wsv`(44) / `MCP_Kernel.wsv`(16) / `MCP_Server_Form.wsv`(12) / `MCP_Server_System.wsv`(11) / `MCP_Server_Workflow.wsv`(4)。

### 0.1 行号口径（重要，否则复核会对不上）

本次交叉核对期间**源码正被并发修改**，且部分文件行尾是 `CR CR LF`（CR 数≈2×LF 数）。因此：

1. 行号是**快照值**：快照时刻 = 2026-09-13 12:06。当次快照行数：`MCP_Server_Core.wsv` 8747、`MCP_Server.wsv` 12402（mtime 12:05:47）、`MCP_Server_System.wsv` 483、`MCP_Server_VIP.wsv` 1940、`MCP_Server_Form.wsv` 1412、`MCP_Server_Reverse.wsv` 4952、`MCP_Server_Callbacks.wsv` 3013、`main.wsv` 970、`MCP_BrowserEvents.wsv` 3535、`MCP_Kernel.wsv` 1955。**每行备注都附了锚点原文**（如 `否则 (方法名 == "browser_stop")`），行号漂移后按锚点文本重定位即可。
2. 行号口径统一为 **LF 口径**（= DSH 的 `read` 工具与 `grep`(ripgrep) 报的行号）。原因：`MCP_Server_System.wsv` / `MCP_Server_Form.wsv` / `MCP_Server_Reverse.wsv` / `MCP_Callbacks.wsv` 这四个文件含裸 `CR` 行尾，用 `Select-String`、Python `splitlines()` 等**按 CR 也断行**的工具去读，同一位置会得到约 **2 倍**的行号 —— 例：`MCP_Server_System.wsv` 的 `browser_send_message` 分支，LF 口径是 **25**，Select-String 口径是 **50**（原始字节特征：`offset 46: CR then LF`、`offset 45: CR then <not LF: 13>`，即 `\r\r\n`）。本文所有 `MCP_Server_System.wsv` 行号均已按 LF 口径给出。
3. `MCP_Server_Core.wsv` / `MCP_Server.wsv` / `MCP_Server_VIP.wsv` / `main.wsv` / `MCP_BrowserEvents.wsv` / `MCP_Kernel.wsv` 为纯 LF 文件（CR 计数 0），两种口径一致。

### 0.2 复核方法（可复现）

对 143 个方法逐个做三件事：① 从 `FBroLib.wsv` 取方法声明行（含签名）；② 在 `src`（排除 `*~vbak*` 备份）里检索该方法**是否被真实调用**（模式 `[ .(]方法名 ?(` 与 `.方法名<`）；③ 若有调用点，追到对应的 `否则 (方法名 == "browser_xxx")` 分派分支并取行号；若 0 调用，再判断是否存在**等价路径**（别的类库方法/CDP）。

---

## 1. `FBrowser辅助功能`（18 个方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| FBrowser_Parser_Base64编码 | FBroLib.wsv:379 | 已覆盖 | `browser_base64_encode` ｜ MCP_Server_Core.wsv:5769（调用 :5778 `result = FBrowser_Parser_Base64编码 (data)`） | 1:1 接线 |
| FBrowser_Parser_Base64解码 | FBroLib.wsv:387 | 已覆盖 | `browser_base64_decode` ｜ MCP_Server_Core.wsv:5781（调用 :5790） | 另 `browser_codec`（:5873）内部复用（:5930/:6034） |
| FBrowser_Parser_取数据URI | FBroLib.wsv:394 | 等价覆盖 | `browser_base64_encode` ｜ MCP_Server_Core.wsv:5769 | **无单一工具**；等价路径=调用方自行拼 `"data:<mime>;base64," + base64结果`（两步）。`browser_navigate` 白名单只放行 **image/\*** 的 `data:`（MCP_Server_Core.wsv:117-121 注释）。⚠ 入参是**文本**，纯二进制数据无法经 base64 工具往返（见 §5 不确定点 D1） |
| FBrowser_Parser_URI编码 | FBroLib.wsv:404 | 已覆盖 | `browser_uri_encode` ｜ MCP_Server_Core.wsv:5800（调用 :5812） | `use_plus` 直通类库（FBroLib.wsv:410） |
| FBrowser_Parser_URI解码 | FBroLib.wsv:418 | 已覆盖 | `browser_uri_decode` ｜ MCP_Server_Core.wsv:5815（调用 :5831） | 工具另有页面 `decodeURIComponent` 兜底（:5842），比类库更强 |
| FBrowser_Parser_解析JSON | FBroLib.wsv:433 | N/A | — | 返回 `类_FBrowser_值`，该类**未在工具面暴露**（属基础设施）；MCP 层 JSON 处理一律走 YYJSON。src 中仅 1 处内部使用，不构成代理能力 |
| FBrowser_Parser_字节值解析为JSON | FBroLib.wsv:443 | N/A | — | 同上；src 内 0 调用 |
| FBrowser_Parser_写入JSON | FBroLib.wsv:450 | N/A | — | 同上；src 内 0 调用 |
| FBrowser_清理全局缓存 | FBroLib.wsv:459 | 已覆盖 | `browser_clear_cache` ｜ MCP_Server_Core.wsv:1368（调用 :1375 `FBrowser_清理全局缓存 (, , , 清理缓存回调)`） | 工具描述已声明"影响所有浏览器实例，不只当前页"，与类库语义一致 |
| FBrowser_浏览器_通过ID取浏览器 | FBroLib.wsv:481 | 已覆盖 | `browser_list`（Core:749）／`browser_close{browser_id}`（Core:727）／`browser_is_same`（Core:6871） | 调用点 :767 / :734 / :6884；公共参数 `browser_id` 就是这条路 |
| FBrowser_浏览器_通过序号取浏览器 | FBroLib.wsv:487 | 等价覆盖 | `browser_list` ｜ MCP_Server_Core.wsv:749 | 该库方法 src 内 **0 调用**；等价=用 `browser_list`（内部 `取ID清单` :753）返回的**数组下标即序号**，再用公共参数 `browser_id` 操作（两步，语义一致） |
| FBrowser_浏览器_通过窗口句柄取浏览器 | FBroLib.wsv:494 | 已覆盖 | `browser_find_by_hwnd` ｜ MCP_Server_Core.wsv:7191（调用 :7200） | — |
| FBrowser_浏览器_通过用户标识取浏览器 | FBroLib.wsv:501 | 已覆盖 | `browser_find_by_tag` ｜ MCP_Server_Core.wsv:6746（调用 :6755） | — |
| FBrowser_浏览器_取数量 | FBroLib.wsv:508 | 已覆盖 | `browser_meta` ｜ MCP_Server_Core.wsv:4137（调用 :4147 `browser_count`） | 另有 `ping`（System:188→:193 `browsers`）、`mcp_status`（Core:4779）、`browser_create` 上限守卫（Core:654）、`/health`（MCP_Server_HTTP.wsv:140） |
| FBrowser_浏览器_取ID清单 | FBroLib.wsv:513 | 已覆盖 | `browser_list` ｜ MCP_Server_Core.wsv:749（调用 :753） | — |
| FBrowser_浏览器_取用户标识清单 | FBroLib.wsv:518 | 已覆盖 | `browser_user_tags` ｜ MCP_Server_Core.wsv:7220（调用 :7223） | — |
| 异常收集回调模板函数 | FBroLib.wsv:523 | N/A | — | 仅供 `FBrowser_启用异常收集` 的 `@匹配方法` 使用的**回调签名模板**，不是能力 |
| FBrowser_启用异常收集 | FBroLib.wsv:531 | N/A | — | 类库自注原文：`注释 = "火山版本内置已经设置了，所有这个没用"`（FBroLib.wsv:531）；src 内 0 调用。暴露成工具只会误导 |

---

## 2. `类_FBrowser_浏览器`（95 个方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| FBrowser_创建浏览器 | FBroLib.wsv:553 | 已覆盖 | `browser_create` ｜ MCP_Server_Core.wsv:631 → 握手字段（:661-709）→ main.wsv:258 `FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, , , 浏览器事件, , 待创建标识)` | 创建走"待创建URL 握手 + 主线程时钟"通道（`窗口信息.父窗口句柄 = 0`，main.wsv:235） |
| FBrowser_创建浏览器_同步 | FBroLib.wsv:573 | 等价覆盖 | `browser_create` ｜ MCP_Server_Core.wsv:631 | `_同步` 变体（要求经 `FBrowser_任务运行器_投递任务`，类库 :573 注释）未接线；项目用 UI 线程时钟握手达到同一结果（调用点在 main.wsv:258） |
| FBrowser_创建后台浏览器 | FBroLib.wsv:594 | 已覆盖 | `browser_create {background:true}` ｜ MCP_Server_Core.wsv:631（:643-651 打 `__BG__` 前缀）→ main.wsv:247-256（:251 调用） | 描述与类库注释（无窗口/无句柄/比无头更优）一致 |
| FBrowser_创建后台浏览器_同步 | FBroLib.wsv:615 | 等价覆盖 | `browser_create {background:true}` ｜ MCP_Server_Core.wsv:631 | 同上；`_同步` 变体未接线 |
| 是否为空 | FBroLib.wsv:637 | N/A | — | 空类守卫，src 内 500+ 处作为**前置判空**使用，不是用户能力 |
| 置空 | FBroLib.wsv:642 | N/A | — | 手动置空 CEF 指针的内部操作；src 内 `置空()` 的 5 处均作用于 `持久CDP观察者` 等内部对象，不是浏览器能力入口 |
| 是否已关闭 | FBroLib.wsv:647 | 已覆盖 | `browser_status` ｜ MCP_Server_Core.wsv:4021（字段 :4052 `is_closed`） | — |
| 取用户标识 | FBroLib.wsv:655 | 已覆盖 | `browser_status`（Core:4021→:4048 `user_flag`）／`browser_window_info`（Core:6524→:6538 `user_tag`） | — |
| 可否后退 | FBroLib.wsv:663 | 已覆盖 | `browser_can_navigate` ｜ MCP_Server_Core.wsv:1389（调用 :1398） | 亦在 `browser_status`（:4031）、`browser_loading_info`（:6800 区段） |
| 后退 | FBroLib.wsv:669 | 已覆盖 | `browser_back` ｜ MCP_Server_Core.wsv:193（调用 :203） | — |
| 可否前进 | FBroLib.wsv:675 | 已覆盖 | `browser_can_navigate` ｜ MCP_Server_Core.wsv:1389（调用 :1399） | — |
| 前进 | FBroLib.wsv:681 | 已覆盖 | `browser_forward` ｜ MCP_Server_Core.wsv:218（调用 :227） | — |
| 是否读取中 | FBroLib.wsv:687 | 已覆盖 | `browser_is_loading` ｜ MCP_Server_Core.wsv:1379（调用 :1385） | 亦在 `browser_status`（:4033）、`browser_popup_info`、`browser_loading_info` |
| 重新载入 | FBroLib.wsv:693 | 已覆盖 | `browser_reload` ｜ MCP_Server_Core.wsv:242（调用 :259） | — |
| 重新载入_忽略缓存 | FBroLib.wsv:700 | 已覆盖 | `browser_reload {ignore_cache:true}` ｜ MCP_Server_Core.wsv:242（调用 :255） | — |
| 停止载入 | FBroLib.wsv:707 | 已覆盖 | `browser_stop` ｜ MCP_Server_Core.wsv:273（调用 :279） | ← 该条即主代理交办说明里"台账实测 pass"的例子，本复核结论与之一致 |
| 取ID | FBroLib.wsv:714 | 已覆盖 | `browser_get_id` ｜ MCP_Server_Core.wsv:1404（调用 :1410） | 亦在 `browser_status`（:4035）等 |
| 是否相同 | FBroLib.wsv:722 | 已覆盖 | `browser_is_same` ｜ MCP_Server_Core.wsv:6871（调用 :6887） | — |
| 是否为弹窗 | FBroLib.wsv:730 | 已覆盖 | `browser_popup_info` ｜ MCP_Server_Core.wsv:6497（字段 :6505） | 亦在 `browser_status`（:4029）、`browser_loading_info`、`browser_window_info` |
| 是否有文档 | FBroLib.wsv:736 | 已覆盖 | `browser_status` ｜ MCP_Server_Core.wsv:4021（字段 :4030 `has_document`） | 亦在 `browser_popup_info`（:6506） |
| 取主框架 | FBroLib.wsv:742 | 已覆盖 | 全体主框架工具（`取安全主框架` MCP_Server.wsv:8312）+ `browser_get_frames` ｜ MCP_Server_Core.wsv:1698 | 项目内部统一走 `取安全主框架`（含 8 秒等待），比裸调更稳 |
| 取当前焦点框架 | FBroLib.wsv:749 | 已覆盖 | `browser_get_focused_frame` ｜ MCP_Server_Core.wsv:4083（调用 :4090） | 返回 url/name/frame_id/is_main/is_focused/is_valid |
| 取框架_ID | FBroLib.wsv:757 | 已覆盖 | `browser_frame_by_id` ｜ MCP_Server_Core.wsv:6706（调用 :6724） | 亦被 `browser_get_frames`（:1743）与 `解析框架对象`（MCP_Server.wsv:8795）复用 |
| 取框架_名称 | FBroLib.wsv:764 | 已覆盖 | `browser_frame_by_name` ｜ MCP_Server_Core.wsv:6670（调用 :6683） | 亦被 `解析框架对象`（MCP_Server.wsv:8795 区段）复用 |
| 取框架ID | FBroLib.wsv:771 | 已覆盖 | `browser_get_frames` ｜ MCP_Server_Core.wsv:1698（调用 :1705） | 另 `browser_frame_names`（:6639）、`解析框架对象`（序号路径） |
| 取框架名称 | FBroLib.wsv:779 | 已覆盖 | `browser_frame_names` ｜ MCP_Server_Core.wsv:6639（调用 :6646） | 亦在 `browser_get_frames`（:1707） |
| 关闭浏览器 | FBroLib.wsv:785 | 已覆盖 | `browser_close` ｜ MCP_Server_Core.wsv:727（调用 :744） | ⚠ 语义差异（不是缺口，但需知）：类库注释称会触发 `onbeforeunload`（FBroLib.wsv:786），而工具描述自述"强制关闭，不询问页面"。若代理依赖页面拦截，需按 `browser_close` 的说明处理 |
| 尝试关闭浏览器 | FBroLib.wsv:796 | **真缺口** | 无（`browser_close_try` ｜ MCP_Server_Core.wsv:4058 为**恒失败桩**） | 详见 §4-A3。项目自述：本架构恒返回假（`browser_close` 描述原文 + Core:4058 失败文案），因为类库要求从"顶层窗口关闭处理器"调用。⇒ 全项目**不存在**可被页面否决的优雅关闭路径 |
| 置焦点 | FBroLib.wsv:809 | 已覆盖 | `browser_set_focus` ｜ MCP_Server_Core.wsv:1777（调用 :1789） | 工具要求显式 `focus`（:1779-1782），防缺省误伤 |
| 取窗口句柄 | FBroLib.wsv:817 | 已覆盖 | `browser_get_window_handle` ｜ MCP_Server_Core.wsv:1767（调用 :1773） | 亦在 `browser_status`（:4050）、`browser_window_info`（:6533） |
| 取打开者窗口句柄 | FBroLib.wsv:824 | 已覆盖 | `browser_window_info`（Core:6524→:6535 `opener_hwnd`）／`browser_get_main_browser`（Core:6859→:6866） | — |
| 是否浏览器视图 | FBroLib.wsv:831 | 已覆盖 | `browser_is_view` ｜ MCP_Server_Core.wsv:6893（调用 :6899） | — |
| 取缩放级别 | FBroLib.wsv:838 | 已覆盖 | `browser_get_zoom` ｜ MCP_Server_Core.wsv:1473（调用 :1479） | 亦在 `browser_status`（`zoom_level_pct`） |
| 置缩放级别 | FBroLib.wsv:845 | 已覆盖 | `browser_set_zoom` ｜ MCP_Server_Core.wsv:805（调用 `browser.置缩放级别 (lvNum)`） | 工具加了 0~10 合法域与持久化（:848-855），比类库更严 |
| 开始下载 | FBroLib.wsv:852 | 已覆盖 | `browser_start_download` ｜ MCP_Server_Core.wsv:1556（调用 :1570） | — |
| 下载图片 | FBroLib.wsv:859 | 已覆盖 | `browser_download_image` ｜ MCP_Server_Core.wsv:4108（调用 :4131） | — |
| 打开对话框 | FBroLib.wsv:878 | 等价覆盖 | `browser_file_dialog` ｜ MCP_Server_Core.wsv:6995（:6995-7010 区段） | ⚠ **语义偏移**：类库是 `RunFileDialog` 真弹窗+回调（FBroLib.wsv:896）；工具改为"传 `path` → 校验存在 → 回显"，**刻意不弹窗**（:7001 注释称原生对话框会阻塞控制台）。对无人值守代理等价，但"有人点了对话框"这一能力不存在 |
| 打印 | FBroLib.wsv:901 | 已覆盖 | `browser_print` ｜ MCP_Server_Core.wsv:1097（调用 :1103） | — |
| 打印为PDF | FBroLib.wsv:908 | 已覆盖 | `browser_print_to_pdf` ｜ MCP_Server_Core.wsv:1108（调用 :1146） | — |
| 查找 | FBroLib.wsv:925 | 已覆盖 | `browser_find` ｜ MCP_Server_Core.wsv:863（调用 :873） | 固定 `(text, 真, 假, 假)`＝向前/不区分大小写/不找下一个（:873） |
| 停止查找 | FBroLib.wsv:935 | 已覆盖 | `browser_stop_find` ｜ MCP_Server_Core.wsv:880（调用 :886） | — |
| 打开开发者工具 | FBroLib.wsv:942 | 已覆盖 | `browser_open_devtools` ｜ MCP_Server_Core.wsv:608（调用 :614） | 工具固定 1024x800 等参数，类库的标题/父窗口/坐标参数未暴露（非能力缺失） |
| 关闭开发者工具 | FBroLib.wsv:964 | 已覆盖 | `browser_close_devtools` ｜ MCP_Server_Core.wsv:619（调用 :625） | — |
| 是否为开发者 | FBroLib.wsv:970 | 已覆盖 | `browser_window_info` ｜ MCP_Server_Core.wsv:6524（字段 :6537 `is_devtools`） | — |
| 是否存在开发者工具 | FBroLib.wsv:976 | 已覆盖 | `browser_window_info` ｜ MCP_Server_Core.wsv:6524（字段 :6536 `has_devtools`） | — |
| 发送按键事件 | FBroLib.wsv:982 | 已覆盖 | `browser_key_event` ｜ MCP_Server_Core.wsv:1008（调用 :1071） | 另 `browser_reverse_input_cdp`(kind=key)、VIP `browser_vip_key_*` |
| 发送鼠标点击事件 | FBroLib.wsv:989 | 已覆盖 | `browser_mouse_click` ｜ MCP_Server_Core.wsv:892（调用 :960/:961 按下+抬起） | — |
| 发送鼠标移动事件 | FBroLib.wsv:999 | 已覆盖 | `browser_mouse_move` ｜ MCP_Server_Core.wsv:966（调用 :1002） | — |
| 发送鼠标滚轮事件 | FBroLib.wsv:1007 | 已覆盖 | `browser_mouse_wheel` ｜ MCP_Server_Core.wsv:1415（调用 :1467） | — |
| 发送触摸事件 | FBroLib.wsv:1017 | 等价覆盖 | `browser_touch_press/release/move` ｜ MCP_Server_Core.wsv:6397 / 6430 / 6463 | 默认走 CDP 派发（:6409/:6442/:6475）；`kernel:true` 走 **VIP** `高级触摸_按下/放开/移动`（:6423/:6456/:6489）—— 即内核路径**不是**本方法，属同源替代。类库的 `FBrowser_触摸事件` 结构体参数（多点/半径）未暴露 |
| 置页面静音 | FBroLib.wsv:1024 | 已覆盖 | `browser_set_mute` ｜ MCP_Server_Core.wsv:1077（调用 :1089） | — |
| 是否页面静音 | FBroLib.wsv:1031 | 已覆盖 | `browser_is_muted` ｜ MCP_Server_Core.wsv:1795（调用 :1801） | — |
| 置自动调整大小 | FBroLib.wsv:1038 | 已覆盖 | `browser_set_auto_resize` ｜ MCP_Server_Core.wsv:6951（调用 :6976） | ⚠ 类库声明顺序为 最小高度/最小宽度（FBroLib.wsv:1040-1041，与 CEF `{width,height}` 相反），工具已如实标注该歧义（:6988 区段） |
| 取请求环境 | FBroLib.wsv:1050 | 已覆盖 | `browser_request_context` ｜ MCP_Server_Core.wsv:6777（调用 :6784）+ `browser_cache_dir` ｜ Core:7372（调用 :7379 → :7382 `reqCtx.取缓存路径 ()`） | ⚠ 覆盖面：`browser_request_context` 只回 `has_context`；请求环境的**缓存路径**由 `browser_cache_dir` 给出。环境对象其余成员（独立缓存开关等）未逐项暴露 |
| 移动窗口 | FBroLib.wsv:1058 | 已覆盖 | `browser_move_window` ｜ MCP_Server_Core.wsv:6543（调用 :6589，CDP 回读 bounds 验证） | 类库该方法无返回值，工具用 `Browser.getWindowForTarget` 回读，`verified=false` 不谎报 |
| 显示隐藏窗口 | FBroLib.wsv:1071 | 已覆盖 | `browser_show_window` ｜ MCP_Server_Core.wsv:6904（调用 :6922，回读 GWL_STYLE 的 WS_VISIBLE 位） | 该能力即此前报告确认过的"真缺口已补"，本复核与之一致 |
| 取父窗口句柄 | FBroLib.wsv:1078 | 已覆盖 | `browser_window_info` ｜ MCP_Server_Core.wsv:6524（字段 :6534 `parent_hwnd`） | — |
| 置父窗口 | FBroLib.wsv:1085 | 已覆盖 | `browser_set_parent` ｜ MCP_Server_Core.wsv:6832（调用 :6844） | 工具拒绝 `hwnd=0`（:6764 区段） |
| 置窗口属性 | FBroLib.wsv:1092 | 已覆盖 | `browser_set_window_style` ｜ MCP_Server_System.wsv:127（调用 :145） | ⚠ 工具白名单仅 `GWL_STYLE/GWL_EXSTYLE/GWL_ID`（System:136），类库无限制（任意 GWL 索引）⇒ 覆盖更保守 |
| 取窗口属性 | FBroLib.wsv:1100 | 已覆盖 | `browser_get_window_style` ｜ MCP_Server_System.wsv:117（调用 :123）；亦被 `browser_show_window`（Core:6920/:6924）、`browser_get_run_style`（System:160）使用 | — |
| 取窗口标题 | FBroLib.wsv:1107 | 已覆盖 | `browser_get_window_title` ｜ MCP_Server_Core.wsv:6849；亦在 `browser_status`（:4047）、`browser_window_info`（:6532） | — |
| 进程间消息_发送数据_到全部渲染进程 | FBroLib.wsv:1114 | 已覆盖 | `browser_ipc_send_all` ｜ MCP_Server_Core.wsv:7023（调用 :7037）；`browser_send_message` ｜ MCP_Server_System.wsv:25（调用 :41） | — |
| 进程间消息_发送数据_到指定渲染进程 | FBroLib.wsv:1126 | 已覆盖 | `browser_ipc_send_to` ｜ MCP_Server_Core.wsv:7042（调用 :7062） | 目标进程号由 `browser_ipc_renderer_ids` 提供 |
| 进程间消息_取渲染进程数量 | FBroLib.wsv:1137 | 等价覆盖 | `browser_ipc_renderer_count` ｜ MCP_Server_Core.wsv:7067 | 实现是取 ID 清单再 `取成员数()`（:7074 调用 `进程间消息_取渲染进程ID清单`），未调本方法但结果等价 |
| 进程间消息_取渲染进程ID清单 | FBroLib.wsv:1142 | 已覆盖 | `browser_ipc_renderer_ids` ｜ MCP_Server_Core.wsv:7079（调用 :7074 同一族） | — |
| 进程间消息_发送数据_到主进程 | FBroLib.wsv:1150 | N/A | — | 类库自注（FBroLib.wsv:1150 区段）："在渲染进程中执行,失败返回0"。本 MCP 服务运行在**主进程**（`browser_get_process_type` 即为此暴露），调用恒失败 ⇒ 不是缺口；反方向两条已覆盖 |
| 离屏渲染_离屏渲染被禁用 | FBroLib.wsv:1160 | N/A | — | 见 §5 不确定点 D2：本类 17 个 `离屏渲染_*` 只对**无窗口(OSR)渲染**的浏览器有意义；项目创建路径（main.wsv:233-258）未设置 `浏览器配置.无窗口渲染`，且现有窗口可见性/截图均有其它通路，暴露成工具在当前架构下是死面 |
| 离屏渲染_通知已被调整大小 | FBroLib.wsv:1166 | N/A | — | 同上 |
| 离屏渲染_通知已被隐藏 | FBroLib.wsv:1174 | N/A | — | 同上 |
| 离屏渲染_通知屏幕信息被改变 | FBroLib.wsv:1183 | N/A | — | 同上 |
| 离屏渲染_使视图无效 | FBroLib.wsv:1194 | N/A | — | 同上 |
| 离屏渲染_取帧率 | FBroLib.wsv:1204 | N/A | — | 同上（若后台浏览器内部确为 OSR 则该项有价值，见 D2） |
| 离屏渲染_置帧率 | FBroLib.wsv:1213 | N/A | — | 同上（见 D2） |
| 离屏渲染_IME置组成 | FBroLib.wsv:1225 | N/A | — | OSR 下的 CJK IME 组合；当前窗口化路径由系统 IME 处理。文本输入可用 `browser_fill_set_value`/`browser_vip_key_type` 达成 |
| 离屏渲染_IME置交互文本 | FBroLib.wsv:1252 | N/A | — | 同上 |
| 离屏渲染_IME完成组合文本 | FBroLib.wsv:1267 | N/A | — | 同上 |
| 离屏渲染_IME取消组合 | FBroLib.wsv:1278 | N/A | — | 同上 |
| 离屏渲染_拖动进入 | FBroLib.wsv:1287 | N/A | — | OSR 拖放（宿主进程需自己处理拖拽数据），当前架构无 OSR 宿主管线；见 D2 |
| 离屏渲染_拖动移动 | FBroLib.wsv:1301 | N/A | — | 同上 |
| 离屏渲染_拖动离开 | FBroLib.wsv:1312 | N/A | — | 同上 |
| 离屏渲染_拖动放下 | FBroLib.wsv:1321 | N/A | — | 同上 |
| 离屏渲染_拖动结束位置 | FBroLib.wsv:1331 | N/A | — | 同上 |
| 离屏渲染_拖动系统结束 | FBroLib.wsv:1346 | N/A | — | 同上 |
| 清理缓存 | FBroLib.wsv:1357 | 已覆盖 | `browser_clear_cache_browser` ｜ MCP_Server_Core.wsv:7241（调用 :7357） | 且工具补齐了 `origin/targets/storage_types` 位或粒度（类库 :1360-1366），覆盖面 ≥ 类库 |
| 设置代理 | FBroLib.wsv:1381 | 已覆盖 | `browser_set_proxy` ｜ MCP_Server_Core.wsv:1484（调用 :1512）；VIP 优先走 `browser_set_s5_proxy`（MCP_Server_VIP.wsv:44） | 类库注释：不支持带账号密码的 S5（:1382），工具已按 VIP 优先处理 |
| 清空代理 | FBroLib.wsv:1393 | 已覆盖 | `browser_clear_proxy` ｜ MCP_Server_Core.wsv:1525（调用 :1545） | — |
| 取主填表框架 | FBroLib.wsv:1399 | 已覆盖 | 21 个填表工具共用 `解析填表框架` ｜ MCP_Server.wsv:8855（调用 :8866 `浏览器.取主填表框架 ()`） | 分派示例 `browser_fill_set_value` ｜ MCP_Server_Form.wsv:12（调用 :27） |
| 取焦点填表框架 | FBroLib.wsv:1406 | 等价覆盖 | `browser_get_focused_frame`（Core:4083）＋ 任一 `browser_fill_*` 的 `frame_id` 参数（Form.wsv:27 等） | 该库方法 src 内 **0 调用**；等价为两步：先由焦点框架拿 `frame_id`，再传给填表工具 ⇒ 操作能力一致，但**没有**"直接取焦点填表框架对象"的入口 |
| 取填表框架_ID | FBroLib.wsv:1414 | 已覆盖 | `解析填表框架` ｜ MCP_Server.wsv:8855（调用 :8869） | 每个填表工具都接受 `frame_id`（Form.wsv:27/:56/:85/:114/:143/:190/:271/:395/:426） |
| 取填表框架_名称 | FBroLib.wsv:1422 | 已覆盖 | `解析填表框架` ｜ MCP_Server.wsv:8855（调用 :8875） | 同上 |
| 取开发者DOM | FBroLib.wsv:1429 | 已覆盖 | `browser_vip_dom_get_document` ｜ MCP_Server_VIP.wsv:1565（经 `取开发者DOM_安全` MCP_Server.wsv:8405 → :8409 `browser.取开发者DOM ()`） | `browser_vip_dom_search`（VIP:1592）亦复用 |
| 取额外数据 | FBroLib.wsv:1436 | 已覆盖 | `browser_get_extra_data` ｜ MCP_Server_VIP.wsv:1839（调用 :1846） | — |
| 取主浏览器 | FBroLib.wsv:1443 | 等价覆盖 | `browser_get_main_browser`（Core:6859→:6866 `opener_hwnd`）＋ `browser_find_by_hwnd`（Core:7191→:7200） | 该库方法 src 内 **0 调用**（全部 `取主浏览器 ()` 命中都是项目自己的 `MCP命令服务器.取主浏览器`，MCP_Server.wsv:8237）。等价为两步链：拿打开者句柄→换成浏览器对象。⚠ 工具语义是"**打开者**浏览器"，类库是"**主(父)**浏览器"：单级弹窗场景一致，多级/非同源父子场景可能不等价（见 D3） |
| 取VIP控制器 | FBroLib.wsv:1449 | N/A | — | VIP 能力入口对象；其能力已被 70+ 个 `browser_vip_*` / `browser_fingerprint_*` 工具逐个暴露，再暴露"取控制器"本身没有新增能力 |
| 取窗口运行风格 | FBroLib.wsv:1456 | 已覆盖 | `browser_get_run_style` ｜ MCP_Server_System.wsv:151（调用 :168 `browser.取窗口运行风格 ()`） | 返回 `runtime_style` 0/1/2（枚举先转整数，:170）+ `runtime_style_name`；工具自述本机值为 1(谷歌) 且项目未显式设置该项（System:183） |

---

## 3. `类_FBrowser_基础框架`（13 个方法，被 `类_FBrowser_框架` 继承）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 是否为空 | FBroLib.wsv:1477 | N/A | — | 判空守卫（框架族 500+ 处前置检查），非能力 |
| 置空 | FBroLib.wsv:1482 | N/A | — | 内部指针置空 |
| 是否有效 | FBroLib.wsv:1487 | N/A | — | 有效性守卫（`解析框架对象` 的契约就以它为准，MCP_Server.wsv:8795 区段）；不单独暴露 |
| 取地址 | FBroLib.wsv:1493 | 已覆盖 | `browser_get_url`（Core:157→:167）；`browser_status`（:4041）；`browser_get_frames`（:1698→:1748）；`browser_frame_by_name`（:6670→:6689）；`browser_frame_by_id`（:6706→:6731）；`browser_find_by_tag`（:6746→:6765）；`browser_find_by_hwnd`（:7191→:7210） | 主框架地址与**逐框架地址**都能取到 |
| 取框架名 | FBroLib.wsv:1501 | 已覆盖 | `browser_get_focused_frame` ｜ MCP_Server_Core.wsv:4083（分支内取 `focusFrame.取框架名 ()`）；`browser_frame_by_name`（:6670 回显 name） | 类库注释：为空=主框架 |
| 是否为主框架 | FBroLib.wsv:1509 | 已覆盖 | `browser_get_frames` ｜ MCP_Server_Core.wsv:1698（:1746 `帧实体.是否为主框架 ()` → `is_main`） | 另在 `browser_frame_by_name`(:6691 区段)/`browser_frame_by_id`/`browser_get_focused_frame` |
| 是否为焦点框架 | FBroLib.wsv:1515 | 已覆盖 | `browser_frame_by_name` ｜ MCP_Server_Core.wsv:6670（字段 :6692 `is_focused`）；`browser_frame_by_id`（:6706 区段） | `browser_get_focused_frame` 亦直接给出焦点框架 |
| 取框架ID | FBroLib.wsv:1521 | 已覆盖 | 同 `类_FBrowser_浏览器.取框架ID`（:1698/:6639）＋ `解析框架对象` 的序号路径（MCP_Server.wsv:8795） | 注意：此名在 `类_FBrowser_浏览器`(:771) 也有一个同名方法，两者都已覆盖 |
| 执行JS代码 | FBroLib.wsv:1529 | 已覆盖 | `browser_execute_js` ｜ MCP_Server_Core.wsv:285；`browser_evaluate` ｜ Core:426 | 项目 JS 通道底层即框架的 `执行JS代码` / `执行JS代码_带返回值`（调用点 Core:335/:419/:547 等） |
| 执行JS代码_带返回值 | FBroLib.wsv:1538 | 已覆盖 | `browser_execute_js{frame_id, world}`（Core:285，:297-360 区段）/ `browser_evaluate`（Core:426） | 子框架执行有显式世界选择与"框架不存在明确报错"契约（:297-304 注释） |
| 取浏览器 | FBroLib.wsv:1555 | N/A | — | "框架→所属浏览器"的型转换辅助；MCP 层每个工具都已知目标浏览器（公共参数 `browser_id`），无需暴露 |
| 取填表框架 | FBroLib.wsv:1561 | N/A | — | 框架→填表框架的型转换；需要填表操作时直接用 `browser_fill_*`（其内部走 `解析填表框架`，MCP_Server.wsv:8855） |
| 取框架 | FBroLib.wsv:1566 | N/A | — | 基础框架→派生框架的型转换 |

---

## 4. `类_FBrowser_框架`（17 个方法）

| 类库方法 | 类库 file:line | 判定 | MCP 工具名 + 实现 file:line | 依据与备注 |
|---|---|---|---|---|
| 撤销 | FBroLib.wsv:1583 | 已覆盖 | `browser_edit_undo` ｜ MCP_Server_Core.wsv:1578（调用 :1588 `undoFrame.撤销 ()`） | — |
| 恢复 | FBroLib.wsv:1589 | 已覆盖 | `browser_edit_redo` ｜ MCP_Server_Core.wsv:1595（调用 :1605） | — |
| 剪切 | FBroLib.wsv:1595 | 已覆盖 | `browser_edit_cut` ｜ MCP_Server_Core.wsv:1612（调用 :1622） | — |
| 复制 | FBroLib.wsv:1601 | 已覆盖 | `browser_edit_copy` ｜ MCP_Server_Core.wsv:1629（调用 :1639） | — |
| 粘贴 | FBroLib.wsv:1607 | 已覆盖 | `browser_edit_paste` ｜ MCP_Server_Core.wsv:1646（调用 :1656） | — |
| 删除 | FBroLib.wsv:1613 | 已覆盖 | `browser_edit_delete` ｜ MCP_Server_Core.wsv:1663（调用 :1673） | — |
| 全选 | FBroLib.wsv:1619 | 已覆盖 | `browser_edit_select_all` ｜ MCP_Server_Core.wsv:1680（调用 :1690） | 7 个编辑工具都作用于**主框架**（`取安全主框架`）；子框架内的编辑需先用 `browser_fill_focus{frame_id}` |
| 源码视图 | FBroLib.wsv:1625 | 等价覆盖 | `browser_view_source` ｜ MCP_Server_Core.wsv:4063 | ⚠ **语义偏移且为刻意设计**：工具注释原文"不调用原生 源码视图(), 其会弹记事本窗口阻塞控制台"（Core:4064），改为返回源码文本（经 `异步取源码_带限制` MCP_Server.wsv:5756）。代理取源码更好用，但"打开 view-source 页"这一 UI 行为不存在 |
| 载入地址 | FBroLib.wsv:1632 | 已覆盖 | `browser_navigate` ｜ MCP_Server_Core.wsv:111（调用 :139 `navFrame.载入地址 (url)`） | ⚠ 只作用于**主框架**（`取安全主框架`，MCP_Server.wsv:8312）。子框架内导航需 `browser_execute_js{frame_id, world:main}` 改 `location`（等价但非同名入口） |
| 取源码_异步 | FBroLib.wsv:1639 | 已覆盖 | `browser_get_source` ｜ MCP_Server_Core.wsv:446；`browser_view_source`（Core:4063） | 调用点：`异步取源码_带限制` MCP_Server.wsv:5756 → :5782 `安全框架.取源码_异步 (字符串回调)` |
| 取文本_异步 | FBroLib.wsv:1654 | 已覆盖 | `browser_get_text` ｜ MCP_Server_Core.wsv:464 | 调用点：`异步取文本_带限制` MCP_Server.wsv:5797 → :5823 `安全框架.取文本_异步 (字符串回调)` |
| 载入请求 | FBroLib.wsv:1669 | **真缺口** | 无 | 详见 §4-A1。src 内 `载入请求` **0 命中**；`browser_navigate` 只发 GET/无自定义头（Core:111 区段） |
| 发送进程消息 | FBroLib.wsv:1676 | 等价覆盖 | `browser_ipc_send_all/to`（Core:7023/7042→:7037/:7062）、`browser_send_message`（System:25→:41） | ⚠ **通道不同**：项目走的是类库另一族 `进程间消息_发送数据_到全部/指定渲染进程`（扩展通道，页面侧由 `window.__mcp_ipc_queue` 接收，见 MCP_BrowserEvents.wsv:2643 注释），**不是** CEF 原生 `CefProcessMessage`（本方法）。且 `类_FBrowser_进程消息`（名+参数对象）未暴露 ⇒ 对"期待原生 IPC 的页面/插件"不等价（见 D4） |
| 取V8环境 | FBroLib.wsv:1685 | N/A | — | 类库自注"只能在渲染进程中调用"（FBroLib.wsv:1685）；本服务在主进程调用无效。页面 JS 环境需求已由 `browser_execute_js` / `browser_evaluate` / `browser_vip_execute_js_context`（VIP:1493）覆盖 |
| 取父框架 | FBroLib.wsv:1692 | **真缺口** | 无 | 详见 §4-A2。src 内 **0 命中**；`browser_get_frames`（Core:1698）只给平铺清单，无父子层级 |
| 访问DOM对象 | FBroLib.wsv:1698 | N/A | — | 类库自注"只能在渲染进程中调用"（FBroLib.wsv:1698）；DOM 读取已有 `browser_dom_query/get_html/inner_html`（Core:1819/1979/2062）与 CDP DOM 域（`browser_vip_dom_get_document` VIP:1565），无需该渲染进程专用入口 |
| 创建URL请求 | FBroLib.wsv:1713 | 等价覆盖 | `browser_create_url_request` ｜ MCP_Server_Core.wsv:7100（调用 :7188 全局版 `FBrowser_创建URL请求 (请求, , URL请求回调, 超时)`） | 框架级方法未接线，但同一能力的**全局版**已接线（含自定义头 :7062-7096、POST 体 :7100-7110、状态码回传）；语义等价 |

### 4-A 真缺口详情（本分片范围内共 3 条）

> 每条给出：① 类库完整签名（从源码行照抄）② 对"AI 代理做浏览器自动化"的实际价值 ③ 实现风险（启动期/安全/文档与安装版本一致性 + 判别办法）。
> 项目已有先例：`FBrowser_取初始化缓存目录 ()` 因**类库文档与安装版本不一致而编译不过**（原始记录见 `MCP_Server_System.wsv:81`：`类库 FBrowser_取初始化缓存目录() 本机**编译不过**(FBroLib.v:155 error C3861 IsEmpty)`），故每条都写明判别办法。

#### A1. `载入请求`（FBroLib.wsv:1669-1674）— 价值最高

```text
方法 载入请求 <公开 注释 = "英文名：LoadRequest">
参数 请求 <类型 = 类_FBrowser_请求>
{
    @ if(IsEmpty()) return;
    @ FBroHsBrowserFrame_LoadRequest(m_class,@<请求>.m_class);
}
```
- 签名要点：无返回值（成功与否只能靠事件/地址变化判定）；参数只有一个 `类_FBrowser_请求`（该对象可设地址/类型/协议头/POST 数据——项目里 `browser_create_url_request` 已示范完整构造法，Core:7100 区段的 :7062-7110）。
- **价值（一句话）**：把"带自定义方法/请求头/POST 体的请求"直接作为**该框架的加载**发出去 —— AI 代理复现"点提交式跳转/带签名头与 Referer 的接口跳转/回放受保护地址"，无需绕 `fetch` + `document.write`（后者会丢历史、丢 Referer、易被风控识别）。
- **风险**：
  1. **无返回值** ⇒ 必须沿用 `browser_navigate` 的"载入前记录发起时刻 + 注册加载等待任务"模式（MCP_Server_Core.wsv:137-147），否则会像早期"恒报成功"的工具一样谎报；断言依据只能是 `load_end` 事件与地址变化。
  2. **主进程可用性未知（不确定点）**：项目在 `browser_navigate` 里确实从主进程调通了框架的 `载入地址`(LoadURL)（MCP_Server_Core.wsv:139），但 `LoadRequest` 是**另一个宿主导出符号**（`FBroHsBrowserFrame_LoadRequest`），二者不能互相推断 ⇒ 接线前必须跑一次最小用例（构造 `类_FBrowser_请求` → 载入请求 → 看是否真的发起请求）。
  3. **安全**：会发出真实网络请求，必须复用 `验证URL安全`（Core:118 同款守卫）与 URL 请求并发槽（:7100 区段的 `尝试占用URL请求槽`）思路；不得让外部输入决定任意方法与任意头（否则成为 SSRF/头注入通道）。
  4. **启动期限制**：无（运行期可调），非仅启动生效。
  5. **文档与安装版本不一致风险 + 判别办法**：该方法体只含 `if(IsEmpty()) return;` + 单一 `FBroHs*` 导出。判别步骤：先看同文件里**已知可编译**的同构方法（`载入地址` FBroLib.wsv:1632-1637、`取父框架` :1692-1696，同为 `IsEmpty()` + 单一导出）——若它们能编译而 `载入请求` 报 `LNK2019 无法解析的外部符号 FBroHsBrowserFrame_LoadRequest` / `C3861`，即为安装版本不一致，此时应放弃接线，改用 CDP 兜底 `browser_cdp_call`(Core:4870) → `Page.navigate {url, postData, headers}`（**注意：该替代只覆盖 postData/headers 子集，且我未运行验证其在本机 CEF 构建下是否生效**）。

#### A2. `取父框架`（FBroLib.wsv:1692-1696）

```text
方法 取父框架 <公开 类型 = 类_FBrowser_框架 注释 = "GetParent" @禁止流程检查 = 真>
{
    @ if(!IsEmpty ()) return @dt<类_FBrowser_框架>(FBroHsBrowserFrame_GetParent(m_class));
    @ return @dt<类_FBrowser_框架>();
}
```
- 签名要点：无参数；返回 `类_FBrowser_框架`（取不到返回**空类**，调用方必须判空）。
- **价值（一句话）**：从子框架回溯父框架 —— 广告位/支付 iframe/嵌套 OOPIF 里定位"当前操作框架的上级文档"，用于逐级向上执行 JS 或读父页面 DOM；现状只能靠 `browser_get_frames`（Core:1698）给出 id/name/url/is_main 的**平铺**清单，没有父子边，跨域框架只能拿 url 猜层级。
- **风险**：
  1. 纯只读、无副作用 ⇒ 安全风险低，不是启动期能力。
  2. **语义风险（CEF 层，不确定点）**：对跨进程(OOPIF)子框架，浏览器进程侧 `GetParent` 可能返回空。实现必须 `是否为空()/是否有效()` 守卫后**如实报 `found:false` + hint**，严禁回退主框架 —— 这条契约项目里已有先例可照抄（`解析框架对象`，MCP_Server.wsv:8795 区段注释："找不到返回空类…不得静默落到主框架"）。
  3. 文档/安装版本一致性：方法体仅 `IsEmpty()+GetParent`，与 `取框架_ID`(FBroLib.wsv:757) 同款 ⇒ 风险低；判别办法同 A1-⑤（看是否只有该方法报未定义符号）。

#### A3. `尝试关闭浏览器`（FBroLib.wsv:796-807）— 价值最低，且**不建议**直接接线

```text
方法 尝试关闭浏览器 <公开 类型 = 逻辑型
        注释 = "英文名：TryCloseBrowser 说明:Helper for closing a browser. Call this method from the top-level window close handler."
        @禁止流程检查 = 真>
参数 是否置空 <类型 = 逻辑型 注释 = "..." @默认值 = 假>
{
    @ if(IsEmpty()) return false;
    @ if(FBroHsBrowserHost_TryCloseBrowser(m_class)){ 
    @ if(@<是否置空>) {m_class = nullptr;}
    @ return true;}
    @ return false;
}
```
- 签名要点：1 个可选逻辑参数（`是否置空`，默认假）；返回逻辑型（真=已请求关闭）。
- **价值（一句话）**：唯一"页面可否决"的优雅关闭路径（`beforeunload` 生效）—— 代理在已填表/未保存页面上收尾时先试优雅关闭，由页面自己决定；现工具 `browser_close` 自述"**强制关闭, 不询问页面**(beforeunload 不阻塞)"（MCP_Server_Core.wsv:727 区段的工具描述）。
- **风险**：
  1. **项目已断言本架构恒失败**（不是我的实测）：`browser_close` 描述原文"类库的 尝试关闭浏览器…在本项目**恒返回假** —— 本项目是控制台程序, 没有类库要求的「顶层窗口关闭处理器」"，且 `browser_close_try`(Core:4058) 是明确的恒失败桩。我**未运行验证**该断言 ⇒ 属**待验证的既有结论**；接线前必须做最小用例（新建浏览器 → 尝试关闭 → 看返回值与页面 `beforeunload` 是否被触发）。
  2. 若验证为恒假：正确处置是**把 `browser_close_try` 从工具表移除**（项目此前已清理过同类恒失败工具），而不是新增接线 —— 否则只会再造一个误导性工具。
  3. 无启动期限制；参数仅一个逻辑型，无注入面；副作用是"可能关闭浏览器"，属破坏性操作，应要求 `confirm:true`（沿用 `browser_close`/`browser_shutdown` 惯例）。
  4. 文档/安装版本一致性：方法体仅 `IsEmpty()+TryCloseBrowser`，风险低；判别办法同 A1-⑤。

---

## 5. 小结

### 5.1 判定计数（本分片 143 个方法）

| 类 | 方法数 | 已覆盖 | 等价覆盖 | 真缺口 | N/A |
|---|---|---|---|---|---|
| FBrowser辅助功能 | 18 | 11 | 2 | 0 | 5 |
| 类_FBrowser_浏览器 | 95 | 66 | 7 | 1 | 21 |
| 类_FBrowser_基础框架 | 13 | 7 | 0 | 0 | 6 |
| 类_FBrowser_框架 | 17 | 10 | 3 | 2 | 2 |
| **合计** | **143** | **94 (65.7%)** | **12 (8.4%)** | **3 (2.1%)** | **34 (23.8%)** |

> 计数口径：对产出文件按"第 2 列含 `FBroLib.wsv:<行号>` 的表格行"逐行统计所得（143 行 = 143 个方法，无遗漏），可与 §1-§4 表格逐行对齐复核。

**结论要点**：此前 363 条"候选缺口"在本分片范围内**绝大多数是误报**（本分片 143 条里只有 3 条真缺口，占 2.1%），且同时存在**漏报**：
- **误报（候选缺口→实为已覆盖）**：本分片命中 `_classlib_gap.md` 候选表的 `停止载入`、`可否前进`、`重新载入`、`重新载入_忽略缓存`、`开始下载`、`打开对话框`、`显示隐藏窗口`、`清理缓存`、`移动窗口`、`设置代理`、`载入地址`、`访问DOM对象` 等 —— 复核后 `停止载入`/`可否前进`/`重新载入*`/`开始下载`/`显示隐藏窗口`/`清理缓存`/`移动窗口`/`设置代理`/`载入地址` 均为**已覆盖**，`打开对话框` 为等价覆盖（语义偏移），`访问DOM对象` 为 N/A（渲染进程专用）。
- **漏报（判为"疑似已覆盖"→实为真缺口或需两步）**：`取父框架`(FBroLib.wsv:1692) 与 `取主浏览器`(FBroLib.wsv:1443) **都不在候选缺口表里**（因工具描述里出现过"主浏览器"等字样被判命中），但前者是真缺口、后者需两步链才等价。⇒ 若要继续用该类启发式，必须补一遍"反向核查"。误报根因与 `_classlib_gap.py`（脚本第 89-91 行）的口径有关：它以"方法名是否出现在**任一工具的完整描述文本**里"为判据，故只要描述里提过名字就算命中、提不到就算缺失 —— 与"是否真的接线"无关（例如 `取窗口运行风格` 曾被记为缺口，实际已接线并在 System:168 调用；而 `取主浏览器` 从未接线，却因描述里出现"主浏览器"字样而被判为疑似已覆盖）。

### 5.2 真缺口清单（按价值排序，本分片仅 3 条）

| # | 方法 | 一句话价值 | 处置建议 |
|---|---|---|---|
| 1 | `载入请求`（FBroLib.wsv:1669） | 用带自定义方法/头/POST 体的**请求**直接加载该框架，是复现"提交式跳转/带签名头接口跳转"的通道（现只能 GET，Core:111 区段） | 建议接线为 `browser_navigate {method, headers, body}` 或独立工具；先做 A1-② 最小验证 |
| 2 | `取父框架`（FBroLib.wsv:1692） | 给出**框架层级**（父边），用于广告/嵌套/OOPIF iframe 场景逐级向上操作；现清单无层级（Core:1698） | 建议并入 `browser_get_frames` 回包（每项加 `parent_id`），比新增工具更省工具位 |
| 3 | `尝试关闭浏览器`（FBroLib.wsv:796） | 唯一可被页面 `beforeunload` 否决的优雅关闭；现只有强制关闭（Core:727 区段） | **先验证再决策**：验证恒假则删除 `browser_close_try` 桩；验证可用再接线（需 `confirm`） |

### 5.3 需要主代理留意：6 条"等价覆盖"其实有语义偏移（不是缺口，但按名字选用会踩坑）

| 方法 | 替代工具 | 偏移点 |
|---|---|---|
| `打开对话框`(878) | `browser_file_dialog`(Core:6995) | 不弹真对话框，改为"传 path 校验存在"（刻意安全替代） |
| `源码视图`(1625) | `browser_view_source`(Core:4063) | 不打开 view-source 页面，只回源码文本（刻意替代；Core:4064 注释） |
| `发送进程消息`(1676) | `browser_ipc_send_all/to`(Core:7023/7042) | 走类库**扩展** IPC 通道（`window.__mcp_ipc_queue`），非 CEF 原生 `CefProcessMessage` |
| `取主浏览器`(1443) | `browser_get_main_browser`(Core:6859)+`browser_find_by_hwnd`(Core:7191) | 工具给的是**打开者**句柄，需两步换算；多级弹窗/非同源父子时语义可能不等价 |
| `取焦点填表框架`(1406) | `browser_get_focused_frame`(Core:4083)+填表工具 `frame_id` | 需两步；无"直取焦点填表框架对象"入口 |
| `发送触摸事件`(1017) | `browser_touch_*`(Core:6397/6430/6463) | 内核路径走的是 **VIP** `高级触摸_*`(Core:6423/6456/6489)；类库的触摸结构体（多点/半径）未暴露 |

### 5.4 我把握不足的点（明确标出，未猜）

- **D1（`取数据URI` 的二进制能力）**：类库签名 `参数 数据 <类型 = 文本型>`（FBroLib.wsv:396）但底层走 `FBroHsGetDataURI(mimetype, 数据)`，我**无法从 .wsv 判定**"文本型"在生成 C++ 侧是按字节集还是按 C 字符串解释 —— 因此"用 base64 工具 + 手拼前缀"对**二进制**数据是否等价，我未确认（纯文本/UTF-8 数据可确定等价）。
- **D2（离屏渲染 17 项的 N/A 判定）**：我判 N/A 的依据是"项目创建路径未设置 `浏览器配置.无窗口渲染`"（main.wsv:233-258 只设窗口信息 5 个字段，`浏览器配置` 全程为默认空对象）**且**这些方法在 src 内 0 命中。但类库 `FBrowser_创建后台浏览器` 的底层 `FBroHsCreateBackground` 是否**内部即 OSR**，从 .wsv 无法判定 —— 若它其实是 OSR，则 `离屏渲染_取帧率/置帧率` 与 `通知已被调整大小/已被隐藏` 对**后台浏览器**就有真实价值（`拖动*`/`IME*` 仍难有代理价值）。此项需要 C++ 头文件或运行期证据才能定论。
- **D3（`取主浏览器` 的两步等价是否严格成立）**：`browser_get_main_browser` 返回的是 `取打开者窗口句柄`（Core:6866），而类库 `取主浏览器` 是 `FBroHsBrowserHost_GetMainBrowser`。在"弹窗由主浏览器打开"的常见场景两者一致；但类库注释写的是"主(父)浏览"（FBroLib.wsv:1443），多级弹窗或非典型父子关系下是否仍一致，我无法静态判定。
- **D4（`发送进程消息` 的等价强度）**：`进程间消息_*` 族与 CEF 原生 `SendProcessMessage` 是否在**内核层同源**，.wsv 层面看不到（`FBroHs` 导出符号不可见）。若目标页面/扩展依赖原生 IPC（例如自定义 C++ 消息处理器、`CefMessageRouter` 之外的原生通道），现有工具**不等价**。
- **D5（`browser_close` 是否真会跳过 beforeunload）**：类库注释说会触发 `onbeforeunload`（FBroLib.wsv:786，且有 `立即关闭` 参数控制），而工具描述说"强制关闭、不询问页面"。两者**可能都成立**（`立即关闭=真` 才是强制），但从 .wsv 无从判定项目实际传的实参，故我未把这条升级为缺口，只在 §2 备注里标出语义差异。（`browser_close` 的调用点：MCP_Server_Core.wsv:744 `closeBrowser.关闭浏览器 ()` —— 无论实参如何，工具描述与类库注释的口径不一致，值得主代理顺带校正文案。）
- **D6（行号漂移）**：`MCP_Server_Core.wsv`（12:00:31）与 `MCP_Server.wsv`（12:05:47）在本次核对期间**被并发修改**（Core 由 8675 行增至 8747 行，Server 由 12254 行增至 12402 行；且早前 `_audit` 里 `MCP_Server_System.wsv:16/47/71/115` 一类旧引用与当前文件已不符）。本文所有行号均为 12:06 快照，**复核时请以每行备注里的锚点原文为准**，不要只按数字跳转。
