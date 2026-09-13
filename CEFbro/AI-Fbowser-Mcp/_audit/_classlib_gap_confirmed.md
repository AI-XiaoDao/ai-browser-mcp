# 类库能力缺口 — 交叉核对确认报告（只读分析产出）

> 分析对象：`_audit/_classlib_gap.md` 的 **363 个候选缺口** 中，**7 个优先类共 210 个候选**。
> 真实工具清单来源：`src/` 下 16 个 `.wsv`（非 `.~vbak`）——`添加工具JSON` 声明 **301 个工具**（全部在 `src/MCP_Server.wsv`），
> 实际分派路径 = `命令注册表`（469 项，含 `browser.x` / `browser_x` / 短名三重变体）**或** `MCP_Server.wsv:10257` 的规范名 if-else 链
> （`browser_get_window_style` / `browser_set_window_style` / `browser_get_run_style` / `browser_create_tab` / `browser_task_runner_post` 等走此链，
> 因此"不在命令注册表"**不等于**死工具）。
>
> **核对判据**（严于原脚本）：① 必须能指名现有工具且**功能等价**（不是词面相似）；② 读 handler 实现确认该工具**真的调用了对应内核 API**，
> 而非仅名字相近；③ 批量工具（一个工具内调多个内核方法）计入"已覆盖"。

## 结论速览

| 判定 | 数量 | 占优先类候选比例 |
|---|---|---|
| **已确认真缺口** | **31** | 14.8% |
| **已覆盖**（含纠正的误报） | **152** | 72.4% |
| **不适用 / 平台限制** | **27** | 12.9% |
| 合计（7 个优先类） | 210 | 100% |

- 原脚本在优先类上的 **误报率 72.4%**（152/210）——主要因为英文工具名 + 批量工具（如 `browser_vip_disable_console` 一个工具吃下 14 个 `内核开关_禁用Console*`）。
- 原报告的 363 个候选按此误报率外推，真实缺口量级远小于 363。

---

## 1. 已确认真缺口（31 项）

`建议工具名 | 对应类库方法 | 所属类 | 价值 | 依据(为何判定缺失) | 实现要点`

### 1.1 高价值（3）

| 建议工具名 | 对应类库方法 | 所属类 | 价值 | 依据（为何判定缺失） | 实现要点 |
|---|---|---|---|---|---|
| `browser_select` | `FBrowser_浏览器_通过ID取浏览器` | FBrowser辅助功能 | **高** | 全项目 **118 处** `取主浏览器()`（`MCP_Server_Core.wsv`），只有 `browser_close` 暴露 `browser_id` 参数。`目标浏览器ID` 全局字段虽在 `MCP_Server.wsv:10229-10233` 被赋值，但**仅 `执行CDP命令_带参数`（CDP 类工具）消费**，Core/填表/内核/VIP 全部分派器直接忽略它。后果：`browser_create` 能造出第二个浏览器，却**没有任何工具能操作它**——多账号/并行采集实际不可用 | 新增 `browser_select {browser_id\|tag\|index}`，内部用 `FBrowser_浏览器_通过ID取浏览器` / `通过用户标识取浏览器` / `通过序号取浏览器` 解析并写入 `目标浏览器ID`；同时把 Core 的 `取主浏览器()` 统一改为 `取目标浏览器()`（`目标浏览器ID>0` 时走指定实例，否则回退主浏览器）。注意 `browser_create` 默认把新实例设为主浏览器 |
| `browser_create_background` | `FBrowser_创建后台浏览器` / `FBrowser_创建后台浏览器_同步` | 类_FBrowser_浏览器 | **高** | 现有唯一创建工具 `browser_create` 描述为"新建一个**可见**浏览器窗口"，无 `background`/`headless` 参数（`MCP_Server.wsv:9314`）。全 `src` grep `FBroHsCreateBackground`/`后台浏览器` **零命中**。类库注释明确：后台浏览器"没有窗口也没有窗口句柄…比前台浏览器占用更低…优于无头模式"，是**批量取数**的核心能力 | `FBrowser_创建后台浏览器(地址,浏览器配置,请求环境,额外信息,事件智能指针,禁用事件,标识)` 返回逻辑型；`_同步` 版返回 `类_FBrowser_浏览器` 但**必须在 UI 线程经 `FBrowser_任务运行器_投递任务`** 调用。当前 `browser_task_runner_post` 被硬禁用（`MCP_Server_System.wsv:20-23`，理由是"GUI窗口自动管理浏览器实例"）——该理由针对 GUI 标签页，对**无窗口**后台浏览器不成立，需放开或改为内部经 UI 时钟创建 |
| `browser_clear_storage` | `FBrowser_浏览器_清理缓存` | 类_FBrowser_浏览器 | **高** | `browser_clear_cache_browser` 声明**无任何 schema 参数**（`MCP_Server.wsv:9332` 后面没有 `单参数Schema文本/多属性Schema文本`），只能整浏览器粗粒度清理；`browser_clear_cache` 是 CEF **全局**缓存且"影响所有浏览器实例"。类库 `清理缓存` 支持 `源地址(origin)` + `清理对象位或(清理缓存.Appcache/Cookies/IndexedDB/LocalStorage/ServiceWorkers/WebSQL/CacheStorage)` + `存储类型`。缺失后果：AI 无法"只清 localStorage/IndexedDB 而保留登录 Cookie"来做状态复位，也没有任何工具能清 localStorage | `FBrowser_浏览器.清理缓存(源地址, 清理对象长整数位或, 存储类型长整数, 清理缓存回调事件智能指针)`；注意**异步回调**语义，结果走 `mcp_result`。常量取 `#清理缓存_Appcache` / `#清理缓存_Cookies` / `#清理缓存_LocalStorage` / `缓存类型.xxx`。与 `browser_delete_cookies` 有交集，文档需明确分工 |

