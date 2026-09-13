# 类库"真缺口"清单 — 第二轮复核（覆盖路径复查）

> 复核对象：`_audit/_classlib_gap_confirmed.md` 第 1 节"已确认真缺口（31 项）"。
> 复核目标：**专门排查"其实已由请求级公共参数 / 批量工具 / 参数化入口覆盖"的误报**（上一版已证实 `browser_select` 因漏看 `browser_id` 公共参数而误报）。
> 只读分析，未修改 `src\` 下任何文件。真机验证由主代理执行，本报告只给**静态证据**与判定。

---

## 0. 方法与口径（务必先读，影响所有行号）

### 0.1 证据快照

| 文件 | 快照 mtime | 字节数 |
|---|---|---|
| `src\MCP_Server.wsv` | 2026-09-13 01:36:03 | 607881 |
| `src\MCP_Server_Core.wsv` | 2026-09-13 01:33:23 | 443949 |
| `src\MCP_BrowserEvents.wsv` | 2026-09-13 01:32:29 | 98592 |
| `src\MCP_Server_System.wsv` | 2026-09-13 01:30:58 | 9113 |
| `src\main.wsv` | 2026-09-13 01:30:48 | 38667 |
| `src\MCP_Server_VIP.wsv` | 2026-09-13 01:29:06 | 89628 |
| `src\MCP_Server_Reverse.wsv` | 2026-09-13 01:29:40 | 117665 |
| `资料\类库\FBrowser浏览器\FBroLib.wsv` | 只读基准 | 287774 |

⚠ **并发修改警告**：复核期间观察到 `src\` 正在被改动（本会话开始时 `MCP_Server.wsv` 为 607561 B，中途变为 607881 B；`MCP_Kernel.wsv` 在本会话内刚被写入）。因此本报告所有行号**以 01:29–01:38 快照为准**，引用时请优先用**代码锚点文本**（下表每项都给了原文片段），不要只信行号。

### 0.2 行号口径

本报告行号来自 **LF 原始分行**（`Select-String` / `[IO.File]::ReadAllText().Split("\n")`），两者互相验证一致（该文件为纯 LF，无 CR）。

⚠ **DSH 的 `read`/`grep` 工具在 `MCP_Server.wsv` 上会少计若干行**（本会话实测：同一位置 read/grep 报 5229，真实为 5232；报 7530，真实为 7533；报 10231，真实为 10234）——上一版报告与用户任务描述里的 `10229-10233` / `7530` 就是 read/grep 口径。**本报告一律用真实 LF 口径（+3）**，与上一版相差 3 行的引用请自行对齐。

### 0.3 判定标准（本次统一采用，共 6 条覆盖路径）

| # | 覆盖路径 | 判据 |
|---|---|---|
| ① | **请求级公共参数** | 在 `执行浏览器命令` / sync-wait 辅助里**统一取出**、对全部工具生效的参数 |
| ② | **批量工具** | 工具的 `action`/`preset` 枚举或参数组已包含目标能力 |
| ③ | **参数化入口 / 直接调用** | `src\` 里能 grep 到该**类库方法名（或其包装名）的直接调用** |
| ④ | **通用 CDP 透传** | `browser_cdp_call` 可发任意 CDP 方法（🆕 本轮新增路径） |
| ⑤ | **现有工具组合** | ≥1 次调用可组合出等价结果（如 touch press+release、get_frames+execute_js_context） |
| ⑥ | **通用 JS 执行** | 能力可在页面 JS 内实现（`browser_execute_js` / `browser_evaluate`） |

**真缺口** = 6 条路径全不可达，且不属于平台/架构限制。**不适用** = 平台限制、初始化期一次性、内部 API、类库自身已失效、或作用于 MCP 无法持有的对象。

> 路径 ④⑤⑥ 是上一版**没有系统性使用**的判据，也是本轮新增误报的主要来源。

### 0.4 清单本身的算术问题（先说清）

上一版标题写"31 项"，但 **1.1/1.2/1.3 三张表实际只有 20 行**（3 + 5 + 12，而 1.3 标题却写"低价值（23）"）。按**类库方法条目**计为 **30 条**（3+11+15 见下）。即：**20 行 / 30 条方法 / 自称 31 项**，存在 1 条计数差异。本报告按**逐行（20 行）+ 逐方法（30 条）**双口径给出结论。

---

## 1. 🎯 请求级公共参数清单（本轮最有价值产出）

这些参数**由请求入口统一取出**，因此 **301 个工具天生全部支持**，任何工具都不需要在自身 schema 里声明。

| 参数名 | 语义 | 作用范围 | 出处（快照行号 + 锚点） |
|---|---|---|---|
| **`browser_id`** | 本次请求的目标浏览器 ID。写入静态 `目标浏览器ID`；`取主浏览器()` 优先按它解析实例；`0`/缺省 = 主浏览器；请求结束**恢复原值**（嵌套 `batch` 时保证外层上下文不被污染）；ID 不存在时 `取主浏览器()` 返回空并打日志，工具走"无浏览器"失败分支 | **全部 301 个工具**（只要该工具经 `取主浏览器()` 取实例——核心/填表/VIP/内核/逆向/系统/编排全部分派器均如此） | 赋值：`MCP_Server.wsv:10232-10236`（`请求浏览器ID = yyjson取整数 (参数JSON, "browser_id")` → `目标浏览器ID = 请求浏览器ID`）；恢复：`10296` / `10331` / `10338`；消费：`取主浏览器` **7533**（`7536: 如果 (目标浏览器ID > 0)` → `取浏览器ByID`）；CDP 侧同源判断 `1560` |
| **`max_ms`** | 服务端 sync-wait 的阻塞上限（毫秒）。>0 覆盖默认值；硬钳制上限 **300000**（5 分钟，防单请求长期占用执行线程） | 全部**返回 `_async` 的工具**（即走 `命令成功_异步` / `尝试同步跟随异步响应` 的异步族），也用于 `browser_wait` 等内部轮询 | 读取：`取同步等待毫秒` **5386**，读键 `5393: 自定义 = yyjson取整数 (参数JSON, "max_ms")`，钳制 `5396-5399`；调用点 `尝试同步跟随异步响应` **6067**、`命令成功_异步` **6129**；超时提示文案 `6085`/`6142` |
| **`sync_wait`** | **强制**服务端阻塞等待异步结果（对不在默认同步白名单里的工具生效）。显式 `sync_wait:true` 时若目标 URL 是本机自托管页面，被**死锁防护**降级为异步（否则必超时） | 全部异步族工具 | `应同步等待` **5232**；读键 `5242: 如果 (yyjson取逻辑 (参数JSON, "sync_wait"))`；防死锁 `5245-5252` |
| **`async_only`** | **强制异步**：跳过全部 sync-wait，立即返回 `{_async:true, task_id}`。在 `应同步等待` 中**最先判断**，优先级高于 `sync_wait` 与工具默认表 | 全部异步族工具；`batch` 另读它来关闭"子命令自动跟随异步" | `应同步等待` **5238**；`尝试同步跟随异步响应` **6052**；`batch` 分支 `MCP_Server.wsv:1425`；各分派器内 `wait_for_load` 联动见 `MCP_Server_Core.wsv:52` |
| **`wait_for_load`** | 载入等待开关（默认真，仅 `browser_navigate`/`browser_reload` 生效）。传 `false`/`0` 或配 `async_only:true` 跳过同步等待 | 仅 `browser_navigate` / `browser_reload`（半公共参数） | `应同步等待` 读键 `5264`；分派器 `MCP_Server_Core.wsv:51`（navigate）/`:153`（reload） |

**补充说明（不是公共参数，但同属"统一通道"，勿混淆）**：

- `参数JSON` 中的 **`url`** 只在 `应同步等待` 里被读，用于"是否本机自托管 URL"的死锁判定（`5246`/`5276`），**不是**通用参数。
- **`mcp_result` 的 `consume`**、**`browser_collect` 的 `action`** 等仍是各自工具的参数，未公共化。

**通用旁路通道（等价于"公共能力"，本轮新增判据）**：

| 通道 | 能力 | 出处 |
|---|---|---|
| `browser_cdp_call` | **任意 CDP 方法透传**。唯一校验是"方法名必须含 `.`"（防无点号方法名挂起阻塞），无白名单、无域限制 | 注册 `MCP_Server.wsv:9512`；handler `MCP_Server_Core.wsv:4296-4311`（`返回 (MCP_命令服务器.执行CDP命令 (命令ID, cdpMethod, 参数JSON))`） |
| `browser_execute_js` / `browser_evaluate` / `browser_reverse_evaluate_silent` | **任意页面 JS**，含 DOM/Storage/IndexedDB 操作 | `MCP_Server_Core.wsv` JS 族 |
| `batch` | 任意子命令序列，一次下发（可承载"逐框架执行"等多步组合） | `MCP_Server.wsv:1429-1458`；注册 `9440` 区（`"batch"`） |

### 1.1 一个附带发现：公共参数对客户端不可见

`browser_id` 已生效，但 **301 个工具里只有 4 个在描述文本里提到它**（`browser_create` `9317`、`browser_close` `9318`、`browser_list` `9320`、`browser_get_id` `9338` 区），其中**只有 `browser_close` 把它声明为真正的 schema 参数**。

→ 建议（纯契约层、无内核改动）：在所有工具 schema 统一注入 `browser_id` 属性，或在 `tools/list` 顶层/`mcp_help` 里显式声明"`browser_id` 为请求级公共参数"。否则 AI 客户端**看不到也只能猜**——这正是上一版把 `browser_select` 误判为 P0 真缺口的根因。

---

## 2. 逐项复核表（20 行 / 30 条类库方法）

值 `上一版判定` 取自 `_classlib_gap_confirmed.md` 第 1 节；`优先级` 为**修正后**优先级。

### 2.1 上一版"高价值（3 行 / 4 条方法）"

| # | 类库方法 | 上一版判定 | 本次判定 | 覆盖路径 / 缺失依据 | 建议工具名 | 优先级 |
|---|---|---|---|---|---|---|
| 1 | `FBrowser_浏览器_通过ID取浏览器` | 真缺口 **高** | **已覆盖** | **路径①**：`browser_id` 是请求级公共参数（`MCP_Server.wsv:10232-10236`），`取主浏览器()`（`7533`，判 `7536`）已按 `目标浏览器ID` 取实例 → 301 个工具全部天然支持多浏览器。上一版"118 处 `取主浏览器()` 忽略它"的判断**错误**：`取主浏览器()` 本身就是该字段的消费点。与真机实测（b1/b2 隔离正确）一致 | — | 已消除（上一版 P0） |
| 2 | `FBrowser_创建后台浏览器` + `FBrowser_创建后台浏览器_同步` | 真缺口 **高** | **真缺口**（维持） | 全 `src` 零命中 `后台浏览器` / `FBroHsCreateBackground`；唯一创建工具 `browser_create`（`MCP_Server_Core.wsv:352`）经 `main.wsv:209 FBrowser_创建浏览器 (url, 窗口信息, ...)` 建**可见顶层窗口**（`窗口信息.父窗口句柄 = 0`，`main.wsv:202`），无 `background`/`headless` 参数（schema 仅 `url`，`MCP_Server.wsv:9317`）；`browser_task_runner_post` 恒失败（`MCP_Server_System.wsv:20-23`），而 `_同步` 版**必须**经 `FBrowser_任务运行器_投递任务` 在 UI 线程调用；路径④ CDP 无"无窗口浏览器"等价物 | `browser_create {background:true}`（推荐并入现有创建工具）或 `browser_create_background` | **P0** |
| 3 | `FBrowser_浏览器_清理缓存` | 真缺口 **高** | **已覆盖**（方法级；残留降级为参数增强） | **路径③（直接调用，上一版漏看）**：`browser_clear_cache_browser`（`MCP_Server.wsv:9335`，确实无 schema 参数）→ handler `MCP_Server_Core.wsv:5528-5543`，**第 5539 行 `browser.清理缓存 (, , , 清理回调)`** —— 就是该类库方法本体，只是四个参数全走默认（`清理对象 = 清理缓存.全部`、`存储类型 = 缓存类型.全部`）。**路径④⑥**：按 origin / 按存储类别的细粒度清理可由 `browser_cdp_call {method:"Storage.clearDataForOrigin", params:{origin, storageTypes}}`，或 `browser_execute_js` 内 `localStorage.clear()` / `indexedDB.deleteDatabase()` 达成。→ **"无任何工具能清 localStorage"的判断不成立；真正缺的只是参数维度** | 增强 `browser_clear_cache_browser {origin, targets[], storage_type}` | 已消除（上一版 P0）→ 增强 **P2** |

### 2.2 上一版"中价值（5 行 / 11 条方法）"

| # | 类库方法 | 上一版判定 | 本次判定 | 覆盖路径 / 缺失依据 | 建议工具名 | 优先级 |
|---|---|---|---|---|---|---|
| 4 | `设置远程调试端口` | 真缺口 **中** | **真缺口**（维持，价值下调） | 全 `src` 零命中 `远程调试`/`remote_debug`/`调试端口`；`main.wsv:456 即将处理命令行` 形参里有现成的 `命令行 <类型 = 类_FBrowser_命令行>`，但方法体只做 `记录应用监控事件 ("app_startup_cmdline", ...)`（`467`），**从不调用命令行对象任何方法**；`类_FBrowser_命令行.置值`（`FBroLib.wsv:1828`，AppendSwitch）全项目零调用；路径④ CDP 无法在运行期开外部调试端口 | `browser_set_remote_debug_port {port}`（写配置 + 明确返回"需重启"） | **P2**（原 P1） |
| 5 | `显示隐藏窗口` | 真缺口 **中** | **真缺口**（维持） | 全 `src` 零命中 `显示隐藏`/`ShowWindows`/`show_window`；`browser_set_window_style`（`MCP_Server_System.wsv:71-93`）调的是 `browser.置窗口属性`（SetWindowLongPtr），**不是** `FBroHsBrowserHost_ShowWindows`，且源码自警"省略 style 会清掉含 WS_VISIBLE 的全部位，可能使窗口不可见/不可用"——确属反例而非替代；路径④ CDP 无窗口显隐能力 | `browser_show_window {show}` | **P1** |
| 6 | `高级_设置触发鼠标触摸事件` | 真缺口 **中** | **已覆盖（CDP 旁路，⚠需真机确认）** | 该类库方法（`FBroVip.wsv:623`，签名 `(启用 逻辑型, 配置 整数)`，`0=MOBILE / 1=DESKTOP`）与 CDP **`Emulation.setEmitTouchEventsForMouse {enabled, configuration:"mobile"\|"desktop"}`** 语义一一对应 → **路径④** `browser_cdp_call {method:"Emulation.setEmitTouchEventsForMouse", params:"{\"enabled\":true,\"configuration\":\"mobile\"}"}`（通道见 `MCP_Server.wsv:9512` / `MCP_Server_Core.wsv:4296-4311`，无域白名单）。**本项是本轮唯一"依赖 CDP 实现情况"的判定**：`browser_cdp_call` 只保证"能发"，不保证 CEF 实现了该 CDP 方法。若真机返回 `method not found`，则回退为真缺口 | 验证失败才做：`browser_set_touch_trigger {enable, mode}`，或并入 `browser_vip_touch_emulation` 的 action | **P1（待验证）** |
| 7 | `添加菜单` `添加子菜单` `添加分隔栏` `添加Check菜单` `添加Radio菜单` `选中状态` `选中状态_索引`（7 条） | 真缺口 **中** | **真缺口**（维持） | 上一版依据经复核**成立且证据更强**：`浏览器_即将打开菜单` 回调（`MCP_BrowserEvents.wsv:2654-2664`）形参里有 `菜单模式 <类型 = 类_FBrowser_菜单模式>`，但方法体**只有** `如果 (是否监控菜单事件) { 记录监控事件 (真, "context_menu_opening", ...) }` —— **从不写入 MenuModel**；同族 `浏览器_菜单被调用`/`_菜单被点击`/`_菜单被关闭`（`2666`/`2681`/`2700`）同样只记录。`browser_kernel_menu` 作用相反（屏蔽，`MCP_Kernel.wsv:514-535`）；`browser_collect event_menu_enable` 只观察。路径④ CDP **无**右键菜单模型定制能力 | `browser_menu_build {action:add_item\|add_submenu\|add_separator\|add_check\|add_radio\|check\|clear, id, label, items[], accelerator}` | **P1** |
| 8 | `启用无头模式` | 真缺口 **中** | **真缺口**（维持；类库方法本身有缺陷，须绕开） | `src` 中 `headless` 仅出现于 MCP 服务器**自身**的 stdio 传输开关（`MCP_Stdio.wsv:225`），与浏览器无关；`browser_create` 无 headless 参数；**类库方法实现有误**：`FBroLib.wsv:1909-1914` 方法体调的是 `FBroHsCommandLine_EnableAutoplayPoliey`，**并未设置 `--headless`**（与上一版判断一致，独立复核确认）。正确做法是 `类_FBrowser_命令行.置值("headless")`（`FBroLib.wsv:1828`），该项目零调用 | **不建议单独做**：需求由 #2 后台浏览器满足；若保留则须用 `置值("headless")` 并在文档写明"进程级、需重启、与嵌入式容器渲染冲突" | **P3**（原 P2） |

### 2.3 上一版"低价值（12 行 / 15 条方法）"

| # | 类库方法 | 上一版判定 | 本次判定 | 覆盖路径 / 缺失依据 | 建议工具名 | 优先级 |
|---|---|---|---|---|---|---|
| 9 | `设置快捷键` + `设置快捷键_索引` | 真缺口 低 | **真缺口**（依附 #7） | 全 `src` 零命中 `设置快捷键`/`Accelerator`/`shortcut`；`CefMenuModel::SetAccelerator` 只能作用于 MCP 无法持有的 MenuModel 对象 | 并入 #7 的 `accelerator:{key,ctrl,shift,alt}` | P3 |
| 10 | `移除快捷键` + `移除快捷键_索引` | 真缺口 低 | **真缺口**（依附 #7） | 同上（`RemoveAccelerator`） | #7 的 `action=remove_accel` | P3 |
| 11 | `存在快捷键` + `存在快捷键_索引` | 真缺口 低 | **不适用**（改判） | `HasAccelerator` / `HasAcceleratorAt` 查询的是**本地构建的 `类_FBrowser_菜单模式` 对象**（`FBroLib.wsv:3451/3457`）内部的加速键表。MCP 跨请求无法持有该对象，且（见 #7）根本没有菜单写回通道 → **无对象可查，无用户语义** | — | — |
| 12 | `高级_执行JS_全部框架` | 真缺口 低 | **已覆盖（组合）**（改判） | **路径⑤**：`browser_get_frames`（`MCP_Server.wsv:9356`，handler 逐个 `f对象.加入文本成员 ("frame_id", frame.取框架ID ())`，`MCP_Server_Core.wsv:5161`）取得全部 `frame_id` 后，对每个框架调 `browser_vip_execute_js_context {frame_id, code}`（`MCP_Server_VIP.wsv:1244`）；或一次 `batch` 下发。**上一版自己也写了"或遍历 browser_frame_names 后逐个…后者无需改内核，建议优先"——按同一标准即应判已覆盖** | 可选便利封装（非缺口） | — |
| 13 | `高级_执行JS_框架序号` | 真缺口 低 | **已覆盖（等价参数）**（改判） | **路径③⑤**：`browser_get_frames` 返回**有序** `frame_id` 表，序号→id 一次换算即可（无需 `取框架名称()`，上一版所述换算成本不存在）；另有 `context_id`（整数环境序号，`MCP_Server_VIP.wsv:1242`）这一**原生序号维度**参数，配合 `browser_vip_get_js_env_ids` 使用 | 可选：给 `browser_vip_execute_js_context` 加 `frame_index` | — |
| 14 | `禁用GPU` | 真缺口 低 | **真缺口**（维持） | 全 `src` 零命中 `禁用GPU`/`DisableGpu`；`FBroLib.wsv:1924`；初始化期一次性、CDP 无等价 | `browser_set_gpu {disable, disable_cache, ignore_blocklist}`（三项合一） | P3 |
| 15 | `禁用GPU缓存` | 真缺口 低 | **真缺口**（维持） | 同上（`FBroLib.wsv:1931`，`DisableGpuCache`） | 同上 | P3 |
| 16 | `忽略GPU禁用清单` | 真缺口 低 | **真缺口**（维持） | 同上（`FBroLib.wsv:1938`，`DisableGpuBlockList`） | 同上 | P3 |
| 17 | `打开对话框` | 真缺口 低 | **不适用**（改判：产品决策） | `browser_file_dialog`（`MCP_Server_Core.wsv:5339-5365`）**刻意**不弹原生对话框，注释原文："安全设计: 传 path 参数直接返回该路径(验证存在性), 不弹任何窗口(**不调用原生OS文件对话框, 其会阻塞控制台**)"，只做 `验证安全路径` + `文件是否存在`。MCP 无人值守场景弹窗是负资产 → 属架构决定而非能力缺失（上一版"建议保持现状"已隐含此意） | —（仅需在工具描述里写明"=程序化路径校验"） | — |
| 18 | `FBrowser_JS交互_删除` | 真缺口 低 | **已覆盖**（改判） | **路径④**：其内核 API 即 CDP `Runtime.removeBinding {name}` → `browser_cdp_call {method:"Runtime.removeBinding", params:"{\"name\":\"xxx\"}"}`。**旁证该通道确实可用**：同域的 `Runtime.addBinding` 已被 `browser_reverse_add_binding`（`MCP_Server_Reverse.wsv:1471-1493`，`执行V8CDP命令 (..., "Runtime.addBinding", ...)`）跑通，说明 Runtime 域 CDP 在该内核上工作 | 建议给 `browser_reverse_add_binding` 加 `action=add/remove`（便利封装，非缺口） | — |
| 19 | `指纹_清空调用计数` | 真缺口 低 | **真缺口**（维持） | 全 `src` 零命中 `清空调用计数`（唯一命中是 `MCP_Server_Core.wsv:2031` 的 `vip_ctrl.指纹_取调用计数 ()`）；`FBroVip.wsv:211`；内核内部计数器，路径④⑥均无等价 | `browser_fingerprint action=clear_count` | P3 |
| 20 | `FBrowser_Parser_取数据URI` | 真缺口 低 | **已覆盖**（改判；二进制输入降级为参数增强） | **路径③⑥**：`browser_base64_encode`（`MCP_Server.wsv:9408` → `MCP_Server_Core.wsv:4948-4958` → **直接调 `FBrowser_Parser_Base64编码 (data)`**）产出 base64；`data:<mime>;base64,` 前缀是纯字符串拼接（AI 侧或 `browser_execute_js` 一行即可）。上一版自评"AI 侧可自行拼 base64"——按同一标准即已覆盖 | 增强 `browser_base64_encode` 支持 `file`/字节集输入（覆盖任意二进制 → data URI 的场景） | 增强 **P3** |

### 2.4 逐项结论汇总

| 判定 | 行数 | 方法条目 | 说明 |
|---|---|---|---|
| **已覆盖**（改判） | 7 | 7 | #1 #3 #6(待验证) #12 #13 #18 #20 |
| **真缺口**（维持） | 11 | 20 | #2 #4 #5 #7(7条) #8 #9 #10(各2条) #14 #15 #16 #19 |
| **不适用**（改判） | 2 | 3 | #11(2条) #17 |
| 合计 | 20 | 30 | 上一版自称 31 项，表内实为 30 条方法条目 |

---

## 3. 修正后的真缺口清单（按优先级）

> 共 **11 行 / 20 条类库方法**，去重为 **8 个建议工具**。

### P0 — 后台浏览器（唯一剩余的高价值缺口）

| 项 | 内容 |
|---|---|
| 类库方法 | `FBrowser_创建后台浏览器`（`FBroLib.wsv:594`，返回逻辑型）/ `FBrowser_创建后台浏览器_同步`（`:615`，返回 `类_FBrowser_浏览器`）/ `FBrowser_创建浏览器_同步`（`:573`） |
| 建议工具 | `browser_create {background:true, url?, tag?}`（**优先并入现有创建工具**，不新增工具名）或独立 `browser_create_background` |
| 实现要点 | ① 后台浏览器**无窗口无句柄**，是批量取数的最优解（类库注释：优于无头模式、占用更低）；② `_同步` 版**必须在 UI 线程经 `FBrowser_任务运行器_投递任务` 调用**，而 `browser_task_runner_post` 现被硬禁用（`MCP_Server_System.wsv:20-23`）——**推荐绕开它**，复用现有"UI 时钟握手"通道：`browser_create` 已用 `待创建URL` + `待创建完成` 双字段与 `main.wsv` 的 UI 时钟交互（`MCP_Server_Core.wsv:372-416` / `main.wsv:175-213`），只需**新增一个"待创建后台"标志与 `待创建标识` 字段**，在 `main.wsv:209` 处按标志改调 `FBrowser_创建后台浏览器`；③ 类库 `标识` 参数（用户标识）可直接支撑"按 tag 寻址"，与已覆盖的 `browser_id` 公共参数配合；④ 非 VIP 版 `FBrowser_创建后台浏览器` 即可用，无需赞助 |
| 风险 | 后台浏览器**只能设置静态事件或动态事件之一**（类库注释），需与 `类_MCP_浏览器事件` 的挂接方式对齐；`browser_list` / `browser_close` 对无窗口实例的适配需一并确认 |

### P1 — 右键菜单写回 + 窗口显隐

| 项 | 内容 |
|---|---|
| 3.1 `browser_menu_build` | 覆盖 7 条：`添加菜单` `添加子菜单` `添加分隔栏` `添加Check菜单` `添加Radio菜单` `选中状态` `选中状态_索引`（`类_FBrowser_菜单模式`，`FBroLib.wsv:3288`，含 `清空菜单:3313` / `添加分隔栏:3325` / `添加菜单:3331` / `添加Check菜单:3339` / `添加Radio菜单:3347` / `添加子菜单:3356` / `选中状态:3437` / `选中状态_索引:3444`）。**两条腿**：① 菜单模型构建器（`browser_menu_build {action, id, label, items[], accelerator, check}` 一次下发整棵菜单树）；② **在 `浏览器_即将打开菜单` 回调里把模型写回 CEF**——该回调形参已有 `菜单模式 <类型 = 类_FBrowser_菜单模式>`（`MCP_BrowserEvents.wsv:2658`），只需在 `记录监控事件` 之外增加"用户下发的菜单 JSON → 构建 MenuModel → 原地修改"的通道。**冲突处理**：`browser_kernel_menu action=disable` 的屏蔽逻辑与之互斥，需定义优先级（建议"有自定义菜单则不再屏蔽"）。优先级：中。 |
| 3.2 `browser_show_window {show}` | 1 条：`显示隐藏窗口`（`FBroLib.wsv:1071`）→ `FBroHsBrowserHost_ShowWindows`。实现要点：嵌入式容器布局 `adjust_layout` 可能在下次布局时**重新显示**窗口，故必须与 `浏览器容器` 状态同步（新增"用户请求隐藏"持久标志，布局时尊重它），并提供恢复入口（否则 AI 可能把窗口藏死；`browser_restore_gui` 现在只是容器重排，不足以恢复）。优先级：中。 |
| 3.3 ⚠ **待真机验证项**：触摸触发 | 先由主代理真机执行 `browser_cdp_call {method:"Emulation.setEmitTouchEventsForMouse", params:"{\"enabled\":true,\"configuration\":\"mobile\"}"}`。**成功 → #6 判"已覆盖"，本项从清单移除**；失败（`method not found` / 无响应）→ 补 `browser_set_touch_trigger {enable, mode}` 或并入 `browser_vip_touch_emulation` 的 action。注意类库要求"**在浏览器载入完成后调用**"。 |

### P2 — 启动期 / 细粒度参数

| 项 | 内容 |
|---|---|
| 4.1 `browser_set_remote_debug_port {port}` | 1 条：`设置远程调试端口`（`FBroLib.wsv:1916`）。实现要点：必须在 `浏览器_即将启动消息调度` 之前调用，而 `main.wsv:456 即将处理命令行` 已提供现成钩子（形参即 `类_FBrowser_命令行`）；做法 = 参数写配置 → 进程启动时钩子里读配置调 `设置远程调试端口` → 工具明确返回"需重启生效"。**价值提示**：MCP 内部已有 `browser_cdp_call` 全量 CDP 通道，本项唯一增量是**外部 Playwright/Puppeteer attach**，故优先级低于上一版评估。 |
| 4.2 增强 `browser_clear_cache_browser` | 类库 `清理缓存`（`FBroLib.wsv:1357`）**已在调用**（`MCP_Server_Core.wsv:5539`），只差暴露参数。加 `{origin, targets[], storage_type}` → `源地址` / `清理对象`（`#清理缓存_Appcache/Cookies/IndexedDB/LocalStorage/ServiceWorkers/WebSQL/CacheStorage` 位或）/ `存储类型`（`缓存类型.xxx`）。默认值分别是"当前 origin / 全部 / 全部"，工具描述需写清**默认会连 Cookie 一起清**（现状即如此，属隐性破坏性行为，建议顺手在描述里告警）。 |

