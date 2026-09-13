# 类库缺口复核 r98 —— 菜单模式 / 命令行 / FBrowser辅助功能

> 只读静态复核。**未编译、未运行、未调用任何 MCP 工具、未发起任何 HTTP 请求、未改动任何已存在文件。**
> 本文所有"已覆盖"均指 **src 中存在对该类库方法的直接调用（或明确的语义等价工具）**，并给出 `文件:行号` 与原文片段。
> **不存在任何"实测/已验证/已测试"结论** —— 凡涉及运行期行为者一律标注为静态推断。

---

## 0. 证据快照与行号漂移警告（**必读**）

本次分析进行期间，**`src/MCP_Server_Core.wsv` 正被另一进程持续写入**。我观察到它的行数在同一会话内从 **7563 → 7583 → 7632** 连续增长（mtime 由 `05:59:42` 变为 `06:01:35`），因此**该文件的行号会随写入漂移**。

**我最终采用的快照（所有 `MCP_Server_Core.wsv` 行号均取自下列同一版本）：**

| 文件 | 行数 | SHA-256（前 16 位） | mtime | 是否稳定 |
|---|---:|---|---|---|
| `src/MCP_Server_Core.wsv` | **7632** | `A6A199AD1403BB67` | `06:01:35` | ❌ **分析期间被并发写入，行号会漂移** |
| `src/MCP_Server.wsv` | 11068 | `75DC8AF0B6505830` | `05:53:21` | ✅ 稳定（全会话未变） |
| `src/MCP_BrowserEvents.wsv` | 3159 | `24599CF1F642A5C1` | `01:42:36` | ✅ 稳定 |
| `src/main.wsv` | 809 | `FFBF32CB431C4AF3` | `04:59:44` | ✅ 稳定 |
| `src/MCP_Kernel.wsv` | 1800 | `F57B970E5F59BE20` | `04:37:08` | ✅ 稳定 |
| `src/MCP_ResponseBuilders.wsv` | 444 | `03B5917579B50DBB` | `01:30:58` | ✅ 稳定 |
| `src/MCP_Server_HTTP.wsv` | 369 | `CF78D64B4077E65F` | `01:31:19` | ✅ 稳定 |
| `src/MCP_Server_VIP.wsv` | 1755 | `75A5A670FC0C1560` | `05:44:12` | ✅ 稳定 |
| `src/MCP_Stdio.wsv` | 339 | `986471AD1AAFDB45` | `01:29:45` | ✅ 稳定 |
| `src/MCP_Server_System.wsv` | — | — | `05:02:15` | ✅ 稳定 |
| `src/MCP_Callbacks.wsv` | 1346 | — | `01:31:25` | ✅ 稳定 |

> **行号漂移的应对**：凡引用 `MCP_Server_Core.wsv` 之处，我都**同时给出"稳定的代码锚点原文"**（可直接 grep 定位，不受重编号影响），行号仅作参考。若你复核时行号对不上，请以锚点原文为准。
> 类库文件 `FBroLib.wsv`（5612 行，**不受本项目写入影响**）的行号是稳定的，可直接引用。

**方法论**：为避免"按中文方法名猜英文工具名"的误报，本次对每条候选做了**双向检索**：
（a）grep 类库中文方法名（含 `*.~vbak.wsv` 备份，故"零命中"是强证据）；
（b）grep 语义等价的英文工具名与描述关键词；
（c）对命中的调用点，**人工回溯到外层工具分支/方法头**，确认该调用真的位于工具可达路径上（而非同名噪声）；
（d）对"已覆盖"结论，另在 `MCP_Server.wsv` 的服务端**注册表**中确认工具确实被 `添加工具JSON` 注册（防止"实现存在但工具不存在"）。
`@输出名` 一律未作为存活/引用依据。

---

## 1. 基准与命名核对

| 项 | 值 |
|---|---|
| 项目根 ROOT | `C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp` |
| 类库基准 | `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroLib.wsv`（5612 行） |
| 项目内其它类库副本 | **无**（`Get-ChildItem -Recurse -Filter FBroLib*` 在 ROOT 下 0 命中）→ 基准唯一，不存在版本歧义 |
| 已注册工具总数 | **313**（`添加工具JSON ("` 在 `src/MCP_Server.wsv` + `src/MCP_Kernel.wsv` + `src/MCP_Server_Core.wsv` 计数 = 313，与任务描述一致） |

**类名核对结果（以类库文件中的真实类名为准）**：

| 任务给的类名 | 类库中真实类名 | 定义位置 | 是否有出入 |
|---|---|---|---|
| `类_FBrowser_菜单模式` | **`类_FBrowser_菜单模式`** | `FBroLib.wsv:3288` `类 类_FBrowser_菜单模式 <公开 注释 = "CefMenuModel" @输出名 = "FBroMenuModel">` | 无出入 |
| `类_FBrowser_命令行` | **`类_FBrowser_命令行`** | `FBroLib.wsv:1733` `类 类_FBrowser_命令行 <公开 @输出名 = "FBroCommandLine" @全局类 = 真 "">` | 无出入 |
| `FBrowser辅助功能` | **`FBrowser辅助功能`**（**无 `类_` 前缀**） | `FBroLib.wsv:377` `类 FBrowser辅助功能 <公开 @全局类 = 真>` | **有出入**：该类是全局静态功能类，名字**不带 `类_` 前缀**，与"类_"系列不同族 |

> 三个类**全部定义在同一个文件** `FBroLib.wsv`（`FBrowser辅助功能` 在 377-537；`类_FBrowser_命令行` 在 1733-1974；`类_FBrowser_菜单模式` 在 3288-3624）。
> 另注：`FBroVip.wsv` / `FBroEventControl.wsv` / `FBroDataType.wsv` / `FBroConst.wsv` / `FBroValue.wsv` / `FBroCallback.wsv` / `FBroHelp.wsv` 中**没有**这三个类。

---

## 2. 摘要

候选原始清单来自 `_audit/_classlib_gap.md:25-27`（辅助功能 18 条）、`:37-39`（命令行 15 条）、`:41-43`（菜单模式 13 条）。

| 类 | 候选数 | 已覆盖 | 真缺口 | 其中「仅启动期生效（运行期不可达）」 | 不确定 |
|---|---:|---:|---:|---:|---:|
| `类_FBrowser_菜单模式` | 13 | **0** | **13** | 0 | 0 |
| `类_FBrowser_命令行` | 15 | **1** | **14** | **14** | 0 |
| `FBrowser辅助功能` | 18 | **12** | **6** | 0 | 0 |
| **合计** | **46** | **13** | **33** | **14** | **0** |

**真缺口 33 条的去向**：

- **「运行期可做」真缺口 = 19 条** —— 13 条菜单模式 + 6 条辅助功能（`通过序号取浏览器` / `取数据URI` / `写入JSON` / `字节值解析为JSON` / `启用异常收集` / `异常收集回调模板函数`）。
  其中**真正有工具价值的只有 14 条**：13 条菜单模式 + `通过序号取浏览器`；另 5 条为**非用户能力或极低价值**（见 §4.1 B 组备注）。
- **「仅启动期生效（本项目运行期不可达）」真缺口 = 14 条** —— 全部属 `类_FBrowser_命令行`（仅 `设置全局代理` 例外，见 §3.2）。

**误报消除的主要战果（13 条已覆盖）**：任务背景中提示的 `Base64编解码` / `URI编解码` 已确认为**误报**——`browser_base64_encode` / `_decode` / `browser_uri_encode` / `browser_uri_decode` 四个工具**已注册且真的直调类库方法**；`清理缓存`→`browser_clear_cache` 亦确认为误报。本轮另新增消除 8 条：`通过ID取浏览器`、`通过用户标识取浏览器`、`通过窗口句柄取浏览器`、`取ID清单`、`取数量`、`取用户标识清单`、`解析JSON`、`设置全局代理`。

---

## 3. 逐条判定

### 3.1 `类_FBrowser_菜单模式`（13 条 —— **全部真缺口**）

**类名核对**：`FBroLib.wsv:3288`。该类是 `CefMenuModel` 封装，共 **36 个方法**（3288-3624）。

**本族共同证据（每一行都适用，不再重复）**

1. **类库侧**：13 个方法定义 + 底层 `FBroHsMenuModel_*` 见下表格"类库方法原文"列。
2. **src 侧逐方法 grep = 0 命中**：对 `添加菜单|添加分隔栏|添加子菜单|添加Check菜单|添加Radio菜单|选中状态|设置快捷键|移除快捷键|存在快捷键|清空菜单|取快捷键|置可见状态|置禁止状态` 在 `src/**/*.wsv`（含备份）全目录 grep → **`No matches found`**。对实例前缀 `菜单模式.` grep → **`No matches found`**。
3. **该类只作为事件形参类型出现**（从不调用方法）：
   - `src/MCP_BrowserEvents.wsv:2662`（稳定文件）：`参数 菜单模式 <类型 = 类_FBrowser_菜单模式 @输出名 = "MenuModel">`（在 `浏览器_即将打开菜单` 内，方法头 `:2658`）
   - `src/MCP_BrowserEvents.wsv:2674`：`参数 菜单模式 <类型 = 类_FBrowser_菜单模式 @输出名 = "MenuModel">`（在 `浏览器_菜单被调用` 内，方法头 `:2670`）