### 1.2 中价值（5）

| 建议工具名 | 对应类库方法 | 所属类 | 价值 | 依据（为何判定缺失） | 实现要点 |
|---|---|---|---|---|---|
| `browser_set_remote_debug_port` | `设置远程调试端口` | 类_FBrowser_命令行 | **中** | 全 `src` grep `远程调试`/`debug_port`/`remote_debugging` **零命中**；`main.wsv:458 即将处理命令行` 只做事件记录（`app_startup_cmdline`），**从不调用命令行对象的任何方法**。缺失后果：外部 Playwright / Puppeteer / chrome-remote-interface 无法 attach 本进程，排障与生态复用被切断 | `类_FBrowser_命令行.设置远程调试端口(端口号)` → `FBroHsCommandLine_SetRemoteDebuggingPort`。必须在 **`浏览器_即将启动消息调度` 之前**调用（`main.wsv` 现成钩子），故需：配置项 + 写到配置 + 重启进程生效；工具语义应明确返回"需重启" |
| `browser_show_window` | `显示隐藏窗口` | 类_FBrowser_浏览器 | **中** | 全 `src` grep `ShowWindows`/`显示隐藏` **零命中**。`browser_restore_gui` 只是"标记需要恢复布局"的容器重排（`MCP_Server_Core.wsv:5417-5421`），`browser_set_window_style {type:GWL_STYLE}` 是改样式位的危险旁路——源码自己警告"省略 style 会清掉含 WS_VISIBLE 的全部位，可能使窗口不可见/不可用"（`MCP_Server_System.wsv:84-92`），属**反例而非替代** | `FBrowser_浏览器.显示隐藏窗口(逻辑型)` → `FBroHsBrowserHost_ShowWindows`。工具建议 `{show:true\|false}`；注意嵌入式容器布局（`adjust_layout`）可能在下次布局时重新显示，需与 `浏览器容器` 状态同步，并考虑恢复入口 |
| `browser_set_touch_trigger` | `高级_设置触发鼠标触摸事件` | 类_FBrowserVIP_控制器 | **中** | `browser_vip_touch_emulation` 的 handler 只调 `指纹_启用触摸事件(enable, max_points)`（`MCP_Server_VIP.wsv:1373-1383`）；`browser_touch_press/release/move` 走 CDP。**没有任何工具调 `高级_设置触发鼠标触摸事件`**，其 `配置` 参数（0=MOBILE / 1=DESKTOP）也无处设置。缺失后果：移动端页面（m.站点）鼠标→触摸事件转换无法开启，`isTrusted` 触摸链路易被识别 | `类_FBrowserVIP_控制器.高级_设置触发鼠标触摸事件(启用 逻辑型, 配置 整数)`，类库注明"**在浏览器载入完成后调用**"。建议与 `browser_vip_touch_emulation` 合并为 action，或独立 `browser_set_touch_trigger {enable, mode}` |
| `browser_menu_build` | `添加菜单` `添加子菜单` `添加分隔栏` `添加Check菜单` `添加Radio菜单` `选中状态` `选中状态_索引` | 类_FBrowser_菜单模式 | **中** | 该类是 `CefMenuModel` 封装（`FBroLib.wsv:3288`，含 `Clear/GetCount/AddItem/AddSubMenu/AddSeparator/AddCheckItem/AddRadioItem`）。MCP 侧只有 `browser_kernel_menu`，作用相反——**屏蔽**右键菜单（`action=disable/enable/status`）；`browser_collect` 的 `event_menu`/`event_quickmenu` 族只能**观察**"即将打开菜单"事件，**没有把自定义菜单模型写回 CEF 的通道**。缺失后果：AI 无法往浏览器右键菜单里加自定义项（如"用AI分析此元素"），只能整体屏蔽 | 需两条腿：① 菜单模型构建器（`类_FBrowser_菜单模式`：`清空菜单/添加菜单(命令ID,文本)/添加子菜单(命令ID,文本)/添加分隔栏/添加Check菜单/添加Radio菜单/选中状态(命令ID,选中)`）；② 在 `浏览器_即将打开菜单` / `即将运行快捷菜单` 事件回调里把构建好的模型交给 CEF。建议 `browser_menu_build {action:add_item\|add_submenu\|add_separator\|add_check\|add_radio\|check\|clear, id, label, items:[...]}` 一次下发整棵菜单树 |
| `browser_set_headless` | `启用无头模式` | 类_FBrowser_命令行 | **中** | `browser_create` 无无头参数；`src` 中 `--headless` 只出现在 **MCP 服务器自身**的 stdio 传输开关（`MCP_Stdio.wsv:214-225`），与浏览器无头无关。**额外证据**：内核库该方法实现有误——`启用无头模式` 方法体调用的是 `FBroHsCommandLine_EnableAutoplayPoliey`（`FBroLib.wsv:1909-1914`），**并未设置 `--headless`** | 不能直接用类库该方法；需 `类_FBrowser_命令行.置值("headless")`（AppendSwitch）在初始化前注入。且本项目是**嵌入式 GUI** 架构，无头与容器渲染冲突，需明确"仅新建后台浏览器场景可用"或改为引导用户用 `browser_create_background` 替代 |

