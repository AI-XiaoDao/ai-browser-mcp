# 类库 API 面 → MCP 工具面 缺口清单（r106 按当前源码刷新）

> **只读静态分析产出。** 未编译、未运行、未调用任何 MCP 工具、未发起任何 HTTP 请求、未启动/重启/结束任何进程。
> 本文**不存在任何「已验证 / 已测试 / 实测通过」结论**；所有判定均为静态证据，并按强度标注。
> 唯一新建文件：本文件。除此以外未修改 ROOT 下任何已存在文件。

---

## 0. 证据快照与并发写入警告（**必读**）

### 0.1 本次分析期间 `src` 正在被并发写入

分析进行中发现 `src` 多个文件在会话内被另一进程持续写入（mtime 距我的读取时刻仅 **10 秒**）：

| 文件 | 长度 | 最后写入 | SHA-256 前 16 位 | 稳定性 |
|---|---:|---|---|---|
| `src/MCP_Server.wsv` | 664,727 B | **06:51:00** | **`301348459A564D30`** | ❌ **被反复并发写入**：会话内观察到 `664,727 → 665,232 →(06:49:39, `C7B1C16079B4E7FF`)→ 664,727`(06:51:00) |
| `src/MCP_Server_Core.wsv` | 510,267 B | **06:48:13** | `0AB7780C9D5FAC6B` | ❌ 被并发写入（长度 508,654 → 510,267） |
| `src/MCP_BrowserEvents.wsv` | 99,330 B | 06:43:57 | `3E327FA54B41233A` | ⚠ 会话内变动过 |
| `src/MCP_Server_Utils.wsv` | 3,100 B | 06:18:45 | `961265E9A80EB467` | ⚠ 变动过 |
| `src/MCP_Server_Reverse.wsv` | 173,476 B | 06:13:40 | `20E39D0B768FD64E` | ⚠ 变动过 |
| `src/MCP_Stdio.wsv` | 19,719 B | 06:18:00 | `1ECA422BD3B93797` | ⚠ 变动过 |
| `src/main.wsv` | 40,176 B | 09-13 04:59:44 | `FFBF32CB431C4AF3` | ✅ 全会话未变 |
| `src/MCP_Kernel.wsv` | 102,298 B | 04:37:08 | `F57B970E5F59BE20` | ✅ 未变 |
| `src/MCP_Server_VIP.wsv` | 103,365 B | 05:44:12 | `75A5A670FC0C1560` | ✅ 未变 |
| `src/MCP_Server_System.wsv` | 9,419 B | 05:02:15 | `2F268F86EF3FA3E4` | ✅ 未变 |
| `src/MCP_Callbacks.wsv` | 65,744 B | 01:31:25 | `C77F591C6D8F14C9` | ✅ 未变 |
| 类库基准 `FBroLib.wsv` 等 8 文件 | — | 不受本项目影响 | — | ✅ 行号稳定 |

**直接后果（我已实际观察到）**：同一个类库调用在两次读取中行号不同 ——
`vip_ctrl.过滤器_取消全部修改内容 ()` 首次扫描落在 `MCP_Server.wsv:8826`，数分钟后重读落在 `:8837`（其间 `MCP_Server.wsv` 长度 +505 B）。

**应对**：本报告所有 `MCP_Server_Core.wsv` / `MCP_Server.wsv` 引用**同时给出「稳定锚点原文」**（可直接 grep 定位，不受重编号影响），行号仅作参考。**若复核时行号对不上，请以锚点原文为准。** 类库文件（`FBroLib.wsv` 等）行号稳定，可直接引用。

**工具总数 = 314，已在 4 个不同时刻独立计数一致**：`06:49:33`、`06:49:53`、`06:52:0x`、`06:54:38`；期间 `MCP_Server.wsv` 至少被写入 2 次（内容哈希变化），但**注册条数始终为 314**。若复核时计数变化，说明写入方正新增/删除工具，本报告的 §1/§6-O1 需以当时计数为准。

### 0.2 判定口径（6 条覆盖路径 + 1 条例外）

判定「已覆盖」必须命中下列任一路径，并给出 `文件:行号` + 原文：

1. **成员调用**：`<对象>.类库方法名 (` 直接调用；
2. **静态/全局调用**：`类库方法名 (` 直接调用（`FBrowser辅助功能`、`FBrowser初始化控制`、`FBrowserVIP全局功能` 等全局类）；
3. **事件接线**：src 中以 `方法 <事件名>` 声明 override（事件类的方法不是被「调用」而是被「覆盖」，故用声明式判定）；
4. **请求级公共参数**：`browser_id` 等对所有工具生效的隐含参数；
5. **语义等价工具**：能找到描述明确对应、且实现分支真的落到同一底层能力的工具；
6. **等价替代通道**：项目自建通道实现了同一能力（须显式注明「非类库方法本身」）。

**例外（本报告新增，防反向误报）**：若类库方法名是**泛用短名**（`取类型`/`取地址`/`取数量`/`是否为空`/`置空`/`创建`/`设置`…），源码中的同名命中极可能来自**其它类的同名方法**，属**名称碰撞**。此类命中**不被采信为覆盖证据**，一律改判 `不确定` 或按类级可达性重新判定。本报告对 `类_FBrowser_菜单环境` 即采用「类级可达性」判定（见 §2.A1）。

### 0.3 类级可达性辅助证据

对类库全部 188 个类声明做了「类名在活动 src 中的非注释引用次数」扫描。用途：若某类在 src 中**只作为形参类型出现、从不消费**，则其全部访问器方法在本项目内**不可达**（这是比逐方法 grep 更强的证据）。

典型：
- `类_FBrowser_菜单环境` 在 src 中**仅 3 处、全部是形参类型声明**（`MCP_BrowserEvents.wsv:2661` / `:2679` / `:2694`），**无任何消费点** → 该类 19 个访问器全部不可达。
- `类_FBrowser_任务运行器` / `类_FBrowser_基础框架` / `类_FBrowser_值转换` / `FBrowser类辅助` / `类_FBrowser_事件智能指针` 引用数 = **0** → 纯基础设施。

⚠ 反向注意：类名引用数 = 0 **不等于**不可达 —— 全局静态类的方法可直接调用而从不写类名（如 `FBrowser辅助功能` 的 `FBrowser_Parser_Base64编码` 就是被直接调用的）。故类级扫描仅作**辅助**，不单独定案。

---

## 1. 基准数字（当前源码）

| 项 | 值 | 出具方式 |
|---|---:|---|
| **已注册工具总数** | **314** | `src/MCP_Server.wsv` 中 `添加工具JSON ("` 计数 = 314，唯一名 = 314（无重名） |
| 类库基准文件 | **8** | `资料/类库/FBrowser浏览器/`：`FBroLib.wsv`(287,774B) `FBroVip.wsv`(137,695B) `FBroEventControl.wsv`(143,472B) `FBroDataType.wsv`(77,608B) `FBroValue.wsv`(65,183B) `FBroCallback.wsv`(39,069B) `FBroConst.wsv`(36,976B) `FBroHelp.wsv`(3,753B) |
| 类库 `类` 声明 | 188 | 8 文件 `^类\s+` |
| 类库 `方法` 声明 | **1360** | 8 文件 `^\s*方法\s+` |
| 类库**去重方法名** | **978** | 多类同名（`是否为空`/`置空`/`取数量`…）大量存在 |
| 有调用/覆盖证据的方法名 | 328 | 成员调用 + 全局调用 + src override 声明三路合并（含名称碰撞噪声，已抽查） |
| 零证据方法名 | 650 → 512 | 扣除 src override 声明可解释的 138 个（事件类为主） |
| 剔除基础设施/数据包装类后的**能力候选** | **239** | 21 个能力类 |
| 候选三分结果 | **A=90 / B=55 / C=31 / D=63** | D = 非能力项，见 §5 |

> 说明：旧报告的「类库方法(去重) = 533（另排除基础设施 827）」是**另一套口径**（它按类做了白/黑名单过滤），与本轮 978/239 不可直接相减。本报告 §4 逐条给出与旧结论的对应关系。

---

## 2. A 真缺口（运行期可做）

**定义**：类库方法作用在**运行期就能拿到的宿主对象**上（浏览器对象、事件回调形参对象、全局静态入口），**不需要在 CEF 初始化之前设置、也不需要以离屏模式创建浏览器**，且**当前无任何工具或等价通道覆盖**。

**合计 92 条**（90 条来自 239 候选集，另 2 条 `取类型`/`取地址` 因名称碰撞未被自动列入候选，由类级阅读补入）。

### A1. `类_FBrowser_菜单环境`（CefContextMenuParams）—— 19 条 · **最高价值**

**类库位置**：`FBroLib.wsv`（类定义 `类_FBrowser_菜单环境`，方法 3151–3279）

| # | 类库方法原文 | 建议工具/字段 | 价值 |
|---|---|---|---|
| 1 | `方法 取横向位置 <公开 类型 = 整数 注释 = "英文名：pGetXCoord">`（`FBroLib.wsv:3163`） | `browser_context_menu_info` → `x` | 右键点坐标 |
| 2 | `方法 取纵向位置 <公开 类型 = 整数 注释 = "英文名：pGetYCoord">`（`:3169`） | 同上 → `y` | 同上 |
| 3 | `方法 取类型 <公开 类型 = 整数 注释 = "英文名：pGetTypeFlags" 返回值注释 = "参考 菜单类型.xxx 类型可叠加">`（`:3175`） | 同上 → `type_flags` | 判断点的是链接/图片/选中文本/编辑框 |
| 4 | `方法 取地址 <公开 类型 = 文本型 注释 = "英文名：pGetLinkUrl">`（`:3181`） | 同上 → `link_url` | **右键目标链接** |
| 5 | `方法 取完整地址 <公开 类型 = 文本型 注释 = "英文名：pGetUnfilteredLinkUrl">`（`:3188`） | 同上 → `unfiltered_link_url` | 未过滤链接（反跳转） |
| 6 | `方法 取源地址 <公开 类型 = 文本型 注释 = "英文名：pGetSourceUr">`（`:3195`） | 同上 → `source_url` | 媒体源 |
| 7 | `方法 取页地址 <公开 类型 = 文本型 注释 = "英文名：pGetPageUrl">`（`:3202`） | 同上 → `page_url` | 所在页 |
| 8 | `方法 取框架网页编码 <公开 类型 = 文本型 注释 = "英文名：pGetFrameCharset">`（`:3209`） | 同上 → `frame_charset` | 低 |
| 9 | `方法 取框架页地址 <公开 类型 = 文本型 注释 = "英文名：pGetFrameUrl">`（`:3216`） | 同上 → `frame_url` | 中 |
| 10 | `方法 是否存在图片 <公开 类型 = 逻辑型 注释 = "英文名：HasImageContents">`（`:3223`） | 同上 → `has_image_contents` | 中 |
| 11 | `方法 取媒体类型 <公开 类型 = 整数 注释 = "英文名：GetMediaType" 返回值注释 = "参考：媒体类型.***">`（`:3229`） | 同上 → `media_type` | 中 |
| 12 | `方法 取媒体类型标识 <公开 类型 = 整数 注释 = "英文名：GetMediaType" 返回值注释 = "参考：媒体标识.*** 因可能会出现多个标识，所以这里可以通过位与/位或/+判断">`（`:3235`） | 同上 → `media_type_flags` | 中 |
| 13 | `方法 取选择文本 <公开 类型 = 文本型 注释 = "英文名：GetSelectionText">`（`:3241`） | 同上 → `selection_text` | **高**：右键时选中的文本，AI 可直接拿去做「用AI分析这段」 |
| 14 | `方法 取错误单词 <公开 类型 = 文本型 注释 = "英文名：GetMisspelledWord">`（`:3248`） | 同上 → `misspelled_word` | 低 |
| 15 | `方法 取字典建议 <公开 类型 = 返回 FBrowser_文本数组>`（`:3255`） | 同上 → `dictionary_suggestions` | 低 |
| 16 | `方法 是否为编辑框 <公开 类型 = 逻辑型 注释 = "英文名：IsEditable">`（`:3261`） | 同上 → `is_editable` | 中 |
| 17 | `方法 是否为选择框 <公开 类型 = 逻辑型 注释 = "英文名：IsSpellCheckEnabled">`（`:3267`） | 同上 → `is_spell_check_enabled` | 低 |
| 18 | `方法 取编辑框类型标识 <公开 类型 = 整数 注释 = "英文名：GetEditStateFlags" 返回值注释 = "参考:编辑框标识.****">`（`:3273`） | 同上 → `edit_state_flags` | 中（能否粘贴/剪切/全选的位标志） |
| 19 | `方法 是否为Custom菜单 <公开 类型 = 逻辑型 注释 = "英文名：IsCustomMenu">`（`:3279`） | 同上 → `is_custom_menu` | 低 |

**应实现在哪个文件**：
- **通道已现成、形参已在手却完全未用** —— `src/MCP_BrowserEvents.wsv:2661` 参数 `菜单环境 <类型 = 类_FBrowser_菜单环境 @输出名 = "MenuParams">`（同款在 `:2679`、`:2694`）；
- 现有方法体只调 `记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), "")`，**从未读 `菜单环境` 任何访问器**；
- 落地方式：把上述字段拼进监控事件载荷（`browser_collect` / `browser_event` 通道）或新增只读工具 `browser_context_menu_info`，实现放 `src/MCP_Server_Core.wsv`（与 `browser_context_menu` 分支 `否则 (方法名 == "browser_context_menu")` 相邻）。