4. **现有同名混淆项 `browser_kernel_menu` 作用相反（屏蔽，非构建）**：
   - 注册：`src/MCP_Server.wsv:9797`（稳定文件）`添加工具JSON ("browser_kernel_menu", "内核层: 右键快捷菜单屏蔽。action=disable屏蔽页面右键菜单(内核事件拦截), enable恢复, status查状态(触发条件以实际内核为准)", 单参数Schema文本 ("action", "text", "disable/enable/status"))`
   - 实现：`src/MCP_Kernel.wsv:522` `屏蔽快捷菜单 = 真` / `:527` `屏蔽快捷菜单 = 假` / `:534` `st.加入逻辑值成员 ("disabled", 屏蔽快捷菜单)`
   - 消费：`src/MCP_BrowserEvents.wsv:2567` `如果 (MCP_内核分派.屏蔽快捷菜单)`
   - → 只有 `disable/enable/status` 三态，**没有任何"改菜单项/加菜单项"的能力**，与本事正交，不构成覆盖。
5. **`browser_context_menu` / `browser_menu_build` 类工具不存在**：对 `menu_build|menu_item` 的 `添加工具JSON` 注册 grep → 0 命中（`context_menu` 仅出现在事件名 `context_menu_opening` 等与 `browser_collect` 描述里）。
6. **事件回调体确实没碰菜单**：
   - `src/MCP_BrowserEvents.wsv:2666`：`记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), "")` —— 形参 `菜单模式` 在手却完全未使用。
   - 同族 `浏览器_菜单被调用`（`:2670-2683`）、`浏览器_菜单被点击`（`:2685-2702`）、`浏览器_菜单被关闭`（`:2704-2712`）同样只 `记录监控事件`。
   - 事件开关定义：`src/MCP_Server.wsv:393` `变量 是否监控菜单事件 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_即将打开菜单/菜单被调用/菜单被点击/菜单被关闭 → browser_event:context_menu*" @输出名 = "IsMonitorContextMenu">`

| 类 | 类库方法原文 | 判定 | 依据（file:line + 原文） | 备注 |
|---|---|---|---|---|
| `类_FBrowser_菜单模式` | `方法 添加菜单 <公开 类型 = 逻辑型 注释 = "英文名：AddItem" @禁止流程检查 = 真>` / `参数 命令ID <类型 = 整数>` / `参数 标签名 <类型 = 文本型>` / `@ if(!IsEmpty()) return FBroHsMenuModel_AddItem(m_class,@<命令ID>,@<标签名>.GetText());`（`FBroLib.wsv:3331-3337`） | **真缺口** | src 零命中：`添加菜单` 全目录 `No matches found`；形参在手不用：`src/MCP_BrowserEvents.wsv:2662` `参数 菜单模式 <类型 = 类_FBrowser_菜单模式 @输出名 = "MenuModel">` + `:2664-2667` 仅 `记录监控事件 (真, "context_menu_opening", ...)` | 运行期可做；菜单构建族核心项 |
| `类_FBrowser_菜单模式` | `方法 添加子菜单 <公开 类型 = 类_FBrowser_菜单模式 注释 = "英文名：AddSubMenu" ...>`（`FBroLib.wsv:3356-3362`） | **真缺口** | 同上（`添加子菜单` `No matches found`；`MCP_BrowserEvents.wsv:2662/2674`） | 运行期可做；返回子菜单对象，可递归建树 |
| `类_FBrowser_菜单模式` | `方法 添加分隔栏 <公开 类型 = 逻辑型 注释 = "英文名：AddSeparator" ...>` → `FBroHsMenuModel_AddSeparator(m_class)`（`FBroLib.wsv:3325-3329`） | **真缺口** | 同上（`添加分隔栏` `No matches found`） | 运行期可做 |
| `类_FBrowser_菜单模式` | `方法 添加Check菜单 <公开 类型 = 逻辑型 注释 = "英文名：AddCheckItem" ...>`（`FBroLib.wsv:3339-3345`） | **真缺口** | 同上（`添加Check菜单` `No matches found`） | 运行期可做 |
| `类_FBrowser_菜单模式` | `方法 添加Radio菜单 <公开 类型 = 逻辑型 注释 = "英文名：AddRadioItem" ...>` / `参数 群ID <类型 = 整数>`（`FBroLib.wsv:3347-3354`） | **真缺口** | 同上（`添加Radio菜单` `No matches found`） | 运行期可做 |
| `类_FBrowser_菜单模式` | `方法 选中状态 <公开 类型 = 逻辑型 注释 = "英文名：SetCheck" ...>` → `FBroHsMenuModel_SetCheck(m_class,@<命令ID>,@<选中>)`（`FBroLib.wsv:3437-3442`） | **真缺口** | 同上（`选中状态` `No matches found`） | 运行期可做；需先有自定义菜单项才有意义 |
| `类_FBrowser_菜单模式` | `方法 选中状态_索引 <公开 类型 = 逻辑型 注释 = "英文名：SetCheckedAt" ...>` → `FBroHsMenuModel_SetCheckedAt`（`FBroLib.wsv:3444-3449`） | **真缺口** | 同上（`选中状态` `No matches found`，`选中状态_索引` 为同族） | 运行期可做 |
| `类_FBrowser_菜单模式` | `方法 设置快捷键 <公开 类型 = 逻辑型 注释 = "只是用于显示快捷键，触发需自行用键盘事件实现" ...>` / `参数 命令ID/键代码/是否按下shift/是否按下ctrl/是否按下alt`（`FBroLib.wsv:3464-3472`） | **真缺口** | 同上（`设置快捷键` `No matches found`） | 运行期可做；**类库注释明写"只是用于显示快捷键，触发需自行用键盘事件实现"** → 它不产生行为 |
| `类_FBrowser_菜单模式` | `方法 设置快捷键_索引 <公开 类型 = 逻辑型 注释 = "只是用于显示快捷键，触发需自行用键盘事件实现" ...>` → `FBroHsMenuModel_SetAcceleratorAt`（`FBroLib.wsv:3474-3482`） | **真缺口** | 同上 | 运行期可做；同"仅显示不触发"限制 |
| `类_FBrowser_菜单模式` | `方法 移除快捷键 <公开 类型 = 逻辑型 注释 = "英文名：" ...>` → `FBroHsMenuModel_RemoveAccelerator(m_class,@<命令ID>)`（`FBroLib.wsv:3484-3488`） | **真缺口** | 同上（`移除快捷键` `No matches found`） | 运行期可做 |
| `类_FBrowser_菜单模式` | `方法 移除快捷键_索引 <公开 类型 = 逻辑型 ...>` → `FBroHsMenuModel_RemoveAcceleratorAt`（`FBroLib.wsv:3490-3494`） | **真缺口** | 同上 | 运行期可做 |
| `类_FBrowser_菜单模式` | `方法 存在快捷键 <公开 类型 = 逻辑型 注释 = "英文名：" ...>` → `FBroHsMenuModel_HasAccelerator(m_class,@<命令ID>)`（`FBroLib.wsv:3451-3455`） | **真缺口** | 同上（`存在快捷键` `No matches found`） | 运行期可做，但**只有在本项目先具备"菜单写回通道"后才有对象可查**，属从属项 |
| `类_FBrowser_菜单模式` | `方法 存在快捷键_索引 <公开 类型 = 逻辑型 注释 = "英文名：HasAcceleratorAt" ...>` → `FBroHsMenuModel_HasAcceleratorAt`（`FBroLib.wsv:3457-3462`） | **真缺口** | 同上 | 同上，从属项 |

> **候选清单不全的额外发现（供参考，不计入 46 条统计）**：`类_FBrowser_菜单模式` 共 36 个方法，13 条候选之外还有 **23 个方法在 src 中同样 0 命中**，包含裸文本过滤时漏掉的高价值项：`清空菜单`（`FBroLib.wsv:3313`，Clear）、`取数量`（`:3319`）、`删除菜单`（`:3364`）、`置菜单标签`（`:3378`）、`取菜单类型`（`:3386`）、`取分组ID`（`:3392`）、`取子菜单`（`:3398`）、`是否可见`/`置可见状态`（`:3405`/`:3411`）、`是否禁止`/`置禁止状态`（`:3418`/`:3424`）、`是否选中`（`:3431`）、`取快捷键`/`取快捷键_索引`（`:3496`/`:3517`）、`置颜色`/`置颜色_索引`/`取颜色`/`取颜色_索引`（`:3538`/`:3550`/`:3563`/`:3586`）、`置字体`/`置字体_索引`（`:3609`/`:3616`，类库注释自标"待验证"）、以及基础设施 `是否为空`/`置空`。
> 证据：`菜单模式.` 全目录 grep = `No matches found`，即**该类在 src 中从未被调用过任何实例方法**。因此"缺口"实际是 34 条（36 − `是否为空`/`置空` 两个空指针工具），远超候选的 13 条。

### 3.2 `类_FBrowser_命令行`（15 条 —— 已覆盖 1 / 真缺口 14，其中 14 条仅启动期生效）

**类名核对**：`FBroLib.wsv:1733`。

**本族共同证据（每一行都适用，不再重复）**

1. **src 侧逐方法 grep = 0 命中（含 `*.~vbak.wsv` 备份）**：对 `插入值|FBrowser_命令行_创建|FBrowser_命令行_取全局|启用单进程模式|启用录音|启用摄像头|启用无头模式|启用自动播放|启用跨框架操作模式|忽略GPU禁用清单|禁用GPU|禁用GPU缓存|禁用代理|设置远程调试端口` 在 `src/**/*.wsv` 全目录 grep → **`No matches found`**。
   → 这是本族最强的证据：**`类_FBrowser_命令行` 的全部方法在 src 中一个都没有被调用过。**