### 1.3 低价值（23）

| 建议工具名 | 对应类库方法 | 所属类 | 价值 | 依据（为何判定缺失） | 实现要点 |
|---|---|---|---|---|---|
| `browser_menu_build` | `设置快捷键` `设置快捷键_索引` | 类_FBrowser_菜单模式 | 低 | 见上，`SetAccelerator` 无任何工具涉及；`grep shortcut` 零命中 | `CefMenuModel::SetAccelerator(command_id, key_code, shift, ctrl, alt)`；作为 `browser_menu_build` 的 `accelerator` 子字段 |
| `browser_menu_build` | `移除快捷键` `移除快捷键_索引` | 类_FBrowser_菜单模式 | 低 | 同上（`RemoveAccelerator`） | 同上，`action=remove_accel` |
| `browser_menu_build` | `存在快捷键` `存在快捷键_索引` | 类_FBrowser_菜单模式 | 低 | 同上（`HasAccelerator`） | 同上，`action=has_accel`，属查询类 |
| `browser_eval_all_frames` | `高级_执行JS_全部框架` | 类_FBrowserVIP_控制器 | 低 | `browser_vip_execute_js_context` 支持 `frame_id`（单框架），`browser_execute_js`/`browser_evaluate` 无 `frame` 参数；无"所有框架各执行一遍"的能力 | `类_FBrowserVIP_控制器.高级_执行JS_全部框架(code, 回调)`；或遍历 `browser_frame_names` 后逐个 `browser_vip_execute_js_context`。后者无需改内核，建议优先 |
| `browser_eval_all_frames` | `高级_执行JS_框架序号` | 类_FBrowserVIP_控制器 | 低 | 现有工具只接受 `frame_id`（字符串），**不接受序号**；需先 `browser_get_frames` 自行换算 | 在 `browser_vip_execute_js_context` 增加 `frame_index` 参数，内部经 `取框架名称()/框架序号` 换算 |
| `browser_set_gpu` | `禁用GPU` | 类_FBrowser_命令行 | 低 | 全 `src` grep `禁用GPU`/`DisableGpu` **零命中**。属兼容性/渲染排查手段（类库注释："不兼容的显卡只能禁用GPU否则网页可能渲染失败"），非高频 | `FBroHsCommandLine_DisableGpu`，初始化期一次性，需重启。建议与下面两项合并为 `browser_set_gpu {disable, disable_cache, ignore_blocklist}` |
| `browser_set_gpu` | `禁用GPU缓存` | 类_FBrowser_命令行 | 低 | 同上（`DisableGpuCache`） | 同上 |
| `browser_set_gpu` | `忽略GPU禁用清单` | 类_FBrowser_命令行 | 低 | 同上（`DisableGpuBlockList`） | 同上 |
| `browser_file_dialog`（增强） | `打开对话框` | 类_FBrowser_浏览器 | 低 | 工具名**存在**但能力被刻意阉割：handler 注释"原生OS文件对话框会弹出GUI窗口阻塞控制台，改为程序化选择"，只做**路径存在性校验**（`MCP_Server_Core.wsv:5422-5448`），既不弹窗也不支持 `文件对话框.保存` 模式的默认文件名/过滤器。若判定"需要真实文件选择器"，则 `RunFileDialog` 能力确实缺失 | `类_FBrowser_浏览器.打开对话框(模式,标题,默认文件名,过滤器文本数组,打开文件对话框回调)` → `FBroHsBrowserHost_RunFileDialog`。**建议保持现状**（MCP 无人值守场景弹窗是负资产），仅在文档里把"打开对话框=程序化路径校验"写清楚，避免 AI 误判 |
| `browser_reverse_add_binding`（增强） | `FBrowser_JS交互_删除` | FBrowser初始化控制 | 低 | `browser_reverse_add_binding` 只有添加（`Runtime.addBinding`），无移除路径；`grep removeBinding` 零命中。长期运行的会话里绑定只增不减 | `Runtime.removeBinding {name}`，作为 `browser_reverse_add_binding` 的 `action=add/remove` |
| `browser_fingerprint`（action 增强） | `指纹_清空调用计数` | 类_FBrowserVIP_控制器 | 低 | `指纹_取调用计数` **已有** `browser_fingerprint action=count`（`MCP_Server_Core.wsv:2075`），但**清空侧零命中**。计数只增不减，多轮测试间无法归零 | `类_FBrowserVIP_控制器.指纹_清空调用计数()` → 建议 `browser_fingerprint action=clear_count`。顺带修正 `browser_fingerprint` 描述：现有描述把 `count` 写成"查当前生效项数"，实际实现返回的是**指纹 API 调用计数**（描述与实际不符） |
| `browser_to_data_uri` | `FBrowser_Parser_取数据URI` | FBrowser辅助功能 | 低 | 无任何工具产出 `data:<mime>;base64,` 形式；`browser_screenshot` 只对自身截图返回 base64（`data:image/...`），无法对任意字节集/文件转 data URI | `FBrowser_Parser_取数据URI(mimetype, ...)`。**价值低**：AI 侧可自行拼 base64，除非要与 `browser_kernel_scheme`（`mcp://` 动态内容）配合注入内联资源，才值得做 |