**为什么值得做（能力价值）**：这是**唯一**能让 AI 知道「用户/脚本到底在什么东西上按了右键」的通道。CEF 的 CDP **没有右键上下文域**，`browser_kernel_menu` 只能整块屏蔽，`browser_context_menu` 只能**写**菜单。缺了它，AI 收到 `context_menu_opening` 事件时只知道「某处右键了」。且形参已经在函数签名里躺了三个回调，属于**零新增通道成本**。

**证据强度**：**高**（类级引用扫描：`类_FBrowser_菜单环境` 在 src 中 3 处、全部为形参声明、0 消费点；19 个访问器方法名逐个 grep 全项目 0 命中）。

**不确定项**：这些访问器在回调内是否真能取到值属运行期契约，**我未实测**。

---

### A2. `类_FBrowser_菜单模式` 未接线部分（CefMenuModel）—— 26 条

**已有部分覆盖**：`browser_context_menu`（`src/MCP_Server.wsv:9998` 注册，分派 `src/MCP_Server_Core.wsv` 锚点 `否则 (方法名 == "browser_context_menu")`）通过**逐行规格文本 + 回调内重施**的方式，已接线 8 个方法（见 §4 C1）。**下列 26 个仍未接线**：

| # | 类库方法原文 | 建议 action / 字段 | 类别 |
|---|---|---|---|
| 1 | `方法 清空菜单 <公开 类型 = 逻辑型 注释 = "英文名：Clear">`（`FBroLib.wsv:3313`） | `action=clear_items`（注意与现存 `clear` 语义不同，后者是清规格） | 写 · 中 |
| 2 | `方法 取数量 <公开 类型 = 整数 注释 = "英文名：GetCount">`（`:3319`） | 回调载荷 → `item_count` | 查 · 低 |
| 3 | `方法 删除菜单 <公开 类型 = 逻辑型 注释 = "英文名：Remove"> 参数 命令ID <类型 = 整数>`（`:3364`） | 规格行加类型 `del` | 写 · 中 |
| 4 | `方法 取菜单标签 <公开 类型 = 文本型 注释 = "英文名：GetMisspelledWord">`（`:3371`） | 载荷 → `label` | 查 · 低 |
| 5 | `方法 置菜单标签 <公开 类型 = 逻辑型 注释 = "英文名：SetLable"> 参数 命令ID 参数 标签名`（`:3378`） | 规格行 `relabel` | 写 · 中 |
| 6 | `方法 取菜单类型 <公开 类型 = 整数 注释 = "英文名：GetType"> 参数 命令ID`（`:3386`） | 载荷 → `item_type` | 查 · 低 |
| 7 | `方法 取分组ID <公开 类型 = 整数 注释 = "英文名：GetType"> 参数 命令ID`（`:3392`） | 载荷 → `group_id` | 查 · 低 |
| 8 | `方法 取子菜单 <公开 类型 = 类_FBrowser_菜单模式 注释 = "英文名：AddSubMenu"> 参数 命令ID`（`:3398`） | 载荷（嵌套展开） | 查 · 低 |
| 9 | `方法 是否可见 <公开 类型 = 逻辑型 注释 = "英文名：IsVisable"> 参数 命令ID`（`:3405`） | 载荷 → `visible` | 查 · 低 |
| 10 | `方法 置可见状态 <公开 类型 = 逻辑型 注释 = "英文名：SetVisable"> 参数 命令ID 参数 可见`（`:3411`） | 规格行 `vis` | 写 · **中高** |
| 11 | `方法 是否禁止 <公开 类型 = 逻辑型 注释 = "英文名：IsEnable"> 参数 命令ID`（`:3418`） | 载荷 → `enabled` | 查 · 低 |
| 12 | `方法 是否选中 <公开 类型 = 逻辑型 注释 = "英文名：IsChecked"> 参数 命令ID`（`:3431`） | 载荷 → `checked` | 查 · 低 |
| 13 | `方法 选中状态_索引 <公开 类型 = 逻辑型 注释 = "英文名：SetCheckedAt"> 参数 索引ID 参数 选中`（`:3444`） | 规格行 `check_at` | 写 · 中 |
| 14 | `方法 存在快捷键 <公开 类型 = 逻辑型> 参数 命令ID`（`:3451`） | 载荷 → `has_accel` | 查 · 低 |
| 15 | `方法 存在快捷键_索引 <公开 类型 = 逻辑型 注释 = "英文名：HasAcceleratorAt"> 参数 索引ID`（`:3457`） | 载荷 → `has_accel_at` | 查 · 低 |
| 16 | `方法 设置快捷键_索引 <公开 类型 = 逻辑型 注释 = "只是用于显示快捷键，触发需自行用键盘事件实现"> 参数 索引ID 参数 键代码 参数 是否按下shift/ctrl/alt`（`:3474`） | 规格行 `accel_at` | 写 · 中 |
| 17 | `方法 移除快捷键 <公开 类型 = 逻辑型> 参数 命令ID`（`:3484`） | 规格行 `noaccel` | 写 · 中 |
| 18 | `方法 移除快捷键_索引 <公开 类型 = 逻辑型> 参数 索引ID`（`:3490`） | 规格行 `noaccel_at` | 写 · 中 |
| 19 | `方法 取快捷键 <公开 类型 = 逻辑型 注释 = "只是用于显示快捷键，触发需自行用键盘事件实现"> 参数 命令ID 参数 键代码<整数类> 参数 返回是否按下shift/ctrl/alt值<逻辑型类>`（`:3496`） | 载荷 → `accel` | 查 · 低 |
| 20 | `方法 取快捷键_索引 <公开 类型 = 逻辑型 …> 参数 索引ID …`（`:3517`） | 载荷 → `accel_at` | 查 · 低 |
| 21 | `方法 置颜色 <公开 类型 = 逻辑型> 参数 命令ID 参数 颜色类型<菜单颜色类型> 参数 A R G B`（`:3538`） | 规格行 `color` | 写 · 低（CEF 原生菜单模型不支持，FBro 扩展） |
| 22 | `方法 置颜色_索引 <公开 类型 = 逻辑型> 参数 索引ID（-1=默认） 参数 颜色类型 A R G B`（`:3550`） | 规格行 `color_at` | 写 · 低 |
| 23 | `方法 取颜色 <公开 类型 = 逻辑型> 参数 命令ID 参数 颜色类型 参数 返回A/R/G/B值<整数类>`（`:3563`） | 载荷 | 查 · 低 |
| 24 | `方法 取颜色_索引 <公开 类型 = 逻辑型> 参数 索引ID 参数 颜色类型 参数 返回A/R/G/B值`（`:3586`） | 载荷 | 查 · 低 |
| 25 | `方法 置字体 <公开 类型 = 逻辑型 注释 = "待验证"> 参数 命令ID 参数 字体清单<文本型，如 "Arial, Helvetica, Bold Italic 14px">`（`:3609`） | 规格行 `font` | 写 · 低（**类库自注「待验证」**） |
| 26 | `方法 置字体_索引 <公开 类型 = 逻辑型 注释 = "待验证"> 参数 索引ID 参数 字体清单`（`:3616`） | 规格行 `font_at` | 写 · 低（同上） |

**应实现在哪个文件**：
- 规格解析与施加：`src/MCP_Server.wsv` 方法 `应用菜单规格`（锚点 `方法 应用菜单规格`，当前 8178–8329 区段，已有 `顶层菜单`/`最近子菜单`/`目标模型`/`子模型` 四个 `类_FBrowser_菜单模式` 局部变量）；
- 分派：`src/MCP_Server_Core.wsv` 锚点 `否则 (方法名 == "browser_context_menu")`；
- 注册与描述：`src/MCP_Server.wsv:9998`；
- 通道：`src/MCP_BrowserEvents.wsv` 锚点 `方法 浏览器_即将打开菜单`（形参 `菜单模式` 在 `:2662`）。

**设计要点（重要，避免做成死工具）**：
- **查询类（下表标「查」的 13 条）不适合做成即时查询工具** —— 菜单模型只在回调内有效（类库/CEF 明令禁止回调外持引用，`browser_context_menu` 的描述原文已写明这一点）。它们的正确去处是**塞进事件载荷**（`context_menu_opening` 事件带上「当前默认菜单结构」），而不是新增 `browser_menu_get` 之类会恒失败的查询工具。
- **写入类**（`清空菜单`/`删除菜单`/`置菜单标签`/`置可见状态`/`选中状态_索引`/`设置快捷键_索引`/`移除快捷键`/`移除快捷键_索引`）可直接扩展现有**逐行规格文本**格式，边际成本近零。
- 现存 `browser_kernel_menu`（屏蔽快捷菜单）与之**语义相反**（描述原文：「注意: 本工具与 browser_kernel_menu(屏蔽快捷菜单)语义相反」），需保留优先级说明。

**证据强度**：**高**（26 个方法名在活动 src 全项目 0 命中；8 个已接线方法可逐行指出）。

**不确定项**：类库注释已自述快捷键「只是用于显示快捷键，触发需自行用键盘事件实现」（`:3464`）→ 快捷键相关 6 条**只改观感不改行为**；`置字体` 两条类库自注「待验证」。

---

### A3. `FBrowser辅助功能`（全局静态类）—— 4 条

| # | 类库方法原文 | 建议工具 | 价值 |
|---|---|---|---|
| 1 | `方法 FBrowser_浏览器_通过序号取浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 注释 = " 通过内置浏览器清单的顺序号获取浏览器类，如果获取失败将返回一个空浏览器，注意判断">`（`FBroLib.wsv:487`） | 并入 `browser_list` / `browser_close` 的 `index` 参数，或新增 `browser_select {index}` | **中**：同族 4 个「取浏览器」入口中**唯一未接线**的一个 |
| 2 | `方法 FBrowser_Parser_取数据URI <公开 静态 类型 = 文本型>`（`FBroLib.wsv:394`，第二参数 `mimetype`） | `browser_to_data_uri {mimetype, data}` | **低**：两参数都是文本型，不能处理任意字节集/文件 |
| 3 | `方法 FBrowser_Parser_写入JSON <公开 静态 类型 = 文本型>`（`FBroLib.wsv:450`） | `browser_json_write` | **低**：MCP 协议本身即 JSON；且需先构造 `类_FBrowser_值` |
| 4 | `方法 FBrowser_Parser_字节值解析为JSON <公开 静态 类型 = 类_FBrowser_值 注释 = "FBroHsParseJSON_BinaryValue">`（`FBroLib.wsv:443`） | `browser_json_parse_binary` | **极低** |

**已排除的同族 2 条（非能力项，不列为缺口）**：
- `方法 FBrowser_启用异常收集 <公开 静态 注释 = "火山版本内置已经设置了，所有这个没用" @嵌入式方法 = "">`（`FBroLib.wsv:531`）—— **类库原文自述无用**；
- `方法 异常收集回调模板函数 <静态 类型 = 整数>`（`FBroLib.wsv:523`）—— **无 `<公开>`**，仅为上者的 `@匹配方法` 模板，非独立用户 API。

**应实现在哪个文件**：分派 `src/MCP_Server_Core.wsv` 编码族（锚点 `// === Base64编码/解码 (FBrowser官方API) ===`，`FBrowser_Parser_Base64编码` 在 `:5497`、`_Base64解码` 在 `:5509`、`FBrowser_Parser_URI编码` 在 `:5528`）；注册 `src/MCP_Server.wsv` 紧邻 `browser_base64_encode` 等四条注册处。

**证据强度**：**高**（4 个方法名全项目 0 命中）。

---

### A4. `类_FBrowserVIP_控制器` —— 11 条

| # | 类库方法原文 | 建议工具/action | 价值 |
|---|---|---|---|
| 1 | `方法 高级_设置触发鼠标触摸事件 <公开 注释 = "在浏览器载入完成后调用,VIP功能，需要赞助后才能使用">`（`FBroVip.wsv:623`） | `browser_fingerprint {action:"mouse_to_touch"}` 或并入 `browser_vip_touch_emulation {trigger_mouse:true}` | **中高**：移动端仿真必需 —— 很多站点用 `ontouchstart` 分流，只开触摸仿真（`指纹_启用触摸事件`）不够，还要把鼠标事件转成触摸 |
| 2 | `方法 高级_执行JS_主框架 <公开 注释 = "…在主框架/顶级框架执行JS">`（`FBroVip.wsv:800`） | `browser_vip_execute_js_context {target:"main"}` | **中** |
| 3 | `方法 高级_执行JS_全部框架 <公开 注释 = "…在当前所有框架里面都执行JS代码，所有框架都会执行一遍，回调会被多次调取">`（`:821`） | 同工具 `{target:"all_frames"}` | **中**：一次注入所有 iframe，省 N 次往返 |
| 4 | `方法 高级_执行JS_框架序号 <公开>`（`:843`） | 同工具 `{target:"frame_index", index:N}` | **中** |
| 5 | `方法 高级_发送触摸事件 <公开 注释 = "…可不启用触摸模式发送触摸事件">`（`:866`） | 扩展现有 `browser_touch_*` 的 `points[]`（多点/压力/半径原始触摸） | **中**：现工具只发单点 |
| 6 | `方法 高级_发送键盘事件 <公开 注释 = "…向浏览器发送键盘事件，支持后台操作">`（`:932`） | 并入 `browser_key_event`（原始按键事件结构） | **低中** |
| 7 | `方法 高级_发送鼠标事件 <公开 注释 = "…向浏览器发送鼠标事件，支持后台发送">`（`:1032`） | 并入 `browser_mouse_*`（原始鼠标事件结构） | **低中** |
| 8 | `方法 高级触摸_单击 <公开 注释 = "…可不启用触摸模式发送触摸事件">`（`:920`） | `browser_touch_press` + `release` 组合，或 `browser_touch_tap` | **低**（现有两工具已可组合出） |
| 9 | `方法 指纹_清空调用计数 <公开>`（`FBroVip.wsv:211`） | `browser_fingerprint {action:"reset_count"}` | **低**：`action=count` **已覆盖**（`MCP_Server_Core.wsv:2217` 锚点 `返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))`），但只有「读计数」没有「清零」，无法做「清零后跑一轮页面看它探测了几次」的差值实验 |
| 10 | `方法 高级_创建标签浏览器 <公开 注释 = "…在当前谷歌UI界面创建一个新的Tab标签浏览器，设置了浏览器事件后即可和创建浏览器一样控制该标签浏览器">`（`:1201`） | `browser_create {as_tab:true}` | **中**（但需先改项目策略，见下） |
| 11 | `方法 取浏览器 <公开 类型 = 类_FBrowser_浏览器 注释 = "取出当前控制器对应的浏览器，如果不存在或者已经关闭将返回空">`（`:199`） | 无需新工具（内部已用 `browser.取VIP控制器 ()` 的反向） | **极低**：控制器→浏览器的反向查，AI 侧无场景 |