2. **该类只作为事件形参类型出现**：
   - `src/main.wsv:477`（稳定文件）：`参数 命令行 <类型 = 类_FBrowser_命令行 @输出名 = "CommandLine">`（在 `即将处理命令行` 内，方法头 `:475`）
   - `src/main.wsv:490`：`参数 命令行 <类型 = 类_FBrowser_命令行 @输出名 = "CommandLine">`（在 `浏览器_即将启动子进程` 内，方法头 `:489`）
3. **两个钩子的方法体确实是空的（只记录监控事件，从不调用形参任何方法）**：
   - `src/main.wsv:479-486`：`如果 (MCP命令服务器.是否监控启动流程 == 假) { 返回 }` / `变量 事件数据 <类型 = YYJSON对象类>` / `事件数据.加入文本成员 ("process_type", 到文本 (进程类型))` / `记录应用监控事件 ("app_startup_cmdline", 事件数据.到可读文本 (YYJSON格式化选项.压缩))`（`:486` 已逐字核对）
   - `src/main.wsv:492-496`：`如果 (MCP命令服务器.是否监控启动流程 == 假) { 返回 }` / `记录应用监控事件 ("app_startup_child_process", "")`
4. **`FBrowser_初始化` 的调用位置即"时间窗关闭点"**：`src/main.wsv:98` `如果真 (FBrowser_初始化 (设置, 初始化事件) == 假)`；其上方 `:96-97` 构造 `类_MCP_初始化事件` 智能指针（即承载上述两个 override 的类）。命令行开关只在 CEF 初始化前有意义 → 本项目**没有任何运行期入口**能改这些开关。
5. **`--headless` 在项目中存在但语义完全无关（反例排除）**：
   - `src/MCP_Stdio.wsv:225`：`如果 (arg == "--mcp-stdio" || arg == "--stdio" || arg == "--headless")` —— 判定的是 **MCP 服务器自身**是否走无控制台 stdio 传输；
   - `src/MCP_Server.wsv:420`：`# 背景: --mcp-stdio/--stdio/--headless 场景下部分用户不希望额外监听端口(隔离/审计要求),`
   - ⇒ **与浏览器无头模式无关**，不能算作 `启用无头模式` 的覆盖。
6. **`远程调试` / `debugging_port` / `webSocketDebuggerUrl` 全目录 0 命中**：对 `远程调试|remote_debug|debugging_port|webSocketDebuggerUrl|ws_url|devtools_url|devtoolsFrontendUrl` grep → `No matches found`。
   - 项目自建的 `/json/version` 与 `/json/list`（`src/MCP_Server_HTTP.wsv:203-222`，`src/MCP_ResponseBuilders.wsv:319-320`、`:330-338`、`:340-382`）**不构成覆盖**：`构建JSON版本响应` 只输出 `Browser/Protocol-Version/MCP-Version` 三字段（`MCP_ResponseBuilders.wsv:334` `版本JSON.加入文本成员 ("Browser", "FBrowser CEF")` 起），`构建JSON列表响应` 每项只输出 `id` 与 `url`（`:366` `项.加入整数成员 ("id", bid)`、`:371` `项.加入文本成员 ("url", urlFrame.取地址 ())`）—— **没有 `webSocketDebuggerUrl`**，外部 Playwright/Puppeteer 无法据此 attach 到 CEF。

| 类 | 类库方法原文 | 判定 | 依据（file:line + 原文） | 备注 |
|---|---|---|---|---|
| `类_FBrowser_命令行` | `方法 FBrowser_命令行_创建 <公开 静态 类型 = 类_FBrowser_命令行 @禁止流程检查 = 真>` → `@ return @dt<类_FBrowser_命令行>(FBroHsCommandLine_CreateCommandLine());`（`FBroLib.wsv:1747-1751`） | **真缺口**（仅启动期生效） | 零命中：`FBrowser_命令行_创建` 全目录 `No matches found`；唯一出现处是形参：`src/main.wsv:477` | **基础设施**：自建命令行对象只为测试/预演，不改 CEF 生效开关 |
| `类_FBrowser_命令行` | `方法 FBrowser_命令行_取全局 <公开 静态 类型 = 类_FBrowser_命令行 @禁止流程检查 = 真>` → `@ return @dt<类_FBrowser_命令行>(FBroHsCommandLine_GetGlobalCommandLine());`（`FBroLib.wsv:1753-1756`） | **真缺口**（仅启动期生效） | 零命中：`FBrowser_命令行_取全局` `No matches found` | **基础设施**：任何启动参数工具的前置入口；本项目一律未接线 |
| `类_FBrowser_命令行` | `方法 启用单进程模式 <公开 注释 = "命令行--single-process，只为了方便多进程模拟调试，仅调试模式下有用，单进程模式存在各种问题，不建议发布软件使用">` → `FBroHsCommandLine_EnableSingleProcess (m_class);`（`FBroLib.wsv:1874-1879`） | **真缺口**（仅启动期生效） | 零命中：`启用单进程模式` `No matches found`；初始化窗口：`src/main.wsv:98` | 类库自述"仅调试、不建议发布" → **价值低** |
| `类_FBrowser_命令行` | `方法 启用录音 <公开 注释 = "命令行：enable-speech-input,允许浏览使用话筒">` → `FBroHsCommandLine_EnableSpeechInput`（`FBroLib.wsv:1895-1900`） | **真缺口**（仅启动期生效） | 零命中：`启用录音` `No matches found` | 无人值守场景需求弱 |
| `类_FBrowser_命令行` | `方法 启用摄像头 <公开 注释 = "命令行enable-media-stream,允许浏览使用摄像头">` → `FBroHsCommandLine_EnableMediaStream`（`FBroLib.wsv:1881-1886`） | **真缺口**（仅启动期生效） | 零命中：`启用摄像头` `No matches found`。**权限侧已被覆盖但不等价**：`src/MCP_Server_Core.wsv:3299`（锚点 `否则 (方法名 == "browser_permission_spoof")`）、`src/MCP_Server.wsv:9936` 注册（"permissions支持:geolocation/notifications/camera/microphone/…"）—— 那是**页面 `navigator.permissions` 的 JS 层伪装**，不是 CEF 的 `enable-media-stream` 开关 | 权限侧有部分替代，**开关本身仍缺** |
| `类_FBrowser_命令行` | `方法 启用无头模式 <公开 注释 = "命令行：--headless，无头模式">` → **方法体实为** `FBroHsCommandLine_EnableAutoplayPoliey (m_class);`（`FBroLib.wsv:1909-1914`） | **真缺口**（仅启动期生效） | 零命中：`启用无头模式` `No matches found`；`--headless` 仅 `src/MCP_Stdio.wsv:225`（服务端 stdio 判定，`src/MCP_Server.wsv:420` 同）；`src/main.wsv:215` 注释 `// 与"先创建再隐藏窗口"不同、也不是无头模式(其优于无头模式), 适合纯后台刷新取数, 占用更低。` | ⚠ **类库实现有复制粘贴缺陷**：`:1909` 注释写 `--headless`，`:1912` 实际调 `FBroHsCommandLine_EnableAutoplayPoliey`（自动播放），**根本没设 `--headless`** → 即使接线也不能直接用；正确绕法是 `置值("headless")`（`FBroLib.wsv:1828` `AppendSwitch`，src 0 调用）。**需求已由 `browser_create {background:true}` 覆盖**（`src/MCP_Server.wsv:9661`），故不建议单独实现 |
| `类_FBrowser_命令行` | `方法 启用自动播放 <公开 注释 = "命令行：autoplay-poliey，支持绝对部分视频网站自动播放视频，各别有限制的除外">` → `FBroHsCommandLine_EnableAutoplayPoliey`（`FBroLib.wsv:1902-1907`） | **真缺口**（仅启动期生效） | 零命中：`启用自动播放` `No matches found` | 媒体自动化前置项；中等价值 |
| `类_FBrowser_命令行` | `方法 启用跨框架操作模式 <公开 注释 = "跨框架操作，解除框架和框架直接不能直接操作的限制，存在不安全性">` → `FBroHsCommandLine_EnableCrossFrame`（`FBroLib.wsv:1888-1893`） | **真缺口**（仅启动期生效） | 零命中：`启用跨框架操作模式` `No matches found` | 项目已有大量跨 frame 工具（`browser_frame_*`），此项为内核层加固，非必需 |
| `类_FBrowser_命令行` | `方法 忽略GPU禁用清单 <公开 注释 = "内核内置不兼容部分显卡，设置后忽略内核这个设置，能有效解决部分显卡不兼容的问题…">` → `FBroHsCommandLine_DisableGpuBlockList`（`FBroLib.wsv:1938-1943`） | **真缺口**（仅启动期生效） | 零命中：`忽略GPU禁用清单` `No matches found` | 兼容性排障项 |
| `类_FBrowser_命令行` | `方法 插入值 <公开 注释 = "英语名：PrependWrapper 说明：在当前命令之间插入值 Insert a command before the current command. Common for debuggers, like \"valgrind\" or \"gdb --args\".">` / `参数 值 <类型 = 文本型>` → **方法体实为** `FBroHsCommandLine_AppendArgument(m_class,@<值>.GetText());`（`FBroLib.wsv:1865-1872`） | **真缺口**（仅启动期生效） | 零命中：`插入值` `No matches found`（该词在 src 中亦无任何其它含义命中） | ⚠ **类库实现与注释不符**：注释称 `PrependWrapper`（前置包装器，调试器场景），`:1870` 实际调 `AppendArgument`（追加参数）→ 语义等同 `置额外参数`，**不是前置** |
| `类_FBrowser_命令行` | `方法 禁用GPU <公开 注释 = "禁用后，网页渲染将由CPU处理，会提高CPU占用，不兼容的显卡只能禁用GPU否者网页可能渲染失败">` → `FBroHsCommandLine_DisableGpu`（`FBroLib.wsv:1924-1929`） | **真缺口**（仅启动期生效） | 零命中：`禁用GPU` `No matches found` | 虚拟机/无 GPU 环境稳定性 |
| `类_FBrowser_命令行` | `方法 禁用GPU缓存 <公开 注释 = "禁止GPU创建缓存文件及文件夹">` → `FBroHsCommandLine_DisableGpuCache`（`FBroLib.wsv:1931-1936`） | **真缺口**（仅启动期生效） | 零命中：`禁用GPU缓存` `No matches found` | 同上族 |
| `类_FBrowser_命令行` | `方法 禁用代理 <公开 注释 = "命令行：--no-proxy-server，禁止使用代理和系统的自动检测代理功能">` → `FBroHsCommandLine_DisableProxy`（`FBroLib.wsv:1968-1973`） | **真缺口**（仅启动期生效） | 零命中：`禁用代理` `No matches found`。**运行期等价物不等价**：`browser_clear_proxy`（`src/MCP_Server.wsv:9690` 注册 / `src/MCP_Server_Core.wsv:1414` 分支，锚点 `否则 (方法名 == "browser_clear_proxy")`）只清"类库设置过的代理"，**不能禁止系统自动检测代理**（`--no-proxy-server` 的语义） | 运行期无替代 |
| `类_FBrowser_命令行` | `方法 设置全局代理 <公开 注释 = "设置全局代理，只能设置一个，如果需要认证则需要设置账号密码；不支持带账号密码的S5代理…">` / `参数 代理地址/代理账号/代理密码` → `FBroHsCommandLine_SetProxy (m_class,…)`（`FBroLib.wsv:1945-1953`） | **已覆盖**（能力等价，非同类库方法） | 覆盖工具 **`browser_set_proxy`**：注册 `src/MCP_Server.wsv:9689`（稳定文件）`添加工具JSON ("browser_set_proxy", "设置浏览器代理并持久生效(新浏览器自动应用)| address 形如 ip:port; 设置后需刷新页面才作用于当前页", …)`；实现 `src/MCP_Server_Core.wsv:1373`（锚点 `否则 (方法名 == "browser_set_proxy")`）/ `:1401` `browser.设置代理 (address, username, password)` / `:1394-1395` `MCP命令服务器.持久代理地址 = address` + `持久代理账号 = username`；新浏览器自动套用 `src/MCP_Server.wsv:2027` `应用代理 = 持久代理地址` / `:2042` `浏览器.设置代理 (应用代理, 应用账号, 应用密码)`。VIP S5 版：`src/MCP_Server_VIP.wsv:44` `否则 (方法名 == "browser_set_s5_proxy")` / `:60` `vip_ctrl.高级_设置代理 (...)` | ⚠ **依据类型必须说清**：调的是 **`类_FBrowser_浏览器::设置代理`**，**不是** `类_FBrowser_命令行::设置全局代理`。用户能力（设代理、带账号密码、持久化到新浏览器）已具备；类库该方法本身未被调用，且其"启动期全局"语义与运行期逐浏览器设置并不完全等同（不影响判定为已覆盖） |
| `类_FBrowser_命令行` | `方法 设置远程调试端口 <公开 注释 = "命令行：--remote-debugging-port">` / `参数 端口号 <类型 = 整数>` → `FBroHsCommandLine_SetRemoteDebuggingPort (m_class, @<端口号>);`（`FBroLib.wsv:1916-1922`） | **真缺口**（仅启动期生效） | 零命中：`设置远程调试端口`/`远程调试`/`remote_debug`/`debugging_port`/`webSocketDebuggerUrl` 全目录 `No matches found`；形参在手不用 `src/main.wsv:477` + `:479-486`；初始化窗口 `src/main.wsv:98`；自建 `/json/list` 无 `webSocketDebuggerUrl`（`src/MCP_ResponseBuilders.wsv:366/371`，`src/MCP_Server_HTTP.wsv:214` `如果 (URL路径 == "/json" || URL路径 == "/json/list")`） | 本族**最高价值**项：唯一增量是**外部 Playwright/Puppeteer/CDP 客户端 attach 本进程**。项目内部已有 `browser_cdp_call` 全量 CDP 通道，故对本项目 AI 自身无增量 |