### 1.4 完整性校验

`31 真缺口 + 152 已覆盖 + 27 不适用 = 210`，与 7 个优先类的候选总数 210 完全吻合。

---

## 2. 已覆盖（152 项，含纠正的误报）

`类库方法 | 对应现有工具名 | 判定依据`（判定依据均指**已读 handler 确认其真的调用了该内核方法**，非仅名字相似）

### 2.1 类_FBrowser_浏览器（9 项；任务点名的 10 个中 7 个是误报）

| 类库方法 | 对应现有工具名 | 判定依据 |
|---|---|---|
| `停止载入` | **`browser_stop`** | 工具名英文、描述"停止加载"不含"停止载入"四字 → 原脚本误报。原报告已实测确认；本次复核 `browser_stop` 在 `命令注册表`(ID 7) 与 `browser.stop`/`stop` 短名三重注册 |
| `可否前进` | **`browser_can_navigate`** | 工具描述即"查询当前页面可否后退/前进"，同时覆盖 `可否后退`+`可否前进`；宿主 `browser_loading_info` 亦返回 `can_go_back/forward` |
| `重新载入` | `browser_reload` | 见下 |
| `重新载入_忽略缓存` | **`browser_reload {ignore_cache:true}`** | **关键证据**：`MCP_Server_Core.wsv:136-143` 读 `ignore_cache` 并调用 `browser.reload_ignore_cache()`（即 `FBrowser_浏览器.重新载入_忽略缓存`）。schema 里 `ignore_cache` 是本工具**第一个参数**（`MCP_Server.wsv:9306`），实现完整——纯属原脚本看不到参数的误报 |
| `设置代理` | `browser_set_proxy`（+`browser_clear_proxy`） | 描述"设置浏览器代理并持久生效(新浏览器自动应用)"，与类库 `设置代理(地址,账号,密码)` 语义一致；`清空代理` 对应 `browser_clear_proxy`；VIP 的 SOCKS5 认证代理另有 `browser_set_s5_proxy` |
| `开始下载` | `browser_start_download` | 类库 `开始下载(地址)` = `FBroHsBrowserHost_StartDownload`；工具描述"触发下载 仅支持 http/https"，另有 `browser_kernel_download`(pause/resume/cancel) 与 `browser_download_image` 覆盖下载族 |
| `尝试关闭浏览器` | **`browser_close`** | 类库 `尝试关闭浏览器`=`TryCloseBrowser`（关闭前触发 beforeunload，可被页面取消）；`browser_close`=`CloseBrowser`，类库注释同样明确"**The JavaScript 'onbeforeunload' event will be fired**"，功能等价。旁证：`browser_close_try` 已被标记"[已废弃] 已替换为 browser_close \| ⛔ 该工具恒失败"（`MCP_Server.wsv:9316`），说明迁移是**有意为之**而非能力丢失 |
| `FBrowser_创建浏览器` | `browser_create`（+`browser_create_tab` 被禁用） | 工具描述"新建一个可见浏览器窗口(默认 about:blank)"，与类库 `FBrowser_创建浏览器` 语义一致；VIP 的标签页版 `高级_创建标签浏览器` 由 `browser_create_tab` 承接（现被禁用并给出替代方案 `browser_create`） |
| `FBrowser_创建浏览器_同步` | `browser_create` | 同步/异步仅是调用形态差异；MCP 侧统一由"返回 task_id + `mcp_result` 取结果"承载同步语义 |

### 2.2 FBrowser辅助功能（10 项）

| 类库方法 | 对应现有工具名 | 判定依据 |
|---|---|---|
| `FBrowser_Parser_Base64编码` / `_Base64解码` | `browser_base64_encode` / `browser_base64_decode` | 一对一命名对应 |
| `FBrowser_Parser_URI编码` / `_URI解码` | `browser_uri_encode` / `browser_uri_decode` | 一对一命名对应 |
| `FBrowser_浏览器_取ID清单` / `_取数量` | `browser_list`（+`ping.browsers`） | `browser_list`"列出所有浏览器实例"；`ping` 返回 `browsers` 计数（`MCP_Server_System.wsv:120`） |
| `FBrowser_浏览器_取用户标识清单` | `browser_user_tags` | 描述"列出用户标识"，即"用户标识清单"的英文名版本 |
| `FBrowser_浏览器_通过用户标识取浏览器` | `browser_find_by_tag` | "按标识查找浏览器"即按用户标识（tag）解析实例 |
| `FBrowser_浏览器_通过窗口句柄取浏览器` | `browser_find_by_hwnd` | "按句柄查找浏览器" |
| `FBrowser_清理全局缓存` | `browser_clear_cache` | 描述"清理CEF全局缓存\| 异步; 影响所有浏览器实例"；另有 `browser_get_global_cache_dir` 供取路径 |

### 2.3 FBrowser初始化控制（9 项）