### P3 — 低价值 / 可选

| 项 | 内容 |
|---|---|
| 5.1 `browser_set_gpu {disable, disable_cache, ignore_blocklist}` | 3 条：`禁用GPU`（`FBroLib.wsv:1924`）/ `禁用GPU缓存`（`:1931`）/ `忽略GPU禁用清单`（`:1938`）。初始化期一次性、需重启，同类库 `置值` 注入通道（与 4.1 共用配置机制）。 |
| 5.2 `browser_fingerprint action=clear_count` | 1 条：`指纹_清空调用计数`（`FBroVip.wsv:211`）。**顺手修正文档 bug**：`browser_fingerprint` 描述把 `count` 写成"查当前生效项数"，实际实现（`MCP_Server_Core.wsv:2031` `指纹_取调用计数 ()`）返回的是 `指纹_取调用计数`（API **调用次数**），描述与实际不符。 |
| 5.3 不建议单独实现 | `启用无头模式`（类库方法实现有误，且与嵌入式容器渲染冲突）→ 需求由 P0 后台浏览器覆盖。 |
| 5.4 可选便利封装（**非缺口**） | `browser_vip_execute_js_context {frame_index}`；`browser_reverse_add_binding {action:add\|remove}`；`browser_base64_encode` 支持 `file`/字节集输入；`浏览器容器` 缓存与 `browser_kernel_menu` 的联动文档。 |