### 3.3 `FBrowser辅助功能`（18 条 —— 已覆盖 12 / 真缺口 6）

**类名核对**：`FBroLib.wsv:377` `类 FBrowser辅助功能 <公开 @全局类 = 真>`（**无 `类_` 前缀**）。全部方法为 `<公开 静态>`。

> 下表 `src/MCP_Server_Core.wsv` 的每个行号后均附**代码锚点原文**（括号内），请以锚点为准（见 §0 漂移警告）。

| 类 | 类库方法原文 | 判定 | 依据（file:line + 原文） | 备注 |
|---|---|---|---|---|
| `FBrowser辅助功能` | `方法 FBrowser_Parser_Base64编码 <公开 静态 类型 = 文本型 @禁止流程检查 = 真>` / `参数 数据 <类型 = 文本型>` → `FBroHsBase64Encode(@<数据>.GetText())`（`FBroLib.wsv:379-385`） | **已覆盖** | 工具 **`browser_base64_encode`**：注册 `src/MCP_Server.wsv:9753` `添加工具JSON ("browser_base64_encode", "Base64编码", 单参数Schema文本 ("data", "text", "数据"))`；分派 `src/MCP_Server_Core.wsv:5285`（锚点 `否则 (方法名 == "browser_base64_encode")`）+ `:5294`（锚点 `result = FBrowser_Parser_Base64编码 (data)`） | ✅ **确认误报**（任务背景中的猜测成立） |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_Base64解码 <公开 静态 类型 = 类_FBrowser_字节集 ...>` / `参数 数据 <类型 = 文本型>` → `FBroHsBase64Decode(@<数据>.GetText())`（`FBroLib.wsv:387-392`） | **已覆盖** | 工具 **`browser_base64_decode`**：注册 `src/MCP_Server.wsv:9754` `添加工具JSON ("browser_base64_decode", "Base64解码", 单参数Schema文本 ("data", "text", "数据"))`；分派 `src/MCP_Server_Core.wsv:5297`（锚点 `否则 (方法名 == "browser_base64_decode")`）+ `:5306`（锚点 `字节结果 = FBrowser_Parser_Base64解码 (data)`）+ `:5310`（锚点 `解码后文本 = 字节结果.取文本 ()`） | ✅ **确认误报**。另有内部用法：`src/MCP_Server.wsv:7784` `base64字节 = FBrowser_Parser_Base64解码 (code)`（`code_base64` 传参通道） |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_URI编码 <公开 静态 类型 = 文本型 注释 = "…The result is basically the same as encodeURIComponent in Javacript." @禁止流程检查 = 真>` / `参数 数据/use_plus` → `FBroHsURIEncode(@<数据>.GetText(),@<use_plus>)`（`FBroLib.wsv:404-416`） | **已覆盖** | 工具 **`browser_uri_encode`**：注册 `src/MCP_Server.wsv:9755` `添加工具JSON ("browser_uri_encode", "URI编码", 单参数Schema文本 ("data", "text", "数据"))`；分派 `src/MCP_Server_Core.wsv:5316`（锚点 `否则 (方法名 == "browser_uri_encode")`）+ `:5325`（锚点 `result = FBrowser_Parser_URI编码 (data, 假)`） | ✅ **确认误报**，且参数已接（`use_plus=假`） |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_URI解码 <公开 静态 类型 = 文本型 注释 = "Unescapes \|text\| and returns the result."…>` / `参数 数据/convert_to_utf8/unescape_rule` → `FBroHsURIDecode(@<数据>.GetText(),@<convert_to_utf8>,@<unescape_rule>)`（`FBroLib.wsv:418-431`） | **已覆盖** | 工具 **`browser_uri_decode`**：注册 `src/MCP_Server.wsv:9756` `添加工具JSON ("browser_uri_decode", "URI解码", 单参数Schema文本 ("data", "text", "数据"))`；分派 `src/MCP_Server_Core.wsv:5328`（锚点 `否则 (方法名 == "browser_uri_decode")`）+ `:5337`（锚点 `result = FBrowser_Parser_URI解码 (data, 真, 真)`） | ✅ **确认误报**。另有 3 处内部用法：`src/MCP_Server.wsv:8098` `decodedScheme = FBrowser_Parser_URI解码 (rawScheme, 真, 真)`，以及同文件 `:10935`、`:11041`（自定义 scheme 路径解码） |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_解析JSON <公开 静态 类型 = 类_FBrowser_值 注释 = "Parses the specified \|json_string\| and returns a dictionary or list representation."…>` / `参数 json_string/options` → `FBroHsParseJSON(@<json_string>.GetText(),@<options>)`（`FBroLib.wsv:433-441`） | **已覆盖**（内部基础设施，无独立工具面） | 直调：`src/MCP_Server.wsv:1628`（稳定文件）`params_value = FBrowser_Parser_解析JSON (paramsJSON文本, JSON解析.RFC)`，位于 CDP 命令分派路径内（紧邻其上的 CDP 观察者就绪检查）；备份同处 `src/MCP_Server_1.~vbak.wsv:1519` | ⚠ 依据类型：**被 CDP 工具链内部调用**，不存在独立工具。MCP 本身即 JSON 协议，无必要单独暴露 → 判已覆盖而非缺口 |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_写入JSON <公开 静态 类型 = 文本型 @禁止流程检查 = 真>` / `参数 node <类型 = 类_FBrowser_值>` / `参数 options <类型 = 整数>` → `FBroHsWriteJSON(@<node>.m_class,@<options>)`（`FBroLib.wsv:450-457`） | **真缺口**（运行期可做） | 零命中：`写入JSON|json_stringify|json_write|browser_json` 全目录 `No matches found`（`src` 内 JSON 序列化统一走 `YYJSON对象类`，如 `src/MCP_ResponseBuilders.wsv:297-301` `变量 对象 <类型 = YYJSON对象类>` / `对象.创建自文本 ("{}")` / `对象.加入逻辑值成员 ("success", 真)`） | **价值低**：宿主侧对象序列化，AI 侧自带 JSON 能力；类库 `类_FBrowser_值` 在 src 中亦无构造入口 |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_取数据URI <公开 静态 类型 = 文本型 @禁止流程检查 = 真>` / `参数 mimetype <类型 = 文本型>` / `参数 数据 <类型 = 文本型>` → `FBroHsGetDataURI(@<mimetype>.GetText(),@<数据>.GetText())`（`FBroLib.wsv:394-402`） | **真缺口**（运行期可做） | 零命中：`取数据URI|data_uri|dataURI` 全目录 `No matches found` | **价值低**：`browser_screenshot` 已返回 data URI（`src/MCP_ResponseBuilders.wsv:439` `包装对象.加入文本成员 ("message", "data:" + mime类型 + ";base64," + base64数据)`），但那是**图片字节**路径；本方法两个参数都是 `文本型`，**不能用于任意字节集/文件** |
| `FBrowser辅助功能` | `方法 FBrowser_Parser_字节值解析为JSON <公开 静态 类型 = 类_FBrowser_值 注释 = "FBroHsParseJSON_BinaryValue" ...>` / `参数 字节值 <类型 = 类_FBrowser_字节集>` / `参数 options <类型 = 整数>` → `FBroHsParseJSON_BinaryValue(@<字节值>.m_class,@<options>)`（`FBroLib.wsv:443-448`） | **真缺口**（运行期可做） | 零命中：`字节值解析为JSON` 全目录 `No matches found` | **价值低**：可从 `browser_base64_decode` 得到 `类_FBrowser_字节集`（`src/MCP_Server_Core.wsv:5306`，锚点 `字节结果 = FBrowser_Parser_Base64解码 (data)`），但 MCP 侧直接传文本更简单 |
| `FBrowser辅助功能` | `方法 FBrowser_启用异常收集 <公开 静态 注释 = "火山版本内置已经设置了，所有这个没用" @嵌入式方法 = "">` / `参数 异常信息文件名/异常执行回调` → `FBroHsDumpStart(@<异常信息文件名>.GetText(),(HANDLE)@<异常执行回调>);`（`FBroLib.wsv:531-536`） | **真缺口**（运行期可做，但**不建议实现**） | 零命中：`异常收集|DumpStart|_EXCEPTION` 全目录 `No matches found`（`崩溃` 的 137 处命中全部是**渲染进程终止事件**路径：`src/MCP_BrowserEvents.wsv:919` `# 渲染进程崩溃 — 通知客户端`、`:961` `状态语义 = "崩溃"`、`:965` `// CEF cef_termination_status_t: 0=异常终止…`，属 CEF 渲染进程终止通知，**不是宿主进程 SEH 崩溃转储**） | ⚠ **类库原文自述该功能无用**（`FBroLib.wsv:531` 注释："火山版本内置已经设置了，所有这个没用"）→ **不建议做工具**。项目另有独立崩溃处理链（`src/main.wsv:54` `// 崩溃恢复:` / `src/MCP_Server.wsv:8182` `方法 原子递增崩溃计数`） |
| `FBrowser辅助功能` | `方法 异常收集回调模板函数 <静态 类型 = 整数 @禁止流程检查 = 真>` / `参数 异常记录文件/异常数据 <类型 = 变整数 注释 = "_EXCEPTION_POINTERS* 类型指针数据">` → `@ return EXCEPTION_EXECUTE_HANDLER;`（`FBroLib.wsv:523-529`） | **真缺口**（非用户能力） | 零命中：`异常收集回调` 全目录 `No matches found`；类库标注 `<静态>` **无 `<公开>`**（`FBroLib.wsv:523`） | ⚠ 它是 `启用异常收集` 的 `@匹配方法` 模板（`FBroLib.wsv:533` `参数 异常执行回调 <@匹配方法 = "异常收集回调模板函数">`），**不是独立用户 API**；主语未接线，从属项随之不存在 |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_取ID清单 <公开 静态 类型 = 类_FBrowser_列表值 注释 = "返回全部浏览器ID清单…">` → `FBroHsBrowserListControl_GetBrowserIDList()`（`FBroLib.wsv:513-516`） | **已覆盖** | 工具 **`browser_list`**：注册 `src/MCP_Server.wsv:9664`（稳定文件）`添加工具JSON ("browser_list", "列出所有浏览器实例(返回各自的 id/url)。**多浏览器用法**…")`；分派 `src/MCP_Server_Core.wsv:638`（锚点 `否则 (方法名 == "browser_list")`）+ `:642` `ID清单 = FBrowser_浏览器_取ID清单 ()`。另有内部用法 `src/MCP_ResponseBuilders.wsv:344` `ID清单 = FBrowser_浏览器_取ID清单 ()`（`/json/list` 端点）、`src/MCP_Server.wsv:7934`、`:8249`（残留清理） | ✅ 覆盖确凿 |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_取数量 <公开 静态 类型 = 整数 @禁止流程检查 = 真>` → `FBroHsBrowserListControl_GetBrowserCount()`（`FBroLib.wsv:508-511`） | **已覆盖** | 工具 **`browser_meta`**：注册 `src/MCP_Server.wsv:9688` `添加工具JSON ("browser_meta", "元数据(机器码/授权/版本)")`；分派 `src/MCP_Server_Core.wsv:3762`（锚点 `否则 (方法名 == "browser_meta")`）+ `:3772` `元数据对象.加入整数成员 ("browser_count", FBrowser_浏览器_取数量 ())`。另有工具内用法：`src/MCP_Server_Core.wsv:543` `如果 (FBrowser_浏览器_取数量 () >= MCP_常量.浏览器实例最大数量)`（`browser_create` 上限守卫）；服务端点与指标 `src/MCP_ResponseBuilders.wsv:312` `信息JSON.加入整数成员 ("browsers", FBrowser_浏览器_取数量 ())`、`src/MCP_Server_HTTP.wsv:140`、`src/MCP_Server_System.wsv:116`（`ping`）、`src/MCP_Server.wsv:9027` `文本 = 文本 + "mcp_browsers " + 到文本 (FBrowser_浏览器_取数量 ()) + "\n"`（Prometheus 指标） | ✅ 覆盖确凿（`browser_list` 亦可推导） |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_取用户标识清单 <公开 静态 类型 = 类_FBrowser_列表值 注释 = "返回全部浏览器标识清单…返回值为一个保存文本的清单列表值">` → `FBroHsBrowserListControl_GetBrowserFlagList()`（`FBroLib.wsv:518-521`） | **已覆盖** | 工具 **`browser_user_tags`**：注册 `src/MCP_Server.wsv:9763` `添加工具JSON ("browser_user_tags", "列出用户标识")`；分派 `src/MCP_Server_Core.wsv:6067`（锚点 `否则 (方法名 == "browser_user_tags")`）+ `:6070`（锚点 `tag清单 = FBrowser_浏览器_取用户标识清单 ()`），失败分支文案 `返回 (MCP_响应构建.命令失败 (命令ID, "无法获取用户标识清单"))` | ✅ 覆盖确凿。工具描述已诚实标注只读：`browser_find_by_tag` 分支内失败文案 `"browser_user_tags 是**只读**的标识清单(旧文案说它「设置」标识, 与事实不符, 已更正)"` |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_通过ID取浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 注释 = "通过浏览器ID取出浏览器类，ID由浏览器类取ID获得…">` / `参数 浏览器ID <类型 = 整数>` → `FBroHsBrowserListControl_GetBrowserFromID(@<浏览器ID>)`（`FBroLib.wsv:481-485`） | **已覆盖** | 工具 **`browser_close`**：注册 `src/MCP_Server.wsv:9662` `添加工具JSON ("browser_close", "关闭指定浏览器(默认关闭主浏览器)", 单参数Schema文本 ("browser_id", "integer", "浏览器ID(省略则关闭主浏览器)", 假))`；分派 `src/MCP_Server_Core.wsv:616`（锚点 `否则 (方法名 == "browser_close")`）+ `:623` `closeBrowser = FBrowser_浏览器_通过ID取浏览器 (closeID)`。工具 **`browser_list`**：`src/MCP_Server_Core.wsv:656` `b = FBrowser_浏览器_通过ID取浏览器 (bid)`。另有 `src/MCP_Server.wsv:7874` `返回 (FBrowser_浏览器_通过ID取浏览器 (browserID))`（`browser_id` 解析兜底）、`:7940`、`:8255`、`src/MCP_Callbacks.wsv:136` 与 `:198`（`bb = FBrowser_浏览器_通过ID取浏览器 (浏览器ID)`）、`src/MCP_Server_Core.wsv:5788`（锚点 `other = FBrowser_浏览器_通过ID取浏览器 (otherID)`） | ✅ 覆盖确凿 |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_通过序号取浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 注释 = " 通过内置浏览器清单的顺序号获取浏览器类，如果获取失败将返回一个空浏览器，注意判断">` / `参数 序号 <类型 = 整数 注释 = "从0开始">` → `FBroHsBrowserListControl_GetBrowserFromIndex(@<序号>)`（`FBroLib.wsv:487-492`） | **真缺口**（运行期可做） | 零命中：`通过序号取浏览器|通过序号|取序号` 全目录 `No matches found`（含 `*.~vbak.wsv`）。对照：同族另三兄弟全部已覆盖（`通过ID`→`browser_close`/`browser_list`；`通过用户标识`→`browser_find_by_tag`；`通过窗口句柄`→`browser_find_by_hwnd`） | ✅ **真缺口确认**：这是同族 4 个"取浏览器"入口中**唯一未被接线的**。`browser_list` 已返回有序 id 列表，AI 可自行按序取 id，故价值中等（便利性/一次调用定位） |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_通过用户标识取浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 注释 = "通过浏览器标识取出浏览器类…">` / `参数 用户标识 <类型 = 文本型>` → `FBroHsBrowserListControl_GetBrowserFromFlag(@<用户标识>.GetText())`（`FBroLib.wsv:501-506`） | **已覆盖** | 工具 **`browser_find_by_tag`**：注册 `src/MCP_Server.wsv:9764` `添加工具JSON ("browser_find_by_tag", "按标识查找浏览器", 单参数Schema文本 ("tag", "text", "标识"))`；分派 `src/MCP_Server_Core.wsv:5650`（锚点 `否则 (方法名 == "browser_find_by_tag")`）+ `:5659`（锚点 `found = FBrowser_浏览器_通过用户标识取浏览器 (tag)`） | ✅ 覆盖确凿（名字不同但直调同名类库方法） |
| `FBrowser辅助功能` | `方法 FBrowser_浏览器_通过窗口句柄取浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 注释 = " 通过浏览器的窗口句柄取浏览器，注意这里是浏览器的窗口句柄，不是浏览器父窗口的句柄" ...>` / `参数 窗口句柄 <类型 = 变整数>` → `FBroHsBrowserListControl_GetBrowserFromWindowHandle((HWND)@<窗口句柄>)`（`FBroLib.wsv:494-499`） | **已覆盖** | 工具 **`browser_find_by_hwnd`**：注册 `src/MCP_Server.wsv:9765` `添加工具JSON ("browser_find_by_hwnd", "按句柄查找浏览器", 单参数Schema文本 ("hwnd", "integer", "窗口句柄"))`；分派 `src/MCP_Server_Core.wsv:6038`（锚点 `否则 (方法名 == "browser_find_by_hwnd")`）+ `:6047`（锚点 `found = FBrowser_浏览器_通过窗口句柄取浏览器 (hwnd)`），失败文案含 `"如何取得有效句柄: 调 browser_get_window_handle(返回当前浏览器窗口句柄) 或 browser_window_info 看 hwnd 字段…"` | ✅ 覆盖确凿（注意类库警示"是浏览器的窗口句柄，不是父窗口句柄"，工具描述未复述该约束） |
| `FBrowser辅助功能` | `方法 FBrowser_清理全局缓存 <公开 静态 注释 = "非cef自带功能，FBrowser特有内核实现功能，清理浏览器缓存，支持占用状态下清理appcache,cache_storage,cookies,indexeddb,local_storage,service_workers,websql">` / `参数 源地址/清理对象/存储类型/结果回调` → `FBroHsBrowser_ClearGlobalCacheData(...)`（`FBroLib.wsv:459-479`） | **已覆盖** | 工具 **`browser_clear_cache`**：注册 `src/MCP_Server.wsv:9678`（稳定文件）`添加工具JSON ("browser_clear_cache", "清理CEF全局缓存\| 异步; 影响所有浏览器实例, 不只当前页")`；分派 `src/MCP_Server_Core.wsv:1257`（锚点 `否则 (方法名 == "browser_clear_cache")`）+ `:1264` `FBrowser_清理全局缓存 (, , , 清理缓存回调)`。粒度版工具 `browser_clear_cache_browser` 亦已注册 `src/MCP_Server.wsv:9679`（分派 `src/MCP_Server_Core.wsv:6088`，锚点 `否则 (方法名 == "browser_clear_cache_browser")`），描述明写按对象/存储类型位或语义 | ✅ **确认误报**（任务背景中的猜测成立）。注：`browser_clear_cache` 走"全局"，`browser_clear_cache_browser` 走逐浏览器+`targets`/`storage_types` 粒度 |