| 类库方法 | 对应现有工具名 | 判定依据 |
|---|---|---|
| `FBrowser_JS交互_注册` | `browser_reverse_add_binding` | 描述"原生桥接(防检测): Runtime.addBinding。装一个由内核提供的函数供页面JS直接调用"——与 `FBrowser_JS交互_注册`（内核级 JS 绑定）功能等价 |
| `FBrowser_关闭` | `browser_shutdown` | handler 实现完整的安全关闭序列（`confirm:true` + `delay_seconds` 钳制 3s + `__SHUTDOWN__` 握手，`MCP_Server_System.wsv:124-151`） |
| `FBrowser_内存_压缩清理` | `browser_compress_memory` | 描述"V8内存压缩"；`MCP_Server_Core.wsv:1535` 实调 `FBrowser_内存_压缩清理 ()` |
| `FBrowser_创建URL请求` | `browser_create_url_request` | 一对一；schema `{url, method:GET/POST}` |
| `FBrowser_取初始化缓存目录` | `browser_cache_dir` / `browser_get_global_cache_dir` | 前者"获取缓存目录"，后者返回 `<运行目录>\CacheData\GlobalData`（`MCP_Server_System.wsv:47-52`） |
| `FBrowser_取版本号` | `browser_fbro_version` | 描述"CEF内核版本"；`MCP_Server_Core.wsv:1542`、`3660`、`5915` 实调 `FBrowser_取版本号 ()` 并注入 `fbro_version` 字段 |
| `FBrowser_自定义方案_注册` / `_清理` | `browser_kernel_scheme` | action=`register`/`unregister`/`clear`/`list`，注册 `mcp://域名` 动态内容，闭合了注册+清理两侧 |
| `FBrowser_进程_取当前进程类型` | `browser_get_process_type` | 描述"获取当前CEF进程类型(浏览器=0/渲染=1/GPU=2)"；handler 实调 `FBrowser_进程_取当前进程类型 ()` |

### 2.4 类_FBrowser_应用事件（24 项——**本类 27 个候选中 24 个是误报，误报率 89%**）

该类全是**事件回调方法**，而 `main.wsv` 已把它们**逐一实现为应用监控事件**并纳入 `browser_event`（描述明确"`app_*`查询应用事件"）。对应关系（`grep 记录应用监控事件` 全部命中）：

| 类库方法 | 对应现有工具名（事件名） | 判定依据（`main.wsv` 行号） |
|---|---|---|
| `即将处理命令行` | `browser_event` → `app_startup_cmdline` | L469 |
| `渲染_VIP_WebSocket客户端_创建` | `browser_event` → `app_render_ws_created` | L656 |
| `渲染_VIP_WebSocket客户端_关闭` | `app_render_ws_closed` | L669 |
| `渲染_VIP_WebSocket客户端_连接服务器` | `app_render_ws_connect` | L688 |
| `渲染_VIP_WebSocket客户端_接收数据` | `app_render_ws_recv` | L703 |
| `渲染_VIP_WebSocket客户端_发送数据` | `app_render_ws_send` | L720 |
| `渲染_即将创建V8环境` | `app_render_v8_context_created` | L513 |
| `渲染_即将初始化WebKit` | `app_startup_webkit_init` | L501 |
| `渲染_即将捕获异常` | `app_v8_exception` | L314 |
| `渲染_即将释放V8环境` | `app_v8_released` | L380 |
| `渲染_即将销毁浏览器` | `app_render_browser_destroyed` | L415 |
| `渲染_浏览器创建` | `app_render_browser_created` | L406 |
| `渲染_焦点节点改变` | `app_dom_focus_changed` | L368 |
| `渲染_收到消息` | `app_render_message_received` | L530 |
| `渲染_载入开始` | `app_render_load_start` | L567 |
| `渲染_载入状态被改变` | `app_render_loading_state` | L551 |
| `渲染_载入结束` | `app_render_load_end` | L583 |
| `渲染_载入错误` | `app_render_load_error` | L396 |
| `扩展插件_创建成功` | `app_extension_created` | L598 |
| `扩展插件_创建失败` | `app_extension_create_failed` | L616 |
| `扩展插件_载入成功` | `app_extension_loaded` | L630 |
| `扩展插件_卸载成功` | `app_extension_unloaded` | L644 |
| `注册自定义方案` | `browser_kernel_scheme`（action=register） | 非事件类，能力型 API，已由内核层工具覆盖 |
| `执行关闭完毕` | `browser_event`（`event_lifecycle` 族）+ `browser_status` | 由 `browser_collect event_lifecycle_enable` 观察族承载；生命周期细分可经 `app_render_browser_destroyed` 获得 |

### 2.5 类_FBrowser_命令行（4 项）

| 类库方法 | 对应现有工具名 | 判定依据 |
|---|---|---|
| `设置全局代理` | `browser_set_proxy` | 工具描述"设置浏览器代理并持久生效(**新浏览器自动应用**)"——正是"全局"语义；`browser_clear_proxy` 对应清理侧 |
| `禁用代理` | `browser_clear_proxy` | `--no-proxy-server` 的目的是"禁止使用代理和系统自动检测代理"。MCP 已配置的代理被清后即直连，对本场景功能等价（差异：不额外关闭 Windows 系统代理自动检测，故不单列缺口） |
| `启用跨框架操作模式` | `browser_vip_execute_js_context {frame_id}` / `browser_frame_by_name` / `browser_get_frames` | 类库手段是"解除框架间不能直接操作的限制"；MCP 用 CDP 按 `frame_id` 直接在各框架上下文求值，**天然绕过同源限制**，效果更强，故判为已覆盖 |
| `启用自动播放` | `browser_set_preference` | `autoplay-poliey` 本质是 Chromium 首选项（`profile.default_content_setting_values.autoplay`）；`browser_set_preference`"设置Chromium首选项"为通用入口，功能等价 |

### 2.6 类_FBrowserVIP_控制器（96 项——**本类 102 个候选中 96 个是误报，误报率 94%**）