---

## 4. 结论摘要

### 4.1 数量口径

| 口径 | 上一版"真缺口" | 维持真缺口 | 改判"已覆盖" | 改判"不适用" | **上一版误报率** |
|---|---|---|---|---|---|
| **逐行**（表内实际 20 行） | 20 | **11** | 7 | 2 | **9/20 = 45.0%** |
| **逐类库方法** | 30 | **20** | 7 | 3 | 10/30 = 33.3% |
| 保守口径（#6 触摸触发按"验证失败"计） | 20 | 12 | 6 | 2 | 8/20 = 40.0% |

> 上一版自称"31 项"，但三张表**只有 20 行 / 30 条方法条目**，且 1.3 标题写"低价值（23）"而表内只有 12 行 —— **清单本身存在计数不一致**，建议同步修正。

### 4.2 核心发现

1. **高价值池基本清空**：上一版 3 项"高价值真缺口"中 **2 项是误报**（`browser_select` 被请求级 `browser_id` 覆盖、`browser_clear_storage` 的类库方法早已被直接调用），仅 `browser_create_background` 一项成立。
2. **`browser_clear_storage` 是"半覆盖"的典型**：类库方法 `清理缓存` 在 `MCP_Server_Core.wsv:5539` **就被调用着**——上一版只看了工具 schema（确实无参数）就断定"缺失"，没有反向 grep 类库方法名的调用点，**正是任务指出的方法学问题的第二个实例**（第一个是 `browser_id`）。真正的缺口只是"参数没暴露"，属增强而非新工具。
3. **本轮新发现第 4~6 条覆盖路径，带来 3 项改判**：
   - **`browser_cdp_call` 是 CDP 全量透传**（唯一校验"方法名含点号"，无域白名单，`MCP_Server_Core.wsv:4296-4311`）——上一版只把它当"某个工具的替代品"，没把它当**系统性覆盖路径**。据此改判：`FBrowser_JS交互_删除`（CDP `Runtime.removeBinding`，且同域 `Runtime.addBinding` 已被 `browser_reverse_add_binding` 跑通）、`高级_设置触发鼠标触摸事件`（CDP `Emulation.setEmitTouchEventsForMouse`，待真机确认）。
   - **组合路径**（≥1 次调用可组合）：`高级_执行JS_全部框架` / `高级_执行JS_框架序号` —— 上一版在**同一份报告内**已把 `高级触摸_单击`（press+release 组合）判为"已覆盖"，却把同样可组合的"全部框架"判为真缺口，**标准不一致**。
   - **`browser_base64_encode` 已经是 `FBrowser_Parser_Base64编码` 的直接调用**，`data:` 前缀只是字符串拼接。