---

## 4. 真缺口清单

### 4.1 「运行期可做」真缺口（19 条）

> 判定口径：这些方法作用在**运行期可获得的宿主对象**上（菜单模式对象由 CEF 在"即将打开菜单"事件里交到回调手上；其余为静态查询/转换），**不需要重启进程、不需要在 CEF 初始化前设置**。

#### A 组：右键菜单模型（13 条，`类_FBrowser_菜单模式`）—— 建议工具 `browser_context_menu`

| # | 类库方法 | 建议工具名 | 应实现的文件 / 类 | 备注 |
|---|---|---|---|---|
| A1 | `添加菜单`（`FBroLib.wsv:3331`） | `browser_context_menu`（`action=add_item`） | 分派 `src/MCP_Server_Core.wsv`（建议与 `browser_kernel_menu` 族相邻或独立段）；注册 `src/MCP_Server.wsv`（建议紧邻 `:9797` 的 `browser_kernel_menu` 注册处）；**通道**在 `src/MCP_BrowserEvents.wsv` 的 `浏览器_即将打开菜单`（override 头 `:2658`，形参 `菜单模式` `:2662`） | **必须两条腿**：① 构建器把 AI 下发的菜单 JSON 存到 `MCP命令服务器` 的一个静态字段；② 在 `浏览器_即将打开菜单` 回调里（现有 `记录监控事件` 之外）读该字段并**原地写回** `菜单模式` |
| A2 | `添加子菜单`（`:3356`） | 同上（`add_submenu`，支持嵌套 `items[]`） | 同上 | 返回 `类_FBrowser_菜单模式` 子对象，可递归建树 |
| A3 | `添加分隔栏`（`:3325`） | 同上（`add_separator`） | 同上 | |
| A4 | `添加Check菜单`（`:3339`） | 同上（`add_check`） | 同上 | |
| A5 | `添加Radio菜单`（`:3347`） | 同上（`add_radio`，参数 `群ID`） | 同上 | |
| A6 | `选中状态`（`:3437`） | 同上（`check`，参数 `命令ID`/`选中`） | 同上 | 依赖 A1-A5 先行 |
| A7 | `选中状态_索引`（`:3444`） | 同上（`check_at`，参数 `索引ID`/`选中`） | 同上 | 依赖 A1-A5 先行 |
| A8 | `设置快捷键`（`:3464`） | 同上（菜单项 `accelerator` 子字段） | 同上 | 类库注释已明写"只是用于显示快捷键，触发需自行用键盘事件实现" → **只是观感** |
| A9 | `设置快捷键_索引`（`:3474`） | 同上（`accelerator_at`） | 同上 | 同上 |
| A10 | `移除快捷键`（`:3484`） | 同上（`remove_accel`） | 同上 | 同上 |
| A11 | `移除快捷键_索引`（`:3490`） | 同上（`remove_accel_at`） | 同上 | 同上 |
| A12 | `存在快捷键`（`:3451`） | 同上（`has_accel`，查询类） | 同上 | **从属项**：只有 A1-A5 落地后有对象可查 |
| A13 | `存在快捷键_索引`（`:3457`） | 同上（`has_accel_at`，查询类） | 同上 | 同上 |