主要靠**批量工具**吃掉大量候选（原脚本按"方法名是否出现在描述文本"判定，天然看不到批量能力）：

| 类库方法（合并计） | 对应现有工具名 | 判定依据 |
|---|---|---|
| `内核开关_禁用ConsoleLog/Warn/Error/Debug/Info/Trace/Clear/Assert/Dir/Table/Time/Count/Group/Profile` + `内核开关_禁用Performance检测`（**15 项**） | **`browser_vip_disable_console`** | handler 逐一调用全部 15 个内核方法（`MCP_Server_VIP.wsv:1503-1517`），参数名 `log/warn/error/debug/info/trace/clear/assert/dir/table/time/count/group/profile/performance`。一个工具即覆盖 15 个候选 |
| `内核开关_禁用Debugger` | `browser_vip_disable_debugger` | 一对一（`MCP_Server_VIP.wsv:317`）；另 `browser_debugger_enable` 描述"会自动清除与之冲突的反检测项(禁用Debugger检测)"，说明双向开关已通 |
| `内核开关_设置CSS内核` / `_设置V8内核` / `_设置Web内核` | `browser_vip_set_css_version` / `browser_vip_set_v8_version` / `browser_vip_set_web_version` | 一对一命名对应；另 `指纹_虚拟内核功能` 类库已注明"**弃用**" |
| `内核开关_设置EventIsTrusted` | `browser_vip_set_is_trusted` | 一对一 |
| `指纹_虚拟屏幕分辨率` + `屏幕可用高度和宽度` + `屏幕colorDepth` + `屏幕pixelDepth`（**4 项**） | **`browser_vip_fingerprint_screen`** | handler 依次调 `指纹_虚拟屏幕分辨率` / `指纹_虚拟屏幕可用高度和宽度` / `指纹_虚拟屏幕colorDepth` / `指纹_虚拟屏幕pixelDepth`（`MCP_Server_VIP.wsv:829-832`），参数 `height/width/avail_h/avail_w/depth/pixel_depth` |
| `指纹_虚拟HardwareConcurrency` + `指纹_虚拟DeviceMemory`（**2 项**） | `browser_vip_fingerprint_hardware` | handler 调 `指纹_虚拟HardwareConcurrency` + `指纹_虚拟DeviceMemory`（`:843-844`） |
| `指纹_虚拟Product` + `ProductSub` + `Vendor` + `VendorSub`（**4 项**） | **`browser_vip_fingerprint_product`** | handler 四个方法全调（`:855-858`），参数 `product/product_sub/vendor/vendor_sub`。**原脚本把 `指纹_虚拟Vendor` 判为缺口，是漏看了这个批量工具** |
| `指纹_虚拟BatteryManagerCharging` + `ChargingTime` + `DischargingTime` + `Level`（**4 项**） | `browser_vip_fingerprint_battery` | handler 四个方法全调（`:869-872`） |
| `指纹_虚拟Canvas_随机` / `指纹_虚拟WebGL_随机` / `指纹_虚拟Audio_随机` | `browser_vip_fingerprint_canvas` / `_webgl` / `_audio` | 均调 `指纹_虚拟X_随机(min,max,seed)`（`:751/763/775`） |
| `指纹_虚拟Canvas_定值` / `WebGL_定值` / `Audio_定值` | `browser_vip_fingerprint_canvas_fixed` / `_webgl_fixed` / `_audio_fixed` | 一对一 |
| `指纹_虚拟Languages` | **`browser_fingerprint {action:set_batch, languages}`** | `MCP_Server_Core.wsv:2233-2237` 读 `languages` 并调 `指纹_虚拟Languages`。**原脚本判为缺口，是漏看了 `set_batch` 批量入口** |
| `指纹_虚拟Webglvendor` / `指纹_虚拟Webglrenderer` | **`browser_fingerprint {action:set_batch, webgl_vendor/webgl_renderer}`** | `:2239-2249` 实调两者的内核方法 |
| `指纹_虚拟Webdriver` | **`browser_fingerprint {action:set_batch, webdriver}`** | `:2270` 实调；另 `browser_reverse_setup {disable_automation_flag}` 与 `browser_antidetect_presets{stealth}` 描述均含"去webdriver/移除webdriver标志" |
| `指纹_虚拟定位` | `browser_vip_fingerprint_geolocation` / `browser_fingerprint {action:geolocation}` | `MCP_Server_VIP.wsv:726` 调 `指纹_虚拟定位(...)` |
| `指纹_虚拟Date时区` | `browser_vip_fingerprint_timezone` | `MCP_Server_VIP.wsv:696` 调 `指纹_虚拟Date时区(offset_h,offset_m,name,iana)` |
| `指纹_虚拟AppVersion` / `AppCodeName` / `AppName` | `browser_fingerprint_appversion` / `_appcodename` / `_appname` | 一对一命名对应（`MCP_Server_VIP.wsv:454` 等） |
| `指纹_虚拟Plugins` / `CookieEnabled` / `JavaEnabled` / `OnLine` | `browser_fingerprint_plugins` / `_cookie_enabled` / `_java_enabled` / `_online` | 一对一（`MCP_Server_VIP.wsv:345/380/397/419`） |
| `指纹_虚拟AudioInput设备` / `AudioOutput设备` / `VideoInput设备`（**3 项**） | `browser_vip_fingerprint_media_devices {target:audio_input/audio_output/video_input}` | handler 按 `target` 分派到三个内核方法（`:887/895` 等） |
| `指纹_虚拟CSS字体指纹` / `Canvas字体指纹` | `browser_vip_fingerprint_font` / `_canvas_font` | `MCP_Server_VIP.wsv:793/806` 实调 |
| `指纹_虚拟Rect` | `browser_vip_fingerprint_rect` | 一对一（`:548`） |
| `指纹_虚拟Viewport` / `屏幕XY` / `DevicePixelRatio` | `browser_vip_fingerprint_viewport` / `browser_fingerprint_screen_xy` / `browser_fingerprint_pixel_ratio` | 一对一命名对应 |
| `指纹_虚拟UserAgent` | `browser_fingerprint_ua` | `MCP_Server_Core.wsv:2218` 经 `类_FBrowserVIP_UA数据` 调 `指纹_虚拟UserAgent`；工具支持 ua/platform/accept_lang/architecture 等完整字段 |
| `指纹_虚拟WebrtcIP` | `browser_vip_fingerprint_webrtc` | 一对一 |
| `指纹_设置SSL加密套件` | `browser_vip_fingerprint_ssl` | 一对一 |
| `指纹_启用触摸事件` | `browser_vip_touch_emulation` / `browser_fingerprint_touch_enable` | `MCP_Server_VIP.wsv:1379` 实调 `指纹_启用触摸事件(enable,max_points)` |
| `指纹_取调用计数` | `browser_fingerprint {action:count}` | `MCP_Server_Core.wsv:2075` 返回 `指纹_取调用计数 ()`（**注**：工具描述写作"查当前生效项数"，与实现不符，建议修正文案） |
| `指纹_虚拟屏幕方向` | `browser_vip_orientation` | 一对一（`MCP_Server_VIP.wsv:1426`） |
| `清理数据` | `browser_fingerprint {action:clear}` | 类库语义为"清理全部 VIP 设置的参数（指纹/代理/wss/debugger/isTrusted）"；`browser_fingerprint` 描述含 `clear 清空`，方向一致 |
| `高级_发送鼠标事件` / `高级鼠标_单击` `_按下` `_放开` `_滚轮滚动` `_移动`（**5 项**） | `browser_vip_mouse_click` / `_press` / `_release` / `_wheel` / `_move` | 一对一命名对应，描述均为"VIP输入: 内核级鼠标X，经CEF内核注入真实输入事件" |
| `高级_发送键盘事件` / `高级键盘_单击` `_按下` `_放开` `_输入字符` `_输入文本`（**5 项**） | `browser_vip_key_click` / `_press` / `_release` / `_input` / `_type` | 一对一命名对应（另有 `browser_key_event` 作为非 VIP 回退） |
| `高级_发送触摸事件` / `高级触摸_按下` `_放开` `_移动` | `browser_touch_press` / `_release` / `_move` | 一对一（CDP 级触摸） |
| `高级触摸_取消` | `browser_vip_touch_cancel` | 一对一 |
| `高级触摸_单击` | `browser_touch_press` + `browser_touch_release` | CDP 触摸"单击" = `touchStart`+`touchEnd`，两步组合即等价（非一次性调用，故未列缺口） |
| `高级_启用执行环境` | `browser_vip_enable_js_env` | 一对一 |
| `高级_取当前环境ID清单` | `browser_vip_get_js_env_ids` | 一对一 |
| `高级_执行JS` / `高级_执行JS_主框架` / `高级_执行JS_框架ID` | `browser_evaluate` / `browser_execute_js` / `browser_vip_execute_js_context {frame_id, context_id}` | `browser_vip_execute_js_context` schema 明确含 `code + context_id + frame_id`，直接覆盖"框架ID"维度；主框架为默认执行目标 |
| `高级_设置代理` / `高级_清空代理` | `browser_set_s5_proxy` / `browser_vip_clear_s5_proxy`（+`browser_clear_proxy`） | `browser_set_s5_proxy` 描述"VIP代理: 设置SOCKS5代理…username/password可选认证"，正对应类库"赞助会员才可用的带认证 S5" |
| `高级_网页截图` | `browser_screenshot` | 描述含 `format/width/height/x/y/scale` 裁剪缩放，语义覆盖 |
| `高级_创建标签浏览器` | `browser_create`（`browser_create_tab` 被禁用并给出替代） | 工具描述"新建一个可见浏览器窗口…需要浏览器级隔离时使用"；`browser_create_tab` 禁用文案明确指向 `browser_create` 作为替代 |