4. **反复出现的根因**：上一版的判据仍以"工具名/描述/参数表"为中心。凡是"能力在公共参数里、在 CDP 里、在组合调用里"的，都会被误判。**正确判据仍是任务给出的反向映射**：`grep 类库方法名 → handler 调用点`（本次新增 `清理缓存`、`Base64编码` 两处直接调用即为证）。
5. **公共参数可见性缺口（新问题，非类库缺口）**：`browser_id` 生效但 **301 个工具中仅 `browser_close` 声明它**，其余只在 3 处描述文本里提到 → AI 客户端难以发现。建议在 schema 层统一注入。

### 4.3 完整覆盖路径清单（供下一轮复用）

```
① 请求级公共参数：browser_id / max_ms / sync_wait / async_only / wait_for_load
② 批量工具：browser_vip_disable_console(15合1) / browser_vip_fingerprint_*(screen 4合1, product 4合1, battery 4合1, hardware 2合1) / browser_kernel_events_all / browser_antidetect_presets / browser_collect(event_* 21族) / browser_fingerprint(set_batch)
③ 参数化入口 + 类库方法直接调用：browser_reload{ignore_cache} / browser_vip_execute_js_context{frame_id,context_id} / browser_clear_cache_browser→清理缓存 / browser_base64_encode→Base64编码(直接调用)
④ 通用 CDP 透传：browser_cdp_call（任意 CDP 方法，无域白名单）
⑤ 现有工具组合：touch press+release / get_frames+execute_js_context / batch
⑥ 通用页面 JS：browser_execute_js / browser_evaluate / browser_reverse_evaluate_silent
```