**A 组建议要点（不写实现代码）**
- 现有 `browser_kernel_menu`（屏蔽）与之**互斥**：需定义优先级（建议"有自定义菜单时不再屏蔽"），否则 `屏蔽快捷菜单=真` 会让自定义菜单也看不见。
- 命令回调侧已有现成落点可让自定义菜单项**真的产生行为**：`src/MCP_BrowserEvents.wsv:2670` `方法 浏览器_菜单被调用 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>`（形参含 `菜单模式` 与 `运行命令菜单回调`，当前只 `记录监控事件` 后 `返回 (假)`）；`:2685` `方法 浏览器_菜单被点击 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>`（形参含 `命令ID`）。
- 类库侧完整可用面远大于 13 条（见 §3.1 末注，含 `清空菜单`/`删除菜单`/`置菜单标签`/`置可见状态`/`置禁止状态`/`取子菜单`/`置颜色`/`置字体` 等 23 个 0 命中方法），建议 schema 一次设计到位。

#### B 组：其余 6 条「运行期可做」真缺口

| # | 类库方法 | 建议工具名 | 应实现的文件 / 类 | 价值 | 备注 |
|---|---|---|---|---|---|
| B1 | `FBrowser_浏览器_通过序号取浏览器`（`FBroLib.wsv:487`，`GetBrowserFromIndex(序号)`） | 并入 `browser_list` 的 `index` 参数，或新增 `browser_select {index}` | 分派 `src/MCP_Server_Core.wsv` 的 `browser_list` 分支（锚点 `否则 (方法名 == "browser_list")`）与 `browser_close` 分支（锚点 `否则 (方法名 == "browser_close")`）；注册 `src/MCP_Server.wsv:9664` / `:9662` | **中** | 同族 4 个"取浏览器"入口中唯一未接线的；`browser_list` 已返回有序 id，AI 可自行按序取 id，故属便利性提升 |
| B2 | `FBrowser_Parser_取数据URI`（`FBroLib.wsv:394`） | `browser_to_data_uri {mimetype, data}` | 分派 `src/MCP_Server_Core.wsv` 的编码族（锚点 `// === Base64编码/解码 (FBrowser官方API) ===`）；注册 `src/MCP_Server.wsv` 紧邻 `:9753-9756` | **低** | ⚠ 两个参数都是**文本型**，不能用于任意字节集/文件；只在配合 `browser_kernel_scheme` 注入内联资源时才有价值 |
| B3 | `FBrowser_Parser_写入JSON`（`FBroLib.wsv:450`） | `browser_json_write` | 同上 | **低** | 需先能构造 `类_FBrowser_值`；src 内 JSON 序列化已统一走 `YYJSON对象类` |
| B4 | `FBrowser_Parser_字节值解析为JSON`（`FBroLib.wsv:443`） | `browser_json_parse_binary` | 同上 | **极低** | 可由 `browser_base64_decode`（锚点 `字节结果 = FBrowser_Parser_Base64解码 (data)`）取到 `类_FBrowser_字节集` 后使用，但 MCP 侧传文本更直接 |
| B5 | `FBrowser_启用异常收集`（`FBroLib.wsv:531`） | **不建议做工具** | — | **无** | ⚠ 类库原文自述"火山版本内置已经设置了，所有这个没用" |
| B6 | `异常收集回调模板函数`（`FBroLib.wsv:523`） | **不建议做工具** | — | **无** | ⚠ 类库标注 `<静态>` **无 `<公开>`**，仅为 B5 的 `@匹配方法` 模板，非独立用户 API |