---

## 3. 不适用 / 平台限制（27 项）

| 类库方法 | 原因 |
|---|---|
| `移动窗口`（类_FBrowser_浏览器） | **平台限制**。工具 `browser_move_window` **已存在**，但 handler 直接返回失败："⛔ 嵌入式GUI浏览器不支持 move_window \| 窗口尺寸由主窗口自动管理"（`MCP_Server_Core.wsv:5185-5188`）。同族 `browser_set_auto_resize` 亦同样恒失败（`adjust_layout` 统一管理）。**结论：不属于缺口，属于架构决定**；若将来要开放，需先确认嵌入式子窗口能否脱离容器布局独立定位 |
| `FBrowser_初始化` | 初始化期一次性调用，且 MCP 服务器的生命周期由 `main.wsv` 独占管理（`main.wsv:98`） |
| `FBrowser_初始化_设置V8环境默认堆栈大小` | 必须在 `FBrowser_初始化` 之前设置，进程启动后不可改 |
| `FBrowser_初始化_设置内存释放` | 同上（初始化期策略配置） |
| `FBrowser_初始化_设置守护` | 同上（初始化期守护进程策略） |
| `FBrowser_设置程序DPI模式` | **平台限制**：DPI 感知必须在**任何窗口创建前**设置，运行期调用无效；且 GUI 主窗口已由产品决定 DPI 模式 |
| `FBrowser_消息循环_执行` | MCP 由 `main.wsv`/火山运行时独占消息循环，暴露给 MCP 客户端将直接死锁 |
| `FBrowser_消息循环_运行` | 同上 |
| `FBrowser_消息循环_退出` | 同上（退出即终结服务器进程，语义已被 `browser_shutdown` 安全接管） |
| `FBrowser_消息循环_设置系统模式` | 同上（消息循环模式属进程级引导配置） |
| `启用自带调试提示` | 开发期开关，对 MCP 客户端无意义 |
| `FBrowser_命令行_创建` | 初始化期内部构造 API（创建命令行对象），非用户能力 |
| `FBrowser_命令行_取全局` | 初始化期内部读取 API；若需观测已在 `main.wsv:469` 以 `app_startup_cmdline` 事件暴露 |
| `插入值`（PrependWrapper） | 调试器包装用途（"gdb --args" 风格），且类库实现有误——方法体调的是 `AppendArgument` 而非 PrependWrapper（`FBroLib.wsv:1870`） |
| `启用单进程模式` | 类库自注"只为了方便多进程模拟调试，仅调试模式下有用，单进程模式存在各种问题，不建议发布软件使用"；且与独立缓存互斥 |
| `启用录音` | 初始化期命令行开关（`enable-speech-input`），且 MCP 无人值守场景无麦克风需求 |
| `启用摄像头` | 初始化期命令行开关（`enable-media-stream`）；相关权限感知已由 `browser_collect {event_permission_enable}` + `browser_permission_spoof` 覆盖 |
| `FBrowser_Parser_写入JSON` | 纯离线工具函数（把 `类_FBrowser_值` 序列化为 JSON 文本）；MCP 侧全程使用 `YYJSON` 且结果直接以 JSON 返回 |
| `FBrowser_Parser_解析JSON` | 同上（反序列化） |
| `FBrowser_Parser_字节值解析为JSON` | 同上 |
| `FBrowser_启用异常收集` | **类库自注失效**："火山版本内置已经设置了，所有这个没用"（`FBroLib.wsv:531`）；实际异常已由 `app_v8_exception` 事件 + `browser_reverse_pause_on_exceptions` 覆盖 |
| `异常收集回调模板函数` | 同上的模板占位函数 |
| `类_初始化`（类_FBrowser_应用事件 / 服务器事件 / JS交互事件 / 资源过滤器 / 各类回调类） | 火山类生命周期方法，由运行时自动调用，无用户语义 |
| `类_清理`（同上，共 12 个类各 1 项） | 同上 |
| `获取默认事件`（类_FBrowser_应用事件） | 内部默认事件对象获取 API |
| `逐字分割`（类_FBrowserVIP_控制器） | 纯离线字符串工具函数，与浏览器能力无关 |
| `指纹_虚拟内核功能` | **类库已弃用**："注释 = 弃用，VIP功能…通过内核版本号虚拟当前浏览器内核"；现由 `browser_vip_set_css_version` / `_set_web_version` / `_set_v8_version` 分别承接 |