---

## 5. 证据复现命令（只读）

```powershell
$src='C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src'

# 1) 请求级公共参数：browser_id
Select-String -Path "$src\MCP_Server.wsv" -Pattern 'yyjson取整数 \(参数JSON, "browser_id"\)|目标浏览器ID = 请求浏览器ID|方法 取主浏览器|如果 \(目标浏览器ID > 0\)'
# 2) 请求级公共参数：sync-wait 族
Select-String -Path "$src\MCP_Server.wsv" -Pattern '方法 应同步等待|方法 取同步等待毫秒|"sync_wait"\)|"async_only"\)|"max_ms"\)|"wait_for_load"'
# 3) 清理缓存 的直接调用（上一版漏看点）
Select-String -Path "$src\MCP_Server_Core.wsv" -Pattern 'browser\.清理缓存 \('
# 4) 后台浏览器 / 显示隐藏窗口 / 无头 / 远程调试 / GPU 全仓零命中核验
Select-String -Path "$src\*.wsv" -Pattern '后台浏览器|FBroHsCreateBackground|显示隐藏|ShowWindows|headless|remote_debug|调试端口|禁用GPU|DisableGpu'
# 5) 菜单写回通道缺失（回调只记录事件）
Select-String -Path "$src\MCP_BrowserEvents.wsv" -Pattern '方法 浏览器_即将打开菜单' -Context 0,10
# 6) CDP 全量透传（路径④）
Select-String -Path "$src\MCP_Server_Core.wsv" -Pattern '方法名 == "browser_cdp_call"' -Context 0,14
# 7) 类库方法名反向映射（通用方法：把 <方法名> 换成目标）
Select-String -Path "$src\*.wsv" -Pattern '清理缓存|Base64编码|URI编码|取数据URI|JS交互_删除|清空调用计数|设置触发鼠标触摸事件'
```

---

## 6. 本报告未做的事（边界声明）

- **未做真机验证**（`#6 触摸触发` 的 CDP 判定、后台浏览器可否在嵌入式容器内共存、菜单写回是否被 CEF 接受），全部标记为"待验证"，由主代理执行。
- **未修改 `src\` 任何文件**，未编译、未启动/结束任何进程、未调用 MCP HTTP 接口。
- 未复核上一版第 2 节"已覆盖（152 项）"与第 3 节"不适用（27 项）"——按本次的 6 条路径标准，那两节里**可能仍有同类误报**（例如"不适用"中若有 CDP/JS 可达项），但超出本轮范围。
- 行号受 `src\` 并发修改影响，以快照（§0.1）为准；引用请用代码锚点文本。