### 4.2 「仅启动期生效（本项目运行期不可达）」真缺口（14 条）

> 判定口径：这些开关只在 **CEF 初始化之前**对命令行对象设置才有效。本项目 `FBrowser_初始化` 在 `src/main.wsv:98` 执行，此后**任何运行期代码都无法补救**；且全 src 对 `类_FBrowser_命令行` 的**方法调用为 0**（§3.2 证据 1），连"启动期接线"本身都不存在。

| # | 类库方法 | 建议工具名 / 通道 | 应实现的文件 | 备注 |
|---|---|---|---|---|
| C1 | `设置远程调试端口`（`FBroLib.wsv:1916`） | `browser_kernel_cmdline`（只写配置 + 明确返回"需重启生效"） | 配置字段写到 `src/MCP_Server.wsv` 静态字段；**启动期落点** = `src/main.wsv` 的 `即将处理命令行`（override 头 `:475`，形参 `命令行` `:477`，**现成钩子且方法体是空的**）或 `浏览器_即将启动子进程`（`:489`）或 `启动方法` 中 `:98` 之前 | **本族最高价值**。唯一增量 = 外部 Playwright/Puppeteer/CDP 客户端可 attach 本进程（项目内 `browser_cdp_call` 已覆盖内部 CDP 需求） |
| C2 | `插入值`（`:1865`） | 同上（`browser_kernel_cmdline {append:"..."}`） | 同上 | ⚠ **类库实现与注释不符**：注释称 `PrependWrapper`（前置），`:1870` 实际调 `FBroHsCommandLine_AppendArgument`（追加）→ 语义等同 `置额外参数`，**不是前置** |
| C3 | `启用无头模式`（`:1909`） | 同上（**绕开类库方法**，改用 `置值("headless")` = `FBroLib.wsv:1828` `AppendSwitch`，src 0 调用） | 同上 | ⚠ **类库方法实现有缺陷**：`:1912` 调的是 `FBroHsCommandLine_EnableAutoplayPoliey`（自动播放），**并未设置 `--headless`**。且**需求已由 `browser_create {background:true}` 覆盖**（`src/MCP_Server.wsv:9661`）→ 建议不单独实现；若要实现须在文档写明"进程级、需重启、与嵌入式容器渲染冲突" |
| C4 | `启用自动播放`（`:1902`） | 同上（`browser_kernel_cmdline {autoplay:true}`） | 同上 | 媒体自动化前置；中等价值 |
| C5 | `禁用代理`（`:1968`） | 同上（`browser_kernel_cmdline {no_proxy:true}`） | 同上 | **运行期无等价替代**：`browser_clear_proxy`（`src/MCP_Server_Core.wsv:1414`，锚点 `否则 (方法名 == "browser_clear_proxy")`）只清类库设过的代理，不能关掉**系统自动检测代理**（`--no-proxy-server` 语义） |
| C6 | `禁用GPU`（`:1924`） | 同上（`browser_kernel_cmdline {disable_gpu:true}`） | 同上 | 虚拟机/无 GPU 环境稳定性 |
| C7 | `禁用GPU缓存`（`:1931`） | 同上（`{disable_gpu_cache:true}`） | 同上 | 同族 |
| C8 | `忽略GPU禁用清单`（`:1938`） | 同上（`{ignore_gpu_blocklist:true}`） | 同上 | 老显卡兼容排障 |
| C9 | `启用摄像头`（`:1881`） | 同上（`{media_stream:true}`） | 同上 | 权限侧已被 `browser_permission_spoof`（`src/MCP_Server_Core.wsv:3299`，锚点 `否则 (方法名 == "browser_permission_spoof")`）部分替代，**但那是 JS 层伪装，不等价于 `enable-media-stream` 内核开关** |
| C10 | `启用录音`（`:1895`） | 同上（`{speech_input:true}`） | 同上 | 无人值守场景需求弱 |
| C11 | `启用跨框架操作模式`（`:1888`） | 同上（`{cross_frame:true}`） | 同上 | 项目已有 `browser_frame_*` 族工具，非必需 |
| C12 | `启用单进程模式`（`:1874`） | 同上（**建议不做**） | 同上 | 类库自述"只为了方便多进程模拟调试，仅调试模式下有用，单进程模式存在各种问题，不建议发布软件使用" |
| C13 | `FBrowser_命令行_取全局`（`:1753`） | 同上的**前置入口** | 同上 | **基础设施**：取 CEF 全局命令行对象的唯一入口；不做它则 C1-C12 全部无从下手 |
| C14 | `FBrowser_命令行_创建`（`:1747`） | 同上（可选，仅测试/预演用） | 同上 | **基础设施**：自建命令行对象，**不改 CEF 生效开关** |

**C 组建议形态（不写实现代码）**：不要做成"运行期工具"，而应做成**启动参数通道**——由 MCP 进程自身的启动参数（或环境变量）承载，在 `src/main.wsv` 的 `即将处理命令行`（`:475`）/`浏览器_即将启动子进程`（`:489`）/`启动方法` 中 `FBrowser_初始化`（`:98`）之前落值；另加一个**只读**工具（如 `browser_kernel_cmdline`）回显当前生效开关集，便于 AI 自检。工具若存在，语义必须明写"需重启生效"。

---

## 5. 我无法确定的

以下各项**没有静态证据可以定案**，我**没有**、也**不能**声称已验证：

1. **`即将处理命令行` 的精确派发时机。** `src/main.wsv:475` 的 override 形参含 `类_FBrowser_命令行`，静态证据只能证明"该 override 存在且方法体为空"。它究竟在 `FBrowser_初始化`（`src/main.wsv:98`）**内部**（CEF `OnBeforeCommandLineProcessing` 语义）还是**之前**派发，我无法从 `.wsv` 源码判断。两种读法下它都是"命令行生效前"的合法落点，但**"在此处设置必然生效"属类库运行期契约，须实测或查类库文档才能定案**（确定办法：读 FBrowser 类库 `FBrowser初始化控制` / `类_FBrowser_应用事件` 的事件语义说明或官方文档，或做一次受控实测）。
2. **`浏览器_即将打开菜单` 事件在本项目实际是否会被 CEF 触发。** override 存在（`src/MCP_BrowserEvents.wsv:2658`）、形参含 `菜单模式`（`:2662`）是静态事实；但该事件是否真的在右键时被调用，取决于 FBrowser 内核与 `类_MCP_BrowserEvents` 是否被真正注册为事件接收方。**这决定了 A 组 13 条是否真的"运行期可做"**——若该事件实际不触发，A 组将整体降级为不可达。（确定办法：开启 `browser_collect {event_menu_enable}` 后右键一次，看 `context_menu_opening` 是否真的进事件缓冲；或在 IDE 中对该 override 下断点。**本次禁止运行，故未做**。）
3. **`browser_kernel_menu`（屏蔽）与自定义菜单同时存在时的内核优先级。** 我只能确认两者是**不同的代码路径**（`src/MCP_Kernel.wsv:522`/`:527` 置位 vs `src/MCP_BrowserEvents.wsv:2567` 消费；菜单模型侧无任何写入），无法判断内核在"事件返回真（阻止默认行为）+ 菜单模型已被修改"时如何取舍。
4. **`类_FBrowser_菜单模式` 各方法的返回值语义是否被内核真正采纳。** 例如 `添加菜单` 返回 `逻辑型`（`FBroLib.wsv:3331`），但"返回真是否代表 CEF 侧菜单模型已生效"属运行期行为。另 `设置快捷键` 类库注释已自述"只是用于显示快捷键，触发需自行用键盘事件实现"（`:3464`），故 A8-A11 即便接线也**只改观感不改行为**——这点由类库注释所述，我未实测。
5. **`启用异常收集` 的"火山版本内置已经设置了，所有这个没用"是否属实。** 这是 `FBroLib.wsv:531` 的**类库注释原文**，我照录并据此建议不实现；但"内置是否真的已生效、生效到哪里、产物在哪"我无法静态确认（确定办法：查火山运行时/封装层是否已调用 `FBroHsDumpStart`，或做一次受控崩溃看是否产生 dump 文件——**本次禁止运行，故未做**）。
6. **`设置全局代理`（命令行）与 `browser_set_proxy`（运行期）的语义差是否会在真实场景暴露。** 我判定为"已覆盖"的依据是用户能力等价（设代理/带账号密码/持久化到新浏览器，`src/MCP_Server_Core.wsv:1401` + `src/MCP_Server.wsv:2042`）；但类库 `FBroHsCommandLine_SetProxy` 是**进程级全局**、`类_FBrowser_浏览器::设置代理` 是**逐浏览器**，两者在"多浏览器不同代理"或"CEF 子进程（渲染/GPU/网络进程）级代理"场景下是否表现一致，**我无法静态判断**。
7. **`src/MCP_Server_Core.wsv` 的行号稳定性（重要）。** 本文件在本次分析期间被并发写入（行数 7563 → 7583 → 7632），我**无法保证**交付后行号仍与 §0 快照一致，也**无法得知写入者改动了哪些行**。因此我对该文件的引用一律附带锚点原文；**若需绝对可靠，请以锚点原文 grep 定位**。同时这也是一个残余风险：**若并发写入恰好改动了 `browser_base64_encode` / `browser_uri_encode` 等分支或 `browser_find_by_*` 分支，本报告的"已覆盖"结论需重新核验**（我最后一次核验的时刻为 `06:01:55`，快照 sha256 前 16 位 `A6A199AD1403BB67`）。
8. **候选清单本身的完整性。** §3.1 末注指出 `类_FBrowser_菜单模式` 有 34 个 0 命中方法而候选只列了 13 个。造成差异的原因（`_audit/classlib_gap.py` 的生成口径）我未审阅其源码，故**不排除其余两个类也存在同类漏列**——例如我未系统清点 `类_FBrowser_命令行` 的 `是否为空/置空/是否有效/是否只读/取字符串/取程序/置程序/是否存在项/是否存在某项/取项值/置值/置项值/是否存在额外参数/取额外参数/置额外参数/VIP_高级_设置全局代理`（`FBroLib.wsv:1758-1973`）以及 `FBrowser辅助功能` 是否还有非候选方法。**本报告只对任务给定的 46 条候选负责。**