---

## 4. 方法论备注（对原脚本判据的修正）

1. **判据缺陷**：原脚本以"类库中文方法名是否出现在任意工具描述文本"为唯一判据，导致两类系统性误报——
   - **批量工具**：`browser_vip_disable_console` 一个工具吃掉 15 个候选；`browser_vip_fingerprint_screen` 吃掉 4 个；`browser_vip_fingerprint_product` 吃掉 4 个（含原脚本判缺口的 `指纹_虚拟Vendor`）。
   - **参数化入口**：`browser_reload {ignore_cache}`、`browser_fingerprint {action:set_batch, languages/webgl_vendor/webgl_renderer/webdriver}`、`browser_vip_execute_js_context {frame_id}`——能力在**参数**里而不在描述词面里。
2. **正确的判据**：应反向建立"内核 API → handler 调用点"映射，即 grep `src/**/*.wsv` 中 `类库方法名` 的直接调用（如 `指纹_虚拟Languages (`、`reload_ignore_cache (`），命中即已覆盖。本次核对即采用此法。
3. **死工具的识别**：不能只看`命令注册表`——`browser_get_window_style` 等仅在 `MCP_Server.wsv:10257` 的规范名 if-else 链上。真正的"名存实亡"工具会**返回 `命令失败` 且文案含 ⛔**（目前 4 个：`browser_move_window`、`browser_set_auto_resize`、`browser_close_try`、`browser_create_tab`/`browser_task_runner_post`），它们对**缺口判定有影响**：有工具名 ≠ 有能力，需单独核对 handler 是否真调内核。
4. **本次未覆盖范围**：原报告 363 个候选中，非优先类尚有约 153 个候选未逐项核对（如 `类_FBrowser_服务器事件`、`类_FBrowser_URL请求事件`、各数组/回调类、`FBrowserVIP全局功能` 等）。按本次 72.4% 的误报率，这些类中大部分为事件回调与容器类型，预计真缺口很少。