**已排除 1 条**：`方法 指纹_虚拟内核功能 <注释 = "弃用，VIP功能，需要赞助后才能使用，通过内核版本号虚拟当前浏览器内核，">`（`FBroVip.wsv:508`）—— **类库原文自注「弃用」**，不列为缺口。

**应实现在哪个文件**：`src/MCP_Server_VIP.wsv`（`browser_vip_execute_js_context` 锚点 `否则 (方法名 == "browser_vip_execute_js_context")`，现用 `vipCtrl.高级_执行JS_框架ID (jsCode, frmID, 真, 假, 真, …, VIPJS回调)`；`browser_vip_touch_emulation` 锚点 `否则 (方法名 == "browser_vip_touch_emulation")`）；`browser_touch_*` 在 `src/MCP_Server_Core.wsv:5546+`。

**证据强度**：**高**（11 个方法名全项目 0 命中；对照的「已覆盖方法」可逐行指出）。

---

### A5. `类_FBrowserVIP_开发者DOM` 未接线部分 —— 6 条

`browser_vip_dom_get_document` / `browser_vip_dom_search` 已接线 4 个方法（`启用`/`枚举DOM`/`预查找文本`/`取查找文本`，见 §4 C9）。下列 6 个仍未接线：

| # | 类库方法原文 | 建议 action | 价值 |
|---|---|---|---|
| 1 | `方法 移除节点 <公开>`（`FBroVip.wsv:1517`） | `browser_vip_dom_node {action:"remove"}` | 中（贴吧/论坛类批量清广告） |
| 2 | `方法 移除节点属性 <公开>`（`:1509`） | 同上 `{action:"remove_attr"}` | 中（清 `readonly`/`disabled`） |
| 3 | `方法 置节点名 <公开>`（`:1648`） | 同上 `{action:"rename"}` | 低 |
| 4 | `方法 清除查找 <公开>`（`:1553`） | 同上 `{action:"clear_search"}` | 低（查完释放） |
| 5 | `方法 取节点容器 <公开>`（`:1666`） | 同上 `{action:"container"}` | 低 |
| 6 | `方法 禁用 <公开>`（`:1497`） | 同上 `{action:"disable"}` | 低 |

**注意（防反向误报）**：该类另有 9 个方法**已有等价工具**，**不算缺口**（见 §4 C9）：`取节点_查询选择器`/`取全部节点_查询选择器` ↔ `browser_dom_query`/`browser_dom_select`；`取节点属性`/`置节点属性文本`/`置节点属性值` ↔ `browser_fill_attr_get`/`browser_fill_attr_set`；`取节点源码`/`置节点源码` ↔ `browser_dom_get_html`/`browser_dom_set_html`；`置节点值` ↔ `browser_dom_set_value`；`置焦点元素` ↔ `browser_fill_focus`。

**证据强度**：**中高**（6 个方法名 0 命中确定；但「等价」判定基于工具名语义 + 工具描述，**未逐个回溯等价工具的实现分支**，故「等价」部分标为中等强度）。

---

### A6. `类_FBrowser_浏览器` 未接线部分 —— 6 条

| # | 类库方法原文 | 建议工具 | 价值 |
|---|---|---|---|
| 1 | `方法 取窗口运行风格 <公开 类型 = 窗口运行风格>`（`FBroLib.wsv:1456`，`→ FBroHsBrowserHost_GetRuntimeStyle`） | 并入 `browser_get_run_style` 返回 `runtime_style` | **中**：现有 `browser_get_run_style`（`src/MCP_Server_System.wsv:95` 锚点 `否则 (方法名 == "browser_get_run_style")`）**并未调用该类库方法** —— 它返回的是 `browser.取窗口属性 (MCP_常量.窗口样式_GWL_STYLE)` + `browser.是否为弹窗 ()` + `browser.取ID ()`。即**工具名与类库方法同名同义，实现却绕开了它**，属「名字撞上了、能力没接上」 |
| 2 | `方法 取焦点填表框架 <公开 类型 = 类_FBrowser_填表框架 注释 = "英文名：GetFocusedFrame 说明：Returns the focused frame for the browser window.">`（`:1406`） | 并入 `browser_get_focused_frame` | 中（现工具用 `类_FBrowser_框架` 版 `取当前焦点框架 ()`，填表框架版未接线） |
| 3 | `方法 取填表框架_ID <公开 类型 = 类_FBrowser_填表框架 注释 = "英文名：GetFrame 说明：必须使用取框架ID取出的ID标识…">`（`:1414`） | 并入 `browser_frame_by_id` | 中 |
| 4 | `方法 取填表框架_名称 <公开 类型 = 类_FBrowser_填表框架 注释 = "英文名：GetFrame 说明：必须使用取框架名称取出的框架名…">`（`:1422`） | 并入 `browser_frame_by_name` | 中（现工具用 `类_FBrowser_框架` 版 `取框架_名称`） |
| 5 | `方法 取框架_ID <公开 类型 = 类_FBrowser_框架 注释 = "英文名：GetFrame 说明：必须使用取框架ID取出的ID标识，ID错误会导致返回值为空…">`（`:757`） | 并入 `browser_frame_by_id` | 中（按 ID 取框架，AI 侧只有按名取的入口） |
| 6 | `方法 进程间消息_发送数据_到主进程 <公开 类型 = 逻辑型 注释 = "在渲染进程中执行,失败返回0">`（`:1150`） | `browser_ipc_send_to_main` | 低（该方向是渲染→主，宿主侧基本用不到） |

**应实现在哪个文件**：`src/MCP_Server_Core.wsv`（`browser_get_focused_frame` 锚点 `否则 (方法名 == "browser_get_focused_frame")`；`browser_frame_by_name` 锚点 `否则 (方法名 == "browser_frame_by_name")`；`browser_frame_names` 锚点 `否则 (方法名 == "browser_frame_names")`；IPC 族锚点 `否则 (方法名 == "browser_ipc_renderer_count")` 等）；注册 `src/MCP_Server.wsv`。

**证据强度**：**高**（6 个方法名 0 命中；`browser_get_run_style` 的实现绕过已逐行读取确认）。

---

### A7. `类_FBrowser_填表框架` 未接线部分 —— 5 条

| # | 类库方法原文 | 对应底层 | 价值 |
|---|---|---|---|
| 1 | `方法 置元素内文本 <公开> 参数 选择器 参数 索引 参数 文本`（`FBroLib.wsv:5259`，`→ SetInnerText`） | **innerText 写** | 中：src 只用 `置元素内容` / `置元素内代码`（innerHTML 语义），**innerText 语义不同**（不解析 HTML、会转义 `<`） |
| 2 | `方法 取元素内文本 <公开> 参数 选择器 参数 索引 参数 结果回调`（`:5273`，`→ GetInnerText`） | **innerText 读** | 中：**无任何工具能取「元素 innerText」** —— `browser_get_text` 取整页文本，`browser_fill_attr_get` 取属性，`browser_dom_query` 取的是选项/结构 |
| 3 | `方法 置元素外文本 <公开> … 参数 文本`（`:5292`，`→ SetOuterText`） | **outerText 写** | 低 |
| 4 | `方法 取元素外文本 <公开> … 参数 结果回调`（`:5306`，`→ GetOuterText`） | **outerText 读** | 低 |
| 5 | `方法 置元素外代码 <公开> … 参数 代码文本`（`:5358`，`→ SetOuterHTML`） | **outerHTML 写** | 中：src 已用 `取元素外代码`（读 outerHTML）但**没有写回入口**，`browser_dom_set_html` 走的是内层 |

**应实现在哪个文件**：`src/MCP_Server_Form.wsv`（填表族实现，锚点 `填表框架.置元素内容 (selector, 0, value)`）与 `src/MCP_Server_Core.wsv`（`填表框架.取元素内容 (selector, 0, 文本回调)`）；注册 `src/MCP_Server.wsv`（`browser_fill_*` 族）。

**证据强度**：**高**（5 个方法名 0 命中；已接线同族方法 `置元素内容`/`取元素内容`/`置元素内代码`/`取元素内代码`/`取元素外代码` 可逐行指出）。

**不确定项**：`置元素外代码` 是否已被 `browser_dom_set_html` 以 JS 方式等价覆盖 —— **我未回溯该工具实现，标 `不确定`**（若已覆盖则应移入 C）。

---

### A8. `FBrowser初始化控制` 运行期可做部分 —— 3 条

| # | 类库方法原文 | 建议工具 | 价值 |
|---|---|---|---|
| 1 | `方法 FBrowser_JS交互_注册 <公开 静态 注释 = "FBroQueryFunctions"> 参数 JS执行函数名 参数 JS退出函数名 参数 JS交互事件<智能指针>`（`FBroLib.wsv:202`） | `browser_js_query_register` | **中高**：类库原生的「页面 JS ↔ 宿主」双向查询通道（配合 `即将查询`/`即将取消查询` 事件）。项目现用 CDP `Runtime.addBinding`（`browser_reverse_add_binding`，`src/MCP_Server_Reverse.wsv:1676` 锚点 `返回 (执行V8CDP命令 (命令ID, "Runtime.addBinding", …))`）**属另一套机制**（内核提供函数 vs 注册查询函数），二者不等价 |
| 2 | `方法 FBrowser_JS交互_删除 <公开 静态> 参数 JS执行函数名`（`:214`） | 同上 `{action:"unregister"}` | 中 |
| 3 | `方法 FBrowser_取初始化缓存目录 <公开 静态 类型 = 文本型 注释 = "取出初始化设置的真实缓存路径">`（`:252`，`→ FBroHsGetSetCachePath`） | 并入 `browser_cache_dir` | 低：现工具（`src/MCP_Server_System.wsv:49`）用 `取运行目录 () + "\\CacheData\\GlobalData"` **自行拼路径**，未回读内核真实值（若用户改过 `设置.缓存目录` 会不一致） |

**证据强度**：**高**（3 个方法名 0 命中）。

---

### A9. `类_FBrowser_请求环境` 未接线部分 —— 7 条

| # | 类库方法原文 | 说明 | 价值 |
|---|---|---|---|
| 1 | `方法 VIP_高级_载入插件路径 <公开>`（`FBroLib.wsv:2075`） | 从磁盘目录载入未打包插件 | 中：现有 `browser_vip_load_extension` 走的是 `VIP_高级_安装CRX插件包`（**已覆盖**，见 §4 C11），**未覆盖「目录形式加载」** |
| 2 | `方法 VIP_高级_取插件名`（`:2117`） | 取插件名 | 低：`VIP_高级_取插件地址`/`取插件路径` 已覆盖（同属 `extension_info`） |
| 3 | `方法 取Cookie管理器 <公开>`（`:2053`） | 取该请求环境的 Cookie 管理器 | **不确定**：项目用的是**全局** `FBrowser_Cookie管理器_取全局 ()`（`src/MCP_Server_Core.wsv:1089` 等 6 处），**逐请求环境的 Cookie 管理器是否等价，静态不可判** |
| 4 | `方法 FBrowser_请求环境_取全局 <公开 静态>`（`:1994`） | 取全局请求环境 | 低（基础设施入口） |
| 5 | `方法 是否为全局 <公开>`（`:2010`） | 判是否全局环境 | 低 |
| 6 | `方法 创建_其他 <公开>`（`:2023`） | 派生新请求环境 | 低中（多环境隔离是高级特性） |
| 7 | `方法 是否为分享 <公开>`（`:2037`） | 判是否共享 | 低 |

**已覆盖的同族 4 条（不算缺口）**：`VIP_高级_安装CRX插件包`、`VIP_高级_卸载插件`、`VIP_高级_取插件地址`、`VIP_高级_取插件路径` —— 均已由 `browser_vip_load_extension` / `browser_vip_unload_extension` / `browser_vip_extension_info` 接线（见 §4 C11）。