---

## 6. 依据方法与可复现的检索式

| 检索目的 | 检索式 | 结果 |
|---|---|---|
| 三个类只作形参用 | `FBrowser辅助功能\|类_FBrowser_命令行\|类_FBrowser_菜单模式` on `src/**/*.wsv` | 4 命中（`MCP_BrowserEvents.wsv:2662`、`:2674`、`main.wsv:477`、`:490`）——**全部是形参声明，无一处方法调用** |
| 命令行全族零调用 | `插入值\|FBrowser_命令行_创建\|FBrowser_命令行_取全局\|启用单进程模式\|启用录音\|启用摄像头\|启用无头模式\|启用自动播放\|启用跨框架操作模式\|忽略GPU禁用清单\|禁用GPU\|禁用GPU缓存\|禁用代理\|设置远程调试端口` | **`No matches found`** |
| 菜单模式全族零调用 | `菜单模式.` ；以及 `添加菜单\|添加分隔栏\|添加子菜单\|添加Check菜单\|添加Radio菜单\|选中状态\|设置快捷键\|移除快捷键\|存在快捷键\|清空菜单\|取快捷键\|置可见状态\|置禁止状态` | 两次均 **`No matches found`** |
| 辅助功能零命中项 | `通过序号\|取序号\|通过序号取浏览器` ；`取数据URI\|data_uri\|dataURI` ；`写入JSON\|json_stringify\|json_write\|browser_json` ；`字节值解析为JSON` ；`异常收集\|DumpStart\|_EXCEPTION` | 均 **`No matches found`** |
| 远程调试零命中 | `远程调试\|remote_debug\|debugging_port\|webSocketDebuggerUrl\|ws_url\|devtools_url\|devtoolsFrontendUrl` | **`No matches found`** |
| 已有覆盖工具（注册侧） | `添加工具JSON \("(browser_clear_cache\|browser_meta\|browser_list\|browser_close\|browser_base64_encode\|browser_base64_decode\|browser_uri_encode\|browser_uri_decode\|browser_user_tags\|browser_find_by_tag\|browser_find_by_hwnd\|browser_set_proxy)"` | 全部在**活动文件** `src/MCP_Server.wsv`（`9662`/`9664`/`9678`/`9688`/`9689`/`9753`/`9754`/`9755`/`9756`/`9763`/`9764`/`9765`）命中 |
| 已有覆盖工具（实现侧） | `FBrowser_Parser_Base64编码\|…\|FBrowser_清理全局缓存\|browser_clear_cache\|browser_meta` | `src/MCP_Server_Core.wsv` 命中（行号见 §3.3，均附锚点） |
| 工具总数复核 | `添加工具JSON \("` 计数 | **313** |

**关于备份文件的处理**：`src` 下存在 `*.~vbak.wsv` 备份（`main_1`、`MCP_Server_1/_2`、`MCP_Kernel_1/_2`、`MCP_BrowserEvents_1`）。本报告的"零命中"结论均在**含备份在内**的全目录检索下成立（即连备份里都没有，是最强形式）；"已覆盖"证据均取自**活动文件**，备份中出现的相同注册（如 `MCP_Server_1.~vbak.wsv:8344`）仅作旁证，未被当作依据。

---

## 7. 结论一句话

46 条候选中 **13 条是误报（已覆盖）**、**33 条是真缺口**；其中 **14 条属 `类_FBrowser_命令行` 的启动期开关（本项目运行期不可达，须做启动参数通道而非运行期工具）**，**真正"运行期可做且有工具价值"的是 14 条：13 条 `类_FBrowser_菜单模式`（右键菜单模型构建 + 快捷键，建议 `browser_context_menu`）与 1 条 `FBrowser辅助功能::通过序号取浏览器`**。

---

## 8. 「运行期可做」真缺口 Top 5（按建议优先级）

| 排名 | 建议工具名 | 覆盖的类库方法（条数） | 类库位置 | 建议实现位置 | 价值与理由 |
|---|---|---|---|---|---|
| **1** | `browser_context_menu`（`action=add_item`/`add_submenu`/`add_separator`/`add_check`/`add_radio`/`check`/`check_at`） | `添加菜单`、`添加子菜单`、`添加分隔栏`、`添加Check菜单`、`添加Radio菜单`、`选中状态`、`选中状态_索引`（**7 条**） | `FBroLib.wsv:3331` / `3356` / `3325` / `3339` / `3347` / `3437` / `3444` | 通道：`src/MCP_BrowserEvents.wsv` `浏览器_即将打开菜单`（override `:2658`，形参 `菜单模式` `:2662`）；分派与注册：`src/MCP_Server_Core.wsv` + `src/MCP_Server.wsv`（紧邻 `:9797` `browser_kernel_menu`） | **最高**。形参已在手却完全未用（`:2666` 只记录事件）；`browser_kernel_menu` 只能整块屏蔽、语义相反；CDP 无菜单域、无替代路径。落地后 AI 可向右键菜单注入"用AI分析此元素"类自定义项 |
| **2** | 同上工具的菜单项 `accelerator` 子字段（`set_accel`/`set_accel_at`/`remove_accel`/`remove_accel_at`/`has_accel`/`has_accel_at`） | `设置快捷键`、`设置快捷键_索引`、`移除快捷键`、`移除快捷键_索引`、`存在快捷键`、`存在快捷键_索引`（**6 条**） | `FBroLib.wsv:3464` / `3474` / `3484` / `3490` / `3451` / `3457` | 与排名 1 **同一工具、同一通道**，仅多几个 action 与字段 | **高（边际成本近零）**。与排名 1 共用同一条"菜单写回"通道，接线后几乎零额外结构成本。⚠ 但类库注释明写"只是用于显示快捷键，触发需自行用键盘事件实现" → **只改观感不改行为**，故排第二 |
| **3** | `browser_select {index}`（或并入 `browser_list` 的 `index` 参数） | `FBrowser_浏览器_通过序号取浏览器`（1 条） | `FBroLib.wsv:487` | `src/MCP_Server_Core.wsv` 的 `browser_list` 分支（锚点 `否则 (方法名 == "browser_list")`）与 `browser_close` 分支 | **中**。同族 4 个"取浏览器"入口中**唯一未接线的**（另 3 个已由 `browser_close`/`browser_find_by_tag`/`browser_find_by_hwnd` 覆盖）；改动量极小、无新通道、无运行期不确定性，是"确定性最高"的一条 |
| **4** | `browser_to_data_uri {mimetype, data}` | `FBrowser_Parser_取数据URI`（1 条） | `FBroLib.wsv:394` | `src/MCP_Server_Core.wsv` 编码族（锚点 `// === Base64编码/解码 (FBrowser官方API) ===`）；注册 `src/MCP_Server.wsv` 紧邻 `:9753-9756` | **低**。实现成本极低（与已覆盖的 base64/URI 四工具同族、同位置），但 ⚠ 两个参数都是 `文本型`，**不能处理任意字节集/文件**；只在配合 `browser_kernel_scheme`（`mcp://` 动态内容）注入内联资源时才值得做 |
| **5** | `browser_json_write` | `FBrowser_Parser_写入JSON`（1 条） | `FBroLib.wsv:450` | 同上 | **低**。MCP 协议本身就是 JSON，AI 侧无需宿主代做序列化；且需先构造 `类_FBrowser_值`（src 中无此入口）。列为 Top 5 仅因它是"运行期可做"组里剩余的、能低成本补齐的一项 |

> **未进 Top 5 的"运行期可做"真缺口（4 条）**：`FBrowser_Parser_字节值解析为JSON`（`FBroLib.wsv:443`，极低价值）、`FBrowser_启用异常收集`（`:531`，**类库自述无用，建议不做**）、`异常收集回调模板函数`（`:523`，**非公开 API，建议不做**），以及 `设置全局代理` 虽已判覆盖但若要求"严格调用该类库方法"亦可补（`FBroLib.wsv:1945`）。