**应实现在哪个文件**：`src/MCP_Server_VIP.wsv`（插件族）；注册 `src/MCP_Server.wsv`。

**证据强度**：**中高**（方法名 0 命中确定；`取Cookie管理器` 等价性标 `不确定`）。

---

### A10. `类_FBrowser_服务器` 未接线部分 —— 6 条（价值低）

| # | 类库方法原文 | 说明 | 价值 |
|---|---|---|---|
| 1 | `方法 是否运行中 <公开 类型 = 逻辑型 注释 = "IsRunning：Returns true if the server is currently running and accepting incoming connections.">`（`FBroLib.wsv:4712`） | 服务器运行状态 | 低：项目自建 `变量 HTTP服务已尝试`（`src/MCP_Server.wsv` 锚点 `变量 HTTP服务已尝试 <公开 静态`）跟踪，未回读内核 |
| 2 | `方法 取服务器地址 <公开 类型 = 文本型 注释 = "GetAddress：Returns the server address including the port number.">`（`:4720`） | 服务器实际监听地址 | 低中：端口被占时能拿到真实绑定地址（现为请求参数回显） |
| 3 | `方法 是否存在连接 <公开 类型 = 逻辑型 注释 = "HasConnection：Returns true if the server currently has a connection.">`（`:4727`） | 是否有连接 | 低 |
| 4 | `方法 是否有效连接 <公开 类型 = 逻辑型 注释 = "IsValidConnection：Returns true if |connection_id| represents a valid connection."> 参数 连接ID`（`:4733`） | 连接有效性 | 低 |
| 5 | `方法 取任务运行器 <公开 类型 = 类_FBrowser_任务运行器 注释 = "GetTaskRunner：Returns the task runner for the dedicated server thread.">`（`:4772`） | 服务器线程任务运行器 | 低（基础设施） |
| 6 | `方法 关闭连接 <公开 注释 = "CloseConnection"> 参数 连接ID`（`:4789`） | 主动断开连接 | 低 |

**注意（类库实现缺陷，如实记录）**：`:4737` 的 `是否有效连接` 实现里调的是 `FBroHsServer_IsValidConnection(m_class)`，**未把形参 `@<连接ID>` 传进去** —— 与签名声明的语义不符（疑似类库封装漏参）。静态可见，**未实测**。

**已覆盖的同族 3 条（不算缺口）**：`发送Http200响应`/`发送Http404响应`/`发送Http500响应` ↔ 项目实际使用的 `发送HttpResponse` + `发送原始数据` + `发送WebSocket数据`（见 §4 C12）。

**证据强度**：**高**（6 个方法名 0 命中；封装漏参为逐行阅读所见）。

---

### A11. `FBrowserVIP注册` —— 3 条（价值低）

| # | 类库方法原文 | 说明 |
|---|---|---|
| 1 | `方法 VIP注册_取目标系统平台`（`FBroVip.wsv:49`） | 授权目标平台查询 |
| 2 | `方法 VIP注册_取错误信息`（`:57`） | **中低**：`browser_kernel_auth` 授权失败时缺一个明确的失败原因回读点 |
| 3 | `方法 VIP注册_生成本地授权文件`（`:89`） | 授权落盘 |

（同族 `取机器码`/`取开始时间`/`取到期时间`/`取注册功能`/`取注册版本`/`取注册码类型`/`置授权码` 等已被 `browser_kernel_auth` 覆盖。）

**证据强度**：**高**（3 个方法名 0 命中）。

---

### A 组价值排序 · Top 5

| 排名 | 建议工具/动作 | 覆盖类库方法（条数） | 类库位置 | 应实现位置 | 一句话理由 |
|---|---|---|---|---|---|
| **1** | `browser_context_menu_info`（只读；或直接并入 `context_menu_opening` 事件载荷） | `类_FBrowser_菜单环境` 全 19 条 | `FBroLib.wsv:3163-3279` | 通道 `src/MCP_BrowserEvents.wsv:2661/2679/2694`（形参已在手、0 消费）；实现 `src/MCP_Server_Core.wsv` | **形参已经在三个事件签名的函数表里躺了，却一个字都没读** —— 零新增通道成本，一次性让 AI 从「某处右键了」升级为「在 link=https://… 上右键，选中文本='…'，目标是编辑框，可粘贴」，而 CDP 完全没有右键上下文域、`browser_kernel_menu` 只能整块屏蔽。 |
| **2** | 扩展 `browser_context_menu` 规格格式（`del`/`relabel`/`vis`/`check_at`/`accel_at`/`noaccel`） | `清空菜单`、`删除菜单`、`置菜单标签`、`置可见状态`、`选中状态_索引`、`设置快捷键_索引`、`移除快捷键`、`移除快捷键_索引`（8 条写类） | `FBroLib.wsv:3313/3364/3378/3411/3444/3474/3484/3490` | 规格解析 `src/MCP_Server.wsv` 方法 `应用菜单规格`（现 8178–8329 区段） | 工具与通道**都已存在**（`browser_context_menu` + 回调内重施），只是规格行只认 5 种类型；加几个行类型即可从「能建菜单」升级到「能改菜单」，边际成本近零。 |
| **3** | `browser_js_query_register`（+ `unregister`） | `FBrowser_JS交互_注册`、`FBrowser_JS交互_删除`（2 条） | `FBroLib.wsv:202/214` | 分派 `src/MCP_Server_Core.wsv`；事件接线 `即将查询`/`即将取消查询` | 类库原生的**双向 JS↔宿主查询**通道，与项目现用的 CDP `Runtime.addBinding`（单向、内核提供函数）**不是一回事**；逆向/防检测场景下多一条不依赖 CDP 的通道价值很高。 |
| **4** | `browser_vip_execute_js_context` 增加 `main` / `all_frames` / `frame_index` 三档 target | `高级_执行JS_主框架`、`高级_执行JS_全部框架`、`高级_执行JS_框架序号`（3 条） | `FBroVip.wsv:800/821/843` | `src/MCP_Server_VIP.wsv` 锚点 `否则 (方法名 == "browser_vip_execute_js_context")`（现只接 `高级_执行JS_框架ID`） | 现在一次注入一个框架；`all_frames` 一次打穿所有 iframe，省掉「枚举框架 → N 次注入」的往返，对逆向 hook 铺全局脚本是刚需。 |
| **5** | `browser_fill_get_text` / `browser_fill_set_text`（innerText 读写） | `取元素内文本`、`置元素内文本`、`取元素外文本`、`置元素外文本`、`置元素外代码`（5 条） | `FBroLib.wsv:5259/5273/5292/5306/5358` | `src/MCP_Server_Form.wsv` + `src/MCP_Server_Core.wsv`；注册 `src/MCP_Server.wsv` | 填表族已有 13 个工具，**唯独没有「取元素 innerText」** —— 抓表格/列表单元格文本目前只能绕 `browser_execute_js` 或取整页 `browser_get_text`；innerText 与 innerHTML 语义不同（不解析、会转义），不能互替。 |

**未进 Top 5 但同属 A 组**：A4 的 VIP 输入事件族（6 条）、A5 的 DOM 节点增删（6 条）、A6 的框架/运行风格（6 条）、A9 的请求环境（7 条）、A10 服务器状态（6 条）、A11 授权（3 条）等。

---

## 3. B 仅启动期生效 / 运行期不可达

**合计 55 条。** 分三个子组，各有独立依据。

### B1. 仅启动期生效：`类_FBrowser_命令行`（CefCommandLine）—— 28 条

**依据**：这些开关只在 **CEF 初始化之前**对命令行对象设置才有效。本项目 `FBrowser_初始化 (设置, 初始化事件)` 在 `src/main.wsv:98` 执行；此后任何运行期代码都无法补救。**全 src 对 `类_FBrowser_命令行` 的方法调用为 0**，该类在 src 中**仅 2 处、全部是形参/事件签名**（`src/main.wsv:477` `参数 命令行`，见类级扫描）。

| 子类 | 条数 | 方法原文（类库位置） |
|---|---:|---|
| **真实开关**（建议做启动参数通道） | **14** | `插入值`(`FBroLib.wsv:1865`) `启用单进程模式`(`:1874`) `启用摄像头`(`:1881`) `启用跨框架操作模式`(`:1888`) `启用录音`(`:1895`) `启用自动播放`(`:1902`) `启用无头模式`(`:1909`) `设置远程调试端口`(`:1916`) `禁用GPU`(`:1924`) `禁用GPU缓存`(`:1931`) `忽略GPU禁用清单`(`:1938`) `设置全局代理`(`:1945`) `VIP_高级_设置全局代理`(`:1955`) `禁用代理`(`:1968`) |
| **基础设施入口**（不做则上面全无从下手） | **2** | `FBrowser_命令行_创建`(`:1747`) `FBrowser_命令行_取全局`(`:1753`) |
| **对象访问器/改写器**（同样仅启动期有意义） | **12** | `是否只读`(`:1778`) `取字符串`(`:1784`) `取程序`(`:1792`) `置程序`(`:1800`) `是否存在项`(`:1806`) `是否存在某项`(`:1811`) `取项值`(`:1819`) `置值`(`:1828`) `置项值`(`:1835`) `是否存在额外参数`(`:1843`) `取额外参数`(`:1849`) `置额外参数`(`:1857`) |

**建议形态**：**不要做成运行期工具**。做成**启动参数通道** —— 由 MCP 进程自身启动参数（或环境变量）承载，在 `src/main.wsv` 的 `即将处理命令行`（现成钩子，方法体为空）或 `浏览器_即将启动子进程` 或 `启动方法` 中 `FBrowser_初始化`（`:98`）**之前**落值；另加一个**只读**工具回显当前生效开关集。工具若存在，描述必须明写「**需重启生效**」。

**本族最高价值项**：`设置远程调试端口`（`:1916`）—— 唯一增量是**外部 Playwright/Puppeteer/CDP 客户端可 attach 本进程**（项目内 `browser_cdp_call` 已覆盖内部 CDP 需求）。

**如实记录的类库缺陷**：
- `插入值`（`:1865`）注释称 `PrependWrapper`（前置），`:1870` 实际调 `FBroHsCommandLine_AppendArgument`（**追加**）→ 语义等同 `置额外参数`，**不是前置**；
- `启用无头模式`（`:1909`）：`:1912` 调的是 `FBroHsCommandLine_EnableAutoplayPoliey`（**自动播放**），**并未设置 `--headless`** → 该方法是**错的**；若要无头应绕开它改用 `置值("headless")`（`:1828`）。且需求已由 `browser_create {background:true}` 覆盖（`src/main.wsv:221` 锚点 `FBrowser_创建后台浏览器 (bgUrl, 浏览器配置, …)`）。

**证据强度**：**高**（28 个方法名 0 命中 + 类级引用仅形参）。

**不确定项**：`即将处理命令行` 的精确派发时机（在 `FBrowser_初始化` **内部**即 CEF `OnBeforeCommandLineProcessing` 语义，还是**之前**）我无法从 `.wsv` 静态判定；两种读法下它都是「命令行生效前」的合法落点，但「在此处设置必然生效」属类库运行期契约，**须实测或查类库文档才能定案**。

---

### B2. 仅初始化前生效（进程级设置）—— 10 条

| # | 类库方法原文 | 依据（类库注释原文） |
|---|---|---|
| 1 | `方法 FBrowser_初始化_设置守护 <静态 注释 = "弃用，设置系统内部守护线程，必须在初始化之前设置…">`（`FBroLib.wsv:167`） | 原文「**必须在初始化之前设置**」；且已在类库中标注**弃用** |
| 2 | `方法 FBrowser_初始化_设置内存释放 <静态 注释 = "弃用，用于设置系统内部内存释放线程，必须在初始化之前设置…">`（`:174`） | 同上（弃用） |
| 3 | `方法 FBrowser_初始化_设置V8环境默认堆栈大小 <公开 静态 注释 = "…必须在初始化之前设置，只针对渲染进程；…">`（`:184`） | 原文「**必须在初始化之前设置**」 |
| 4 | `方法 FBrowser_设置程序DPI模式 <公开 静态 类型 = 逻辑型 注释 = "设置当前程序的DPI感知模式,在程序入口初始化之前调用">`（`:260`） | 原文「**在程序入口初始化之前调用**」 |
| 5 | `方法 启用自带调试提示 <公开 静态 注释 = "仅调试模式下有用，启用模块类调试输出提示…全部类初始化在全局所以该设置屏蔽不到已经初始化的事件类，只能屏蔽设置后的；">`（`:27`） | 调试输出开关，且受 `#ifdef _DEBUG` 包裹（`:31-33`），**发布版无效** |
| 6 | `方法 初始化调试信息显示 <静态>`（`:37`） | 无 `<公开>`，且方法体首行即 `如果真 (是否为调试版 ())` → 纯调试打印 |
| 7 | `方法 FBrowser_消息循环_执行 <公开 静态 注释 = "DoMessageLoopWork">`（`:121`） | 消息循环接管方式的选择。项目已用**配置**表达：`src/main.wsv:90` `设置.启用系统消息循环 = 真` → 走类库配置项而非手工调消息循环 API |
| 8 | `方法 FBrowser_消息循环_运行 <公开 静态 注释 = "RunMessageLoop">`（`:127`） | 同上 |
| 9 | `方法 FBrowser_消息循环_退出 <公开 静态 注释 = "QuitMessageLoop">`（`:133`） | 同上；项目用 `FBrowser_关闭 (真)`（`src/main.wsv:249`）收尾 |
| 10 | `方法 FBrowser_消息循环_设置系统模式 <公开 静态 注释 = "SetOSModalLoop"> 参数 系统模式`（`:139`） | 同上（OS 模态循环，控制台程序无场景） |

**证据强度**：**高**（依据为**类库自身注释原文**，非我推断）。

---

### B3. 运行期不可达（需离屏模式浏览器，本项目是窗口模式）—— 17 条

**依据**：这 17 个方法的类库注释**逐条自述**「**This method is only used when window rendering is disabled.**」（仅当窗口渲染被禁用时使用，即 CEF 离屏渲染 OSR 模式）。本项目以**窗口模式**创建浏览器：`src/main.wsv:203-209` 构造 `FBrowser_窗口信息`（`父窗口句柄 = 0` 即桌面为父窗口），`:228` `FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, …)` —— **不是**离屏模式。因此这些方法在本项目当前构建下**不产生任何效果**。

| # | 类库方法原文（`FBroLib.wsv`） |
|---|---|
| 1 | `方法 离屏渲染_离屏渲染被禁用 <公开 类型 = 逻辑型 注释 = "英文名：IsWindowRenderingDisabled Returns true if window rendering is disabled.">`（:1160） |
| 2 | `方法 离屏渲染_通知已被调整大小 <公开 注释 = "英文名：WasResized" … 注释 = "This method is only used when window rendering is disabled.">`（:1166） |
| 3 | `方法 离屏渲染_通知已被隐藏 <公开 注释 = "英文名：WasHidden" …`（:1174，参数 `隐藏`） |
| 4 | `方法 离屏渲染_通知屏幕信息被改变 <公开 注释 = "英文名：NotifyScreenInfoChanged" …`（:1183） |
| 5 | `方法 离屏渲染_使视图无效 <公开 注释 = "英文名：Invalidate" …`（:1194，参数 `绘制元素类型`） |
| 6 | `方法 离屏渲染_取帧率 <公开 类型 = 整数 注释 = "英文名：GetWindowlessFrameRate 单位：fps" …`（:1204） |
| 7 | `方法 离屏渲染_置帧率 <公开 注释 = "英文名：SetWindowlessFrameRate" …`（:1213） |
| 8 | `方法 离屏渲染_IME置组成 <公开 注释 = "英文名：ImeSetComposition">`（:1225） |
| 9 | `方法 离屏渲染_IME置交互文本 <公开 注释 = "英文名：ImeCommitText">`（:1252） |
| 10 | `方法 离屏渲染_IME完成组合文本 <公开 注释 = "英文名：ImeFinishComposingText">`（:1267） |
| 11 | `方法 离屏渲染_IME取消组合 <公开 注释 = "英文名：ImeCancelComposition">`（:1278） |
| 12 | `方法 离屏渲染_拖动进入 <公开 注释 = "英文名：DragTargetDragEnter">`（:1287） |
| 13 | `方法 离屏渲染_拖动移动 <公开 注释 = "英文名：DragTargetDragOver">`（:1301） |
| 14 | `方法 离屏渲染_拖动离开 <公开 注释 = "英文名：DragTargetDragLeave">`（:1312） |
| 15 | `方法 离屏渲染_拖动放下 <公开 注释 = "英文名：DragTargetDrop">`（:1321） |
| 16 | `方法 离屏渲染_拖动结束位置 <公开 注释 = "英文名：DragSourceEndedAt">`（:1331） |
| 17 | `方法 离屏渲染_拖动系统结束 <公开 注释 = "英文名：DragSourceSystemDragEnded">`（:1346） |

**证据强度**：**高**（类库注释原文 + `src/main.wsv` 窗口模式创建路径逐行确认）。

**不确定项**：若将来把浏览器改为离屏模式创建，本组会**整体转为运行期可做**；届时 OSR 帧数据如何交给 MCP（现在走窗口截图 `browser_screenshot`）需重新设计，**我未评估**。

---

## 4. C 已被覆盖（含误报消除）

**合计 31 条**（全部来自 §1 的 239 候选集，即**曾被自动扫描判为「零证据」、经人工复核后确证已覆盖**的项）。另在 §6 单独列出「旧报告判为缺口、现在已覆盖」的项（它们已有调用证据，不在候选集内）。

| # | 类库方法（原文摘） | 覆盖它的工具 | 证据 `文件:行号` + 原文 | 强度 |
|---|---|---|---|---|
| **C1** | `类_FBrowser_菜单模式` 的 **8 个**：`添加菜单`(`FBroLib.wsv:3331`)、`添加子菜单`(`:3356`)、`添加分隔栏`(`:3325`)、`添加Check菜单`(`:3339`)、`添加Radio菜单`(`:3347`)、`选中状态`(`:3437`)、`置禁止状态`(`:3424`)、`设置快捷键`(`:3464`) | `browser_context_menu`（注册 `src/MCP_Server.wsv:9998`；分派锚点 `否则 (方法名 == "browser_context_menu")`） | `src/MCP_Server.wsv:8240` `如果 (目标模型.添加分隔栏 ())`<br>`src/MCP_Server.wsv:8248` `子模型 = 目标模型.添加子菜单 (条目命令ID, 条目标签)`<br>`src/MCP_Server.wsv:8261` `如果 (目标模型.添加Check菜单 (条目命令ID, 条目标签))`<br>`src/MCP_Server.wsv:8266` `目标模型.选中状态 (条目命令ID, 真)`<br>`src/MCP_Server.wsv:8278` `如果 (目标模型.添加Radio菜单 (条目命令ID, 条目标签, 单选项群ID))`<br>`src/MCP_Server.wsv:8285` `如果 (目标模型.添加菜单 (条目命令ID, 条目标签))`<br>`src/MCP_Server.wsv:8255/8290` `目标模型.置禁止状态 (条目命令ID, 真)`<br>`src/MCP_Server.wsv:8321` `目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本), 是否Shift, 是否Ctrl, 是否Alt)` | 高 |
| **C2** | `类_FBrowserVIP_控制器` 的 **5 个**：`过滤器_修改内容`(`FBroVip.wsv:1134`)、`过滤器_取消修改内容`(`:1147`)、`过滤器_替换资源_数据`(`:1162`)、`过滤器_替换资源_文件`(`:1174`)、`过滤器_取消替换资源`(`:1186`) | `browser_intercept`（**等价替代通道**，见 C2 注） | 工具描述原文（`src/MCP_Server.wsv:10010`）：「action=modify(流式内容搜索替换…)／replace_data(整体替换为replace_text数据)／replace_file(整体替换为file_path文件内容…)／**unmodify(按url撤销资源替换规则…)／unreplace(同上,但只撤销replace_file类)**／…**注: clear 与 un* 只作用于手写过滤器通道, 不含 VIP 过滤器**」<br>`src/MCP_Server_Core.wsv:2629` `否则 (action == "unmodify")` → `:2633` `unmodify删数 = MCP命令服务器.删除资源替换规则 (url, "")`<br>`src/MCP_Server_Core.wsv:2636` `否则 (action == "unreplace")` → `:2640` `unreplace删数 = MCP命令服务器.删除资源替换规则 (url, "replace_file")`<br>手写过滤器挂钩类库事件：`src/MCP_BrowserEvents.wsv:545` `设置资源过滤器.设置 (篡改过滤器)` | 中高 |
| **C3** | `类_FBrowserVIP_控制器` 的 **2 个**：`过滤器_取消全部修改内容`、`过滤器_取消全部替换资源`（`FBrowserVIP全局功能` 同名包装 `FBroVip.wsv:133`/`:168`） | 内部维护/关闭流程（无独立工具） | `src/MCP_Server.wsv:8837` `vip_ctrl.过滤器_取消全部修改内容 ()`<br>`src/MCP_Server.wsv:8838` `vip_ctrl.过滤器_取消全部替换资源 ()`<br>所在方法头 `src/MCP_Server.wsv:8823` `方法 清理VIP拦截资源 <公开 静态 注释 = "关闭或维护时释放 VIP 过滤器">` | 高 |
| **C4** | `类_FBrowser_Cookie管理器` 的 **5 个**：`取地址Cookie`(`FBroLib.wsv:2927`)、`取全部Cookie`(`:2913`)、`置Cookie`(`:2943`)、`删除Cookie`(`:2951`)、`刷新Cookie`(`:2959`) | `browser_get_cookies` / `browser_set_cookie` / `browser_delete_cookies` / `browser_get_all_cookies` / `browser_refresh_cookies` | `src/MCP_Server_Core.wsv:1089` `FBrowser_Cookie管理器_取全局 ().取地址Cookie (urlFrame.取地址 (), 真, Cookie回调)`<br>`src/MCP_Server_Core.wsv:1262` `FBrowser_Cookie管理器_取全局 ().置Cookie ("http://" + urlDomain, Cookie数据)`<br>`src/MCP_Server_Core.wsv:1273` `FBrowser_Cookie管理器_取全局 ().删除Cookie ("", "")`<br>`src/MCP_Server_Core.wsv:6676` `FBrowser_Cookie管理器_取全局 ().取地址Cookie (caUrl, 真, caCookieCB)`<br>`src/MCP_Server_VIP.wsv:1272` `FBrowser_Cookie管理器_取全局 ().刷新Cookie ()`<br>`src/MCP_Server_VIP.wsv:1282` `FBrowser_Cookie管理器_取全局 ().取全部Cookie (Cookie回调)` | 高 |
| **C5** | `类_FBrowser_填表框架` 的 **17 个**：`置元素内容`(`:5226`)、`取元素内容`(`:5240`)、`置元素内代码`(`:5325`)、`取元素内代码`(`:5339`)、`取元素外代码`(`:5372`)、`置元素属性`(`:5391`)、`取元素属性`、`置元素焦点`、`元素是否存在`、`点击元素`、`滚动到元素`、`触发元素事件`、`取元素坐标`、`取元素选择框`、`置元素选择框`、`取元素选择项`、`置元素选择项` | `browser_fill_*` 族（13 个工具）+ `browser_dom_*` 族 | `src/MCP_Server_Form.wsv:36` `填表框架.置元素内容 (selector, 0, value)`<br>`src/MCP_Server_Form.wsv:475` `ff框架.置元素内容 (ffSel, 0, ffVal)`<br>`src/MCP_Callbacks.wsv:221` `ff.置元素内容 (选择器文本, 0, 操作值)`<br>`src/MCP_Callbacks.wsv:318` `ff.置元素内代码 (选择器文本, 0, 操作值)`<br>`src/MCP_Server_Core.wsv:475` `填表框架.取元素内容 (selector, 0, 文本回调)`<br>`src/MCP_Server_Core.wsv:1767` `填表框架.取元素内容 (selector, 0, 内容回调)` | 高 |
| **C6** | `类_FBrowser_浏览器` 的 **6 个**：`FBrowser_创建浏览器_同步`(`FBroLib.wsv:573`)、`FBrowser_创建后台浏览器_同步`(`:615`)、`尝试关闭浏览器`(`:796`)、`打开对话框`(`:878`)、`发送触摸事件`(`:1017`)、`进程间消息_取渲染进程数量`(`:1137`) | `browser_create`、`browser_close`、`browser_file_dialog`、`browser_touch_press/release/move`、`browser_ipc_renderer_count` | `FBrowser_创建浏览器_同步`/`创建后台浏览器_同步`：类库注释自述「**只能通过：FBrowser_任务运行器_投递任务 的方式创建，发送到UI线程使用**」；项目恰在 UI 线程直接创建 —— `src/main.wsv:228` `FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, , , 浏览器事件, , MCP命令服务器.待创建标识)`、`src/main.wsv:221` `FBrowser_创建后台浏览器 (bgUrl, 浏览器配置, …)` → 同步变体无增量<br>`尝试关闭浏览器`：`src/MCP_Server.wsv:9947` 注册原文 `添加工具JSON ("browser_close_try", "**[已废弃]** 关闭浏览器, 已替换为 browser_close \| ⛔ 该工具恒失败, 请改用 browser_close")` → 能力由 `browser_close` 承担<br>`打开对话框`：`src/MCP_Server_Core.wsv:6104` 方法体原文注释「**安全设计: 传 path 参数直接返回该路径(验证存在性), 不弹任何窗口(不调用原生OS文件对话框, 其会阻塞控制台)**」→ **刻意**程序化替代<br>`发送触摸事件`：`src/MCP_Server_Core.wsv:5572` `vip.高级触摸_按下 (touchX, touchY)`、`:5605` `vip.高级触摸_放开`、`:5638` `vip.高级触摸_移动`（缺省另走 CDP）<br>`进程间消息_取渲染进程数量`：`src/MCP_Server_Core.wsv:6181` `清单 = browser.进程间消息_取渲染进程ID清单 ()` → `:6182` `构建整数值JSON ("count", 清单.取成员数 ())`（**由清单长度导出**，等价） | 高 |
| **C7** | `类_FBrowser_服务器` 的 **3 个**：`发送Http200响应`(`:4740`)、`发送Http404响应`(`:4753`)、`发送Http500响应`(`:4761`) | 项目实际使用 `发送HttpResponse` / `发送原始数据` / `发送WebSocket数据`（同族更通用入口） | 类级+方法扫描：`发送HttpResponse`、`发送原始数据`、`发送WebSocket数据`、`关闭`、`FBrowser_服务器_创建` 在 src 中有调用，而 3 个特化 200/404/500 版本 0 命中 → 属**便利包装**，能力已被通用入口覆盖；服务器创建 `src/MCP_Server.wsv:8566` `FBrowser_服务器_创建 (服务器绑定地址, 服务器端口, 100, 服务器事件)` | 中高 |
| **C8** | `FBrowserVIP全局功能` 的 **7 个**：`FBrowser_VIP过滤器_修改内容`(`FBroVip.wsv:114`)、`_取消修改内容`(`:126`)、`_取消全部修改内容`(`:133`)、`_替换资源_数据`(`:139`)、`_替换资源_文件`(`:150`)、`_取消替换资源`(`:161`)、`_取消全部替换资源`(`:168`) | 同 C2/C3（全局静态包装版 ↔ 控制器方法版） | 同上；静态包装与控制器方法指向同一底层，项目走控制器路径 | 中 |
| **C9** | `类_FBrowserVIP_开发者DOM` 的 **9 个**：`置焦点元素`(`:1503`)、`置节点属性文本`(`:1523`)、`置节点属性值`(`:1531`)、`置节点值`(`:1539`)、`置节点源码`(`:1546`)、`取节点属性`(`:1577`)、`取节点源码`(`:1595`)、`取节点_查询选择器`(`:1612`)、`取全部节点_查询选择器`(`:1630`) | `browser_fill_focus`、`browser_fill_attr_set`、`browser_fill_attr_get`、`browser_dom_set_value`、`browser_dom_set_html`、`browser_dom_get_html`、`browser_dom_query`、`browser_dom_select` | **已接线的同族 4 个可逐行证明该通道是活的**：`src/MCP_Server_VIP.wsv:1445` `vipDom.启用 ("all")`、`:1461` `vipDom.枚举DOM (dDepth, 假, DOM回调)`、`:1485` `vipDom2.取查找文本 (sID, 0, 100, 搜索回调)`、`:1495` `vipDom2.预查找文本 (searchQuery, 假, 预查回调)`。**等价判定基于工具名语义 + 工具描述，未逐个回溯等价工具实现分支** | 中 |
| **C10** | `类_FBrowser_请求环境` 的 **1 个**：`取Cookie管理器`(`FBroLib.wsv:2053`) | `FBrowser_Cookie管理器_取全局 ()`（全局 Cookie 管理器族） | 同 C4（6 处调用点）—— **注：这是「全局」vs「逐请求环境」的语义等价，静态不可判是否在所有场景等价 → 强度中** | 中 |
| **C11** | `类_FBrowser_请求环境` 的 **4 个**：`VIP_高级_安装CRX插件包`、`VIP_高级_卸载插件`、`VIP_高级_取插件地址`、`VIP_高级_取插件路径` | `browser_vip_load_extension` / `browser_vip_unload_extension` / `browser_vip_extension_info` | 方法级证据扫描：这 4 个方法名在 src 中有调用命中（未被列入 239 候选集）；工具注册见 `browser_vip_load_extension` / `browser_vip_unload_extension` / `browser_vip_extension_info`（`src/MCP_Server.wsv`） | 中高 |
| **C12** | `类_FBrowserVIP_控制器` 的 **14 个 UA 设置**：`置UserAgent`、`置Platform`、`置HighPlatform`、`置AcceptLanguage`、`置Architecture`、`置Bitness`、`置Model`、`置Mobile`、`置Wow64`、`置PlatformVersion`、`置FullVersion`、`置Brands`、`置FullVersionList`（`FBroVip.wsv:1722-1948` 段） | `browser_fingerprint_ua` | `src/MCP_Server_VIP.wsv:1582` `ua_data.置UserAgent (…)`；`:1586-1587` `置Platform`/`置HighPlatform`；`:1591` `置AcceptLanguage`；`:1595` `置Architecture`；`:1599` `置Bitness`；`:1603` `置Model`；`:1605` `置Mobile`；`:1606` `置Wow64`；`:1615` `置PlatformVersion`；`:1619` `置FullVersion`；`:1623` `置Brands (MCP命令服务器.解析双文本表 (…))`；`:1627` `置FullVersionList (…)`；`:1629` `vipUA.指纹_虚拟UserAgent (ua_data)` | 高 |
| **C13** | `类_FBrowserVIP_控制器` 的 **12 个输入事件**：`高级鼠标_单击/移动/按下/放开/滚轮滚动`、`高级键盘_单击/按下/放开/输入字符/输入文本` | `browser_vip_mouse_click` / `_move` / `_press` / `_release` / `_wheel`；`browser_vip_key_click` / `_press` / `_release` / `_type` / `_input` | `src/MCP_Server_VIP.wsv:91` `vip_ctrl.高级鼠标_单击 (vx, vy, …)`；`:113` `高级鼠标_移动`；`:802` `高级鼠标_按下`；`:819` `高级鼠标_放开`；`:845` `高级鼠标_滚轮滚动`；`:136` `高级键盘_按下`；`:159` `高级键盘_放开`；`:1096` `高级键盘_单击`；`:1124` `高级键盘_输入字符`；`:1147` `高级键盘_输入文本`；另有 `src/MCP_Server_Core.wsv:860/902/937/942/947/1367` 兜底路径 | 高 |
| **C14** | `类_FBrowserVIP_控制器` 的 **4 个触摸**：`高级触摸_按下`、`高级触摸_放开`、`高级触摸_移动`、`高级触摸_取消` | `browser_touch_press` / `_release` / `_move` / `browser_vip_touch_cancel` | `src/MCP_Server_Core.wsv:5572/5605/5638`；`src/MCP_Server_VIP.wsv:328` `vip_ctrl.高级触摸_取消 (…)` | 高 |
| **C15** | `类_FBrowserVIP_控制器` 的 **2 个**：`高级_执行JS_框架ID`、`指纹_启用触摸事件`、`指纹_取调用计数`（3 条） | `browser_vip_execute_js_context`、`browser_vip_touch_emulation`、`browser_fingerprint {action:"count"}` | `src/MCP_Server_VIP.wsv:1426` `vipCtrl.高级_执行JS_框架ID (jsCode, frmID, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)`<br>`src/MCP_Server_VIP.wsv:1566` `vipTouch.指纹_启用触摸事件 (…, …)`<br>`src/MCP_Server_Core.wsv:2217` `返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))` | 高 |
| **C16** | `类_FBrowser_V8环境` 的 **1 个**：`执行JS代码` | `browser_vip_execute_js_context`（V8 环境内执行） | 方法级扫描命中 | 中 |

### C 组特别注记（防误报纪律）

1. **C2 是「等价替代通道」，不是「类库方法本身被调用」** —— `browser_intercept` 的 `unmodify`/`unreplace` 明确「**只作用于手写过滤器通道, 不含 VIP 过滤器**」（`src/MCP_Server.wsv:10010` 描述原文）。因此严格说：**类库 VIP 过滤器方法仍未接线，但同一个用户能力（按 URL 撤销资源替换）已可达**。若将来要求「必须走 VIP 原生过滤器」，C2 需回退为 A。
2. **C6 的 `进程间消息_取渲染进程数量` 是「派生等价」** —— 工具返回的是 `取渲染进程ID清单().取成员数()`，不是类库的专用计数方法。功能等价，但若清单与计数在 CEF 侧可能不一致，则不等价；**我未实测**。
3. **C6 的 `打开对话框` 是「刻意移除」而非「覆盖」** —— 项目为控制台安全**故意不弹 OS 对话框**。这对 MCP 场景是正确的（弹窗会阻塞），但「打开真正的文件选择对话框」这一能力**确实不在 MCP 面上**。按任务口径归 C（已有明确对应的替代工具 + 明确理由），但**这属于设计取舍，不是误报消除**。
4. **C7 的「便利包装」判定基于「特化版本 0 命中 + 通用版本有调用」**，我**未逐行比对** `发送HttpResponse` 与 `发送Http200响应` 的行为差异，故强度标中高而非高。
5. **C9/C10/C11 的等价判定基于工具名语义 + 工具描述**，**未逐个回溯等价工具的实现分支**，强度中。若需绝对可靠，应逐个 grep 到实现分支。

---

## 5. D 非能力项 / 基础设施（**不计入缺口**）—— 63 条（239 候选集内）

列出以保证口径可核对（避免把「缺基础设施」误报成「缺能力」）。

| 类 | 条数 | 说明与依据 |
|---|---:|---|
| `类_FBrowserVIP_UA数据` 的 13 个 `取*` | 13 | `取UserAgent`/`取AcceptLanguage`/`取Platform`/`取HighPlatform`/`取Brands`/`取FullVersionList`/`取FullVersion`/`取PlatformVersion`/`取Architecture`/`取Model`/`取Mobile`/`取Bitness`/`取Wow64`/`取FormFactors`（`FBroVip.wsv:1832-1937`）—— **都是「写进去再读回来」的自反访问器**：设置侧已由 `browser_fingerprint_ua` 覆盖（见 C12），MCP 侧再暴露 getter 无用户价值（AI 自己刚设过）。<br>⚠ 其中 `置FormFactors`（`:1825`）**是写方法，属真缺口**，已计入 A4 旁注（低价值）：A 组未单列它是因为 `browser_fingerprint_ua` 的 schema 里没有 form_factors 字段，补一个字段即可。 |
| `类_FBrowser_任务运行器` | 9 | 类名在 src 引用数 = **0**。`FBrowser_任务运行器_取当前`/`取指定线程`/`投递任务`/`投递任务_延迟`/`是否指定线程上调用`、`是否为当前线程`/`是否为指定线程`/`投递任务`/`投递延时任务`（`FBroLib.wsv:2771-2865`）—— 线程任务调度基础设施。 |
| `类_FBrowser_V8环境` 的 9 个 | 9 | `FBrowser_V8_注册JS扩展`/`FBrowser_V8环境_取当前环境`/`_取运行环境`/`是否当前环境`/`取任务处理器`/`取浏览器`/`取框架`/`取全局V8值`/`进入`（`FBroLib.wsv:3822-3889`）—— V8 嵌入层内部句柄。项目逆向走 CDP（`browser_reverse_*` 族 90+ 工具），不使用 V8 嵌入。 |
| `类_FBrowserVIP_WebSocket客户端` | 7 | `连接`/`销毁`/`取协议`/`取插件`/`取数据类型`/`发送文本`/`发送数据`（`FBroVip.wsv:1397-1456`）—— 该类是**渲染进程内 WebSocket 客户端事件**的宿主侧句柄（对应 `渲染_VIP_WebSocket客户端_*` 事件）；项目用 `browser_vip_websocket_intercept`（拦截）与 CDP 覆盖，不构造客户端。 |
| `FBrowser类辅助` | 5 | 类名引用数 = **0**。`FBrowser创建类指针`/`取执行类`/`释放类`/`释放当前类`/`设置类`（`FBroLib.wsv:339-366`）—— C++ 类指针封送工具，**给封装者用，不是用户 API**。 |
| `类_FBrowser_服务器事件` 外的服务器基础设施 | — | 见上；`类_FBrowser_任务运行器` 同族。 |
| `类_FBrowser_事件智能指针` | 4 | `FBrowser创建事件智能指针`/`引用`/`取指针`/`取事件数据类型`（`FBroLib.wsv:281-319`）—— 回调对象生命周期管理。项目用 `创建 (类_MCP_XXX回调)` 路径（如 `src/MCP_Server_Core.wsv:1281` `清理缓存回调.创建 (类_MCP_清理缓存回调)`），不需要全局工厂。 |
| `类_FBrowser_值转换` | 3 | 类名引用数 = **0**。`FBrowser_数据到字节集`/`FBrowser_字节集到字节集`/`FBrowser_文本到字节集`（`FBroValue.wsv:7/14/24`）—— 类型转换工具，项目有自建 `取空文本数组`/`文本到字节集` 等（`src/MCP_Server_Core.wsv` 多处）。 |
| `类_FBrowser_基础框架` | 3 | 类名引用数 = **0**。`取浏览器`/`取填表框架`/`取框架`（`FBroLib.wsv:1555-1566`）—— 框架类之间的向上/向下转型访问器。 |
| `类_FBrowserVIP_控制器` 的 2 个 | 2 | `指纹_虚拟内核功能`（`FBroVip.wsv:508`，**类库自注「弃用」**）、`逐字分割`（`:1006`，字符串工具）。 |
| `FBrowserVIP全局功能` 的 1 个 | 1 | `FBrowser_VIP功能_启用插件高级功能`（`FBroVip.wsv:109`）—— 插件高级功能开关；插件族本身已由 `browser_vip_load_extension` 覆盖（C11），该开关的**独立价值不确定**（**标 `不确定`**）。 |
| `类_FBrowser_请求环境` 的 4 个 | 4 | `FBrowser_请求环境_取全局`/`是否为全局`/`创建_其他`/`是否为分享`（`FBroLib.wsv:1994/2010/2023/2037`）—— 环境句柄管理；A9 已把 `VIP_高级_载入插件路径`/`取插件名` 单列为缺口。 |
| `FBrowser辅助功能` 的 2 个 | 2 | `FBrowser_启用异常收集`（**类库自注「没用」**）、`异常收集回调模板函数`（**无 `<公开>`**）。 |
| *（其余为「有调用证据但非能力」的名）* | — | 如 `类_FBrowser_浏览器事件`/`类_FBrowser_应用事件` 等事件声明（已由 src override 解释）、各数据包装类的 `是否为空`/`置空`/`取大小` 等。 |

> 注：D 组共 63 条来自 239 候选集内部统计；239 之外另有约 273 个「有调用证据」的方法名与大量事件名，未逐条列出。

---

## 6. 旧报告的过时结论（逐条）

> 旧报告：`_classlib_gap.md`（基线 301/533）· `_classlib_gap_confirmed.md`（31 缺口/152 覆盖/27 不适用）· `_classlib_gap_confirmed2.md`（46 缺口/313 误报/4 存疑）· `_classlib_gap_recheck.md`（P0–P3）· `_classlib_gap_verify_r98.md`（r98，基线 **313** 工具）· `_gap_recheck.md`（5 项复核）· `_vip_gap_analysis.md` + `_vip_app_gap_round98.md`。
> 所有「现在实际是 Y」的行号均为**本轮实测快照**（`src` 哈希见 §0.1）。

| # | 旧报告说 | 现在实际是 | 依据 `file:line` |
|---|---|---|---|
| **O1** | 工具总数 **313**（`_classlib_gap_verify_r98.md:48`「已注册工具总数 **313**」；更早报告用 301） | **314** | `src/MCP_Server.wsv` 中 `添加工具JSON ("` 计数 = **314**（唯一名 314，无重名），在 `06:49:33`/`06:49:53`/`06:52`/`06:54:38` 四次独立计数一致；该文件在分析期间被反复写入（长度 664,727 ↔ 665,232；哈希 `301348459A564D30` ← `C7B1C16079B4E7FF`），但**注册条数未变** |
| **O2** | `_gap_recheck.md:27/64` 判 **`显示隐藏窗口` = REAL GAP**（「类库 `FBroLib.wsv:1071-1076` … 而 `browser_set_window_style(type=-16)` 只能提供**不可靠**替代」） | **已覆盖**。新工具 `browser_show_window` 直调类库方法 + 回读 `WS_VISIBLE` 位验证 | 注册 `src/MCP_Server.wsv:9982` `添加工具JSON ("browser_show_window", "显示/隐藏浏览器窗口。**已实现**: 经类库 显示隐藏窗口 调用宿主 ShowWindows(不需 HWND), 并用 GWL_STYLE 的 WS_VISIBLE 位**回读验证**; 位没变成请求的状态就如实报 verified=false, 不谎报成功。…")`<br>调用 `src/MCP_Server_Core.wsv:6029` `swBrowser.显示隐藏窗口 (sw目标)`<br>回读 `src/MCP_Server_Core.wsv:6028` `sw前 = swBrowser.取窗口属性 (MCP_常量.窗口样式_GWL_STYLE)` / `:6032` `sw后 = …` |
| **O3** | `_gap_recheck.md:62/64` 判 **`移动窗口` = 真缺口**（「类库侧 `移动窗口` … 在 src 中 0 调用，是被主动禁用的」） | **已覆盖**。新工具 `browser_move_window` 直调类库方法 + CDP `Browser.getWindowForTarget` 回读 bounds 验证 | 注册 `src/MCP_Server.wsv:9983` `添加工具JSON ("browser_move_window", "移动/缩放浏览器窗口。**已实现**: 经类库 移动窗口 -> 宿主 MoveWindow(不需 HWND), 并用 CDP Browser.getWindowForTarget 回读 bounds 验证, 回读不符则如实报 verified=false。…")`<br>调用 `src/MCP_Server_Core.wsv:5738` `mwBrowser.移动窗口 (mwX, mwY, mwW, mwH, mwRepaint)` |
| **O4** | `_gap_recheck.md:72`「**`置自动调整大小` 对应的类库方法全项目 0 调用** … 工具是**恒失败桩**」 | **已覆盖（不再是恒失败桩）**。`browser_set_auto_resize` 现在真的调用类库方法 | 注册 `src/MCP_Server.wsv:9979` `添加工具JSON ("browser_set_auto_resize", "启用/关闭窗口自动调整大小(CEF SetAutoResizeEnabled)。**已实现**: 经类库 置自动调整大小 调用宿主 SetAutoResizeEnabled(不需 HWND)。类库无返回值、且该类设置没有可回读的查询接口, 故只报 verified=false 而不谎报生效。…")`<br>调用 `src/MCP_Server_Core.wsv:6083` `arBrowser.置自动调整大小 (ar启用, ar最小高, ar最小宽, ar最大高, ar最大宽)` |
| **O5** | `_classlib_gap_verify_r98.md:202-218/303/§7` 判 **`类_FBrowser_菜单模式` 13 条全是真缺口**，建议新工具 `browser_context_menu`（Top 1）；r98 §5 第 2 条还担心「该事件是否真的会被 CEF 触发，若否 A 组整体降级」 | **该工具已存在，13 条中 8 条已接线**（`添加菜单`/`添加子菜单`/`添加分隔栏`/`添加Check菜单`/`添加Radio菜单`/`选中状态`/`置禁止状态`/`设置快捷键`）；另发现该类实际有 **36** 个方法（r98 自己也发现「候选只列了 13，类里其实有 34 个 0 命中方法」），**剩 26 条未接线**（见 A2） | 注册 `src/MCP_Server.wsv:9998` `添加工具JSON ("browser_context_menu", …)`（action=schema `set/get/clear`，规格逐行 `类型|标签|命令ID|参数|父命令ID|快捷键`，类型 `item/check/radio/sep/sub`）<br>调用 `src/MCP_Server.wsv:8240/8248/8255/8261/8266/8278/8285/8290/8321`<br>通道 `src/MCP_BrowserEvents.wsv:2662` 形参 `菜单模式`，且 `:2666-2676` 已加 `如果 (MCP命令服务器.菜单已启用) { MCP命令服务器.应用菜单规格 (菜单模式) }`（r98 时该处只有 `记录监控事件`）<br>r98 §5-2 的担心**已被实现方自行解决**（每次右键重施规格，注释明写「`菜单模式` 只在本次回调内有效…故必须每次重施」） |
| **O6** | `_vip_app_gap_round98.md:288/297` 判 **T2 `过滤器_取消修改内容`（`FBroVip.wsv:1147`）/ T3 `过滤器_取消替换资源`（`:1186`）= 候选真缺口**；`§5 相关说明 B`「`browser_intercept action=clear` 与 VIP 过滤器是两套互不干涉的状态」 | **能力已可达（等价通道）**：`browser_intercept` 新增 `unmodify` / `unreplace` 两个 action，按 URL 撤销资源替换规则；`action=clear` 另有「取消全部」路径。**但注意**：工具描述明确「**clear 与 un* 只作用于手写过滤器通道, 不含 VIP 过滤器**」→ 类库 VIP 方法本身**仍未接线**，判定为「等价覆盖」而非「误报」 | 描述 `src/MCP_Server.wsv:10010`（新增 `unmodify(按url撤销资源替换规则,返回实际删除条数;撤销不存在按幂等成功)/unreplace(同上,但只撤销replace_file类)`）<br>分派 `src/MCP_Server_Core.wsv:2629` `否则 (action == "unmodify")` / `:2636` `否则 (action == "unreplace")` / `:2633` `删除资源替换规则 (url, "")` / `:2640` `删除资源替换规则 (url, "replace_file")`<br>「取消全部」`src/MCP_Server.wsv:8837/8838`<br>r98「相关说明 B」的判断**依然成立**（两套状态确实互不干涉），但**能力面上已不缺** |
| **O7** | `_classlib_gap_verify_r98.md:229/305` 判 **`FBrowser_浏览器_通过序号取浏览器`（`FBroLib.wsv:487`）仍是缺口**（建议 `browser_select {index}` / `browser_list` 加 `index`，列为 Top 3） | **仍然未接线 —— 此结论未过时**（我复核确认 0 命中） | 全项目非注释命中：`通过序号取浏览器` = **0**；类级扫描 `FBrowser辅助功能` 方法名 `FBrowser_浏览器_通过序号取浏览器` 0 命中。仍列 A3-1 |
| **O8** | `_classlib_gap_verify_r98.md:230/306` 判 **`FBrowser_Parser_取数据URI`（`FBroLib.wsv:394`）是缺口**（Top 4） | **仍然未接线 —— 未过时** | `取数据URI` / `data_uri` 全项目 **0 命中**；当前 `browser_base64_encode`/`_decode` 只做裸 Base64（`src/MCP_Server_Core.wsv:5497` `result = FBrowser_Parser_Base64编码 (data)`） |
| **O9** | `_classlib_gap_verify_r98.md:231-232/307-309` 判 **`写入JSON` / `字节值解析为JSON` 是缺口**（低/极低） | **仍然未接线 —— 未过时** | `写入JSON`/`字节值解析为JSON` 0 命中 |
| **O10** | `_classlib_gap_verify_r98.md:236-255`（C 组）判 **`类_FBrowser_命令行` 15 条中 14 条「仅启动期生效」真缺口** | **仍然成立，且范围更大**：该类实际有 **31** 个方法（r98 只看 15 条候选），我清点后 **28 个为 0 命中**（见 B1） | 类级扫描：`类_FBrowser_命令行` 在 src 仅 2 处、全部是形参（`src/main.wsv:477`）；`FBrowser_初始化` 在 `src/main.wsv:98` 之后无法补救 |
| **O11** | `_classlib_gap_recheck.md:3`（上一版）判 `通过用户标识取浏览器` 是低价值缺口；`_classlib_gap_verify_r98.md:80` 已把它列为「本轮新增消除的 8 条误报」之一 | **确认已覆盖**（与 r98 一致，旧结论已自纠） | `src/MCP_Server_Core.wsv:5862` `found = FBrowser_浏览器_通过用户标识取浏览器 (tag)`（供 `browser_find_by_tag`） |
| **O12** | `_classlib_gap.md:63`（最旧）把 `停止载入`/`清理缓存`/`重新载入`/`开始下载`/`设置代理`/`显示隐藏窗口`/`移动窗口`/`可否前进` 等列为候选缺口 | **前 7 项全部已覆盖**（`可否前进` 亦已接线）；旧清单的 363 条候选**绝大部分是误报** | `src/MCP_Server_Core.wsv:279` `browser.停止载入 ()`（`browser_stop`）<br>`src/MCP_Server_Core.wsv:6407` `browser.清理缓存 (ccOrigin, ccMask, ccTypeMask, 清理回调2)`（`browser_clear_cache`，掩码族 `取清理对象掩码` 在 `:19`，值 `清理缓存.全部` 在 `:6343`）<br>`src/MCP_Server_Core.wsv:255` `browser.重新载入_忽略缓存 ()`；`src/MCP_Server_Core.wsv:234-240` 区段 `browser.重新载入 ()`（`browser_reload`）<br>`src/MCP_Server_Core.wsv:1478` `browser.开始下载 (url)`（`browser_start_download`）<br>`src/MCP_Server_Core.wsv:1420` `browser.设置代理 (address, username, password)`；`:1453` `browser.清空代理 ()`<br>`src/MCP_Server_Core.wsv:1283` `FBrowser_清理全局缓存 (, , , 清理缓存回调)` |
| **O13** | `_gap_recheck.md:2/73` 认为 `FBrowser_Parser_取数据URI` 已被旧报告以「mimetype 前缀由调用方拼接」视为覆盖，**应改标「部分覆盖」**；并称 `browser_base64_encode` 只做裸 Base64 | **该判断成立且更有力**：`取数据URI` 现在确证 0 命中，应直接列为**真缺口**（低价值），而非「部分覆盖」 | 同 O8 |
| **O14** | `_gap_recheck.md:71`「**`window_topmost` / `window_width` / `window_height` 三个配置项是死配置**」 | **仍未过时 —— 复核确认依旧只有「定义 + 赋值」、无读取点** | `src/MCP_Server.wsv:282` `变量 窗口置顶 <公开 静态 类型 = 逻辑型 值 = 真 注释 = "窗口是否置顶, 由 mcp_config.json window_topmost 控制">`；`:650` `窗口置顶 = 配置解析.取逻辑值 ("window_topmost")`<br>`src/MCP_Server.wsv:283` `变量 窗口默认宽度 <公开 静态 类型 = 整数 值 = 1000 …`；`:657` `窗口默认宽度 = 配置窗口宽`<br>全 src 无第三处引用（`browser_move_window` / `browser_show_window` 的实现**也没有**读它们） |
| **O15** | `_gap_recheck.md:63`「`browser_restore_gui` 并不恢复任何『布局』…工具描述名不符实」 | **描述仍是原文，未修正** | 注册 `src/MCP_Server.wsv:9980` `添加工具JSON ("browser_restore_gui", "恢复嵌入式GUI布局与欢迎页")`（与 `_gap_recheck.md` 引用的一致）；实现锚点 `否则 (方法名 == "browser_restore_gui")` 在 `src/MCP_Server_Core.wsv:6097` |
| **O16** | `_gap_recheck.md:74`「`browser_uri_encode` 的 `use_plus` 被硬编码为 `假`；`browser_uri_decode` 的 `convert_to_utf8`/`unescape_rule` 硬编码为 `真,真`」 | **仍未过时（硬编码依旧）**，属**参数面收窄**而非能力缺失 | `src/MCP_Server_Core.wsv:5528` `result = FBrowser_Parser_URI编码 (data, 假)`（第二参硬编码 `假`）<br>`src/MCP_Server_Core.wsv:5540` `result = FBrowser_Parser_URI解码 (data, 真, 真)`<br>（另 `src/MCP_Server.wsv:8372/11208/11314` 也各自硬编码 `真, 真`） |
| **O17** | `_classlib_gap_confirmed.md:26`（31 项真缺口）与 `_classlib_gap_confirmed2.md:72`（46 条）的**高价值**条目：`高级_创建标签浏览器`（confirmed2 §C 存疑 / vip_round98 T5）、`高级_执行JS_全部框架`（vip_round98 T4）、`过滤器_取消修改内容`（T2）、`过滤器_取消替换资源`（T3） | **状态分化**：T2/T3 已由 `browser_intercept unmodify/unreplace` 能力覆盖（O6）；`高级_执行JS_全部框架`、`高级_创建标签浏览器` **仍未接线** —— **未过时**，仍在我的 A4 清单（A4-3、A4-10） | `高级_执行JS_全部框架` 0 命中；`高级_创建标签浏览器` 0 命中；`src/MCP_Server_VIP.wsv:1426` 只接 `高级_执行JS_框架ID` |
| **O18** | `_vip_gap_analysis.md:264-298`（4.1–4.4）把 **`置Brands` / `置FullVersionList` / `置PlatformVersion` / `置FullVersion`** 列为 VIP **REAL GAP 排名前 4**（含 UA-CH brands/fullVersionList） | **全部已覆盖** → 已由 `browser_fingerprint_ua` 接线。**这是旧报告最大的一处过时**（`_audit/add_uach_fields.py` 的存在也印证其间补齐过） | `src/MCP_Server_VIP.wsv:1623` `ua_data.置Brands (MCP命令服务器.解析双文本表 (MCP命令服务器.yyjson取文本 (参数JSON, "brands")))`<br>`:1627` `ua_data.置FullVersionList (…)`<br>`:1615` `ua_data.置PlatformVersion (…)`<br>`:1619` `ua_data.置FullVersion` (…)`<br>字段名 `brands` / `full_version_list` / `platform_version` / `full_version` 全部在 schema 中 |
| **O19** | `_vip_app_gap_round98.md:269` 判 **T1 `高级_设置触发鼠标触摸事件`（`FBroVip.wsv:623`）= 候选真缺口**（最高优先） | **仍未接线 —— 未过时**（我复核确认 0 命中）。注意 `browser_vip_touch_emulation` **走的是另一个方法** `指纹_启用触摸事件`，**不能算覆盖** | `高级_设置触发鼠标触摸事件` 0 命中；`src/MCP_Server_VIP.wsv:1566` `vipTouch.指纹_启用触摸事件 (…, …)`（对照） |
| **O20** | `_classlib_gap_confirmed.md:202`「**不适用 / 平台限制（27 项）**」把一批项归为平台限制 | **部分需重新归类**：其中 `类_FBrowser_浏览器` 的 17 条离屏渲染（OSR）族我改判为 **B3「运行期不可达（需离屏模式）」**并给出**逐条类库注释依据**（「This method is only used when window rendering is disabled」），比旧报告的「平台限制」更精确、可复核 | `FBroLib.wsv:1166/1174/1183/1194/1213…` 注释原文；对照 `src/main.wsv:203-209`（窗口模式创建） |
| **O21** | `_classlib_gap_verify_r98.md:266`（§5-2）「**我无法确定**：`浏览器_即将打开菜单` 事件在本项目实际是否会被 CEF 触发。**这决定了 A 组 13 条是否真的『运行期可做』**」 | **该不确定性已被实现方解决（不再是阻塞项）**：`browser_context_menu` 已按「每次右键重施规格」落地，且实现了 `set/get/clear` 与 `菜单上次施加条数/菜单施加次数/菜单上次施加时刻` 等**回读状态字段**（说明实现方已按「事件会触发」设计）。<br>⚠ **但这是实现方的设计选择，不等于已实测** —— 我**未**验证事件是否真被 CEF 触发 | `src/MCP_Server.wsv:8325` `菜单最近施加条数 = 施加条数` / `:8326` `菜单施加次数 = 菜单施加次数 + 1` / `:8327` `菜单上次施加时刻 = 到文本 (取启动时间 ())` |
| **O22** | `_classlib_gap_verify_r98.md:271`（§5-7）「`src/MCP_Server_Core.wsv` 的行号稳定性（重要）…**我不保证交付后行号仍与 §0 快照一致**」 | **该风险已实际发生且仍在持续**：本轮分析期间 `MCP_Server.wsv` 664,727 → 665,232 B、`MCP_Server_Core.wsv` 508,654 → 510,267 B，同一调用点行号 `8826 → 8837` | §0.1 快照表（各文件长度/mtime/SHA-256 前 16 位） |
| **O23** | `_classlib_gap_confirmed2.md:890-960`「四族单独结论」：命令行族「真缺口，但必须做成启动通道」（**仍成立**）；菜单模式「13 条全是真缺口，都是 P2」（**部分过时**，8 条已接线 → O5）；VIP 控制器「误报 100 条、真缺口 1 条、存疑 1 条」（**过时**：按当前源码 VIP 控制器仍有 **11 条**真缺口 + 5 条等价覆盖 + 2 条非能力，见 A4）；应用事件「误报 27 条，无缺口」（**仍成立**） | 见左 | 菜单：O5；VIP：A4 全表；应用事件：类级扫描 `类_FBrowser_应用事件` 的 32 个方法中，除 `类_初始化`/`类_清理`（`FBroEventControl.wsv:7/13`）外**全部有 src override 声明**（`src/main.wsv:272` 注册事件类） |
| **O24** | `_classlib_gap_verify_r98.md:48` 的计数口径「`添加工具JSON ("` 在 **`src/MCP_Server.wsv` + `src/MCP_Kernel.wsv` + `src/MCP_Server_Core.wsv`** 计数 = 313」 | **计数口径可简化且已是 314**：当前 **全部 314 条注册都在 `src/MCP_Server.wsv` 单文件内**（`MCP_Kernel.wsv` / `MCP_Server_Core.wsv` 中 `添加工具JSON (` 计数为 0） | `src/MCP_Server.wsv` 计数 314；`src/MCP_Kernel.wsv` / `src/MCP_Server_Core.wsv` 中 `添加工具JSON ("` 计数 **0** |

**过时结论合计：24 条**（其中 **8 条**为「旧判缺口→现已覆盖」：O2 O3 O4 O5 O6 O18 O21 O23-菜单；**6 条**为「旧结论经复核仍成立、不算过时」但必须点明（O7 O8 O9 O14 O16 O19）；其余为口径/基线/风险类更新）。

---

## 7. 统计汇总

| 组 | 条数 | 含义 |
|---|---:|---|
| **A 真缺口（运行期可做）** | **92** | 90 条来自 239 候选集 + 2 条类级阅读补入（见 A1 表头） |
| **B 仅启动期生效 / 运行期不可达** | **55** | B1 命令行 28 + B2 初始化前 10 + B3 离屏模式专属 17 |
| **C 已被覆盖（含误报消除）** | **31** | 全部来自 239 候选集；另 §6 单列 8 条「旧判缺口→现已覆盖」 |
| **D 非能力项 / 基础设施（不计缺口）** | **63** | 来自 239 候选集 |
| **239 候选集合计校验** | 90+55+31+63 = **239** ✅ | A 组表内 92 条 = 候选集中的 **90** 条 + 类级阅读补入的 **2** 条（`类_FBrowser_菜单环境::取类型` / `取地址`，因名称碰撞未被自动列入候选） |

| 基准量 | 值 |
|---|---:|
| 当前工具总数 | **314** |
| 类库文件 | 8 |
| 类库 `类` 声明 | 188 |
| 类库 `方法` 声明 | 1360 |
| 类库去重方法名 | 978 |
| 有调用/覆盖证据的方法名 | 328 |
| 零证据方法名（扣 override 后） | 512 |
| 能力候选（扣基础设施类后） | 239 |
| 旧报告过时结论 | **24** |

---

## 8. 依据方法与可复现检索式（全部只读）

| 目的 | 检索式 | 结果 |
|---|---|---|
| 工具总数 | `Select-String -Path src\MCP_Server.wsv -Pattern '添加工具JSON\s*\(\s*"'` | **314**（唯一 314） |
| 类库方法抽取 | 8 文件 `^\s*方法\s+` + `^类\s+` 上下文归并 | 1360 声明 / 978 名 / 188 类 / 100 个含方法的类 |
| 成员调用证据 | `(?:[\w\u4e00-\u9fff]|\s*\)|\s*\])\.(方法名)\s*\(`（1360 名做 alternation，一次遍历） | 328 名有证据 |
| 全局静态调用证据 | `(?<![\w\u4e00-\u9fff.])(方法名)\s*\(`（长度 ≥3 的名） | 追加命中（如 `FBrowser_Parser_Base64编码`、`FBrowser_服务器_创建`） |
| 事件接线证据 | `^\s*方法\s+(方法名)\s` | 解释 138 个原本「零证据」的名（事件类为主） |
| 零证据判定 | 三路取并集后取补 | 512 → 扣基础设施类 → **239** |
| 类级可达性 | 逐类 `类名` 在活动 src 非注释行计数 | 70 类引用数 = 0；`类_FBrowser_菜单环境` = 3（**全是形参**） |
| 过滤注释噪声 | 跳过 `^\s*//` 与 `^\s*#` 行 | 全流程生效（**关键**：`显示隐藏窗口`/`移动窗口`/`置自动调整大小` 的类库方法名在 src 里**只出现在注释里**，若不跳过必然把它误判为「已覆盖」） |
| 备份文件处理 | `*.~vbak.wsv` 全程**排除**在证据源之外（`main_1`/`MCP_Server_1`/`MCP_Server_2`/`MCP_Kernel_1`/`MCP_Kernel_2`/`MCP_BrowserEvents_1`） | 证据一律取自**活动文件** |
| `@输出名` 处理 | **未**作为存活/引用依据（按任务要求） | — |

### 本轮方法论上踩过/避开的三个坑（留档给后续审计）

1. **注释污染（最危险）**：`显示隐藏窗口`、`移动窗口`、`置自动调整大小`、`指纹_虚拟Viewport`、`置Brands`、`清理缓存` 等类库方法名在 src 中**大量出现在注释与工具描述字符串里**（例如 `src/MCP_Server_Core.wsv:6013` `// ★ 补能力(能力面反查确认的真缺口): 类库 显示隐藏窗口(显示隐藏) -> FBroHsBrowserHost_ShowWindows。`）。若不做「跳过注释行」过滤，会得出「已覆盖」的**反向误报**。
2. **链式调用漏检**：`FBrowser_Cookie管理器_取全局 ().取地址Cookie (...)` 中 receiver 以 `()` 结尾，`[\w]+\.` 式正则**漏检**，会把 5 个 Cookie 方法全部误判为「零证据」。修正为允许 `)`/`]` 结尾后即命中。
3. **泛用短名碰撞**：`取类型`/`取地址`/`取数量`/`设置`/`创建`/`是否为空`/`置空` 等在 src 中必然有大量**其它类**的同名命中，属**假「已覆盖」**。本轮对这类名一律**不采信名称命中**，改按「类级可达性 + 类库原文语义」重判（`类_FBrowser_菜单环境` 的 19 条即由此从「疑似覆盖」翻回「真缺口」）。

---

## 9. 局限性与未做的事（如实声明）

1. **本报告全部结论均为静态阅读所得。未编译、未运行、未调用任何 MCP 工具、未发起任何 HTTP 请求、未启动/重启/结束任何进程。** 凡涉及运行期行为的判断（访问器是否真能取到值、菜单事件是否真被 CEF 触发、清 `WS_VISIBLE` 位是否真隐藏窗口、`URI解码(真,真)` 对 `+` 的处理）**均未验证**。
2. **行号会漂移**：`src/MCP_Server.wsv` / `MCP_Server_Core.wsv` 在分析期间被并发写入（§0.1）。所有引用均附**稳定锚点原文**，请以锚点 grep 定位。
3. **C 组 5 处等价判定未回溯实现分支**（C7 C9 C10 C11 及 C2 的通道语义），强度已逐条标为「中/中高」。若需绝对可靠，应逐个 grep 到等价工具的实现分支。
4. **A6-1「`browser_get_run_style` 未调用 `取窗口运行风格`」已逐行读取确认**（`src/MCP_Server_System.wsv:95-110`）；但**该工具名与类库方法同名同义却绕开实现，是否为有意为之**（例如 `窗口运行风格` 枚举在窗口模式下无意义），我**无法判断** → 标 `不确定`。
5. **未审阅旧脚本 `_audit/classlib_gap.py` / `cg2_*.py` 的口径**，故不排除旧候选清单本身存在漏列（r98 §5-8 已提出同一疑虑，本轮我改为**从 8 个类库文件全量重抽**，不依赖旧候选清单，因此该风险已消除）。
6. **未评估改动成本与风险**：本报告只回答「类库有、MCP 未暴露」，**不评价**新增工具对现有 `browser_id` 公共参数族、`browser_collect` 事件同步名单、工具描述长度与 AI 可读性的影响。
7. **`类_FBrowser_服务器::是否有效连接` 的封装漏参**（`FBroLib.wsv:4737` 未传 `@<连接ID>`）为逐行阅读所见，**未实测**，也未查是否有意为之。
