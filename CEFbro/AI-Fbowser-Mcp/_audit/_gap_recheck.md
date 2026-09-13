# 5 项「候选缺口」独立复核（只读静态复核）

复核范围：仅任务书指定的 5 项。方法一律为**读实现**，不采信「工具名存在」即达标的推断。
未运行任何程序、未调用任何 MCP 工具、未修改任何源文件。

判定口径：
- **ALREADY COVERED** = 存在一个已注册工具，其**实现分支真的调用了目标类库方法**，且能指出选中该能力的**确切参数**。
- **REAL GAP** = 全项目无任何工具分支调用目标类库方法；或只有「改同一个底层窗口属性」这类不等价替代。

---

## 结论表

| 声称的缺口 | 判定 | 覆盖工具 + 参数 | 证据（file:line + 引文） | 置信度 |
|---|---|---|---|---|
| **1a.** `Base64编解码` → `FBrowser_Parser_Base64编码` | **ALREADY COVERED** | `browser_base64_encode`，参数 `data` (text) | 注册 `src/MCP_Server.wsv:9625` `添加工具JSON ("browser_base64_encode", "Base64编码", 单参数Schema文本 ("data", "text", "数据"))`；实现 `src/MCP_Server_Core.wsv:5128` `否则 (方法名 == "browser_base64_encode")` → `:5137` `result = FBrowser_Parser_Base64编码 (data)` | 高 |
| **1b.** `Base64编解码` → `FBrowser_Parser_Base64解码` | **ALREADY COVERED** | `browser_base64_decode`，参数 `data` (text) | `src/MCP_Server.wsv:9626`；实现 `src/MCP_Server_Core.wsv:5140` `否则 (方法名 == "browser_base64_decode")` → `:5149` `字节结果 = FBrowser_Parser_Base64解码 (data)`，经 `:5153` `字节结果.取文本 ()` 返回文本 | 高 |
| **1c.** `URI编解码` → `FBrowser_Parser_URI编码` | **ALREADY COVERED**（有一处硬编码取舍，见注A） | `browser_uri_encode`，参数 `data` (text) | `src/MCP_Server.wsv:9627`；实现 `src/MCP_Server_Core.wsv:5159` → `:5168` `result = FBrowser_Parser_URI编码 (data, 假)` | 高 |
| **1d.** `URI编解码` → `FBrowser_Parser_URI解码` | **ALREADY COVERED** | `browser_uri_decode`，参数 `data` (text) | `src/MCP_Server.wsv:9628`；实现 `src/MCP_Server_Core.wsv:5171` → `:5180` `result = FBrowser_Parser_URI解码 (data, 真, 真)`（convert_to_utf8=真, unescape_rule=真） | 高 |
| **2a.** `FBrowser_浏览器_取ID清单` | **ALREADY COVERED** | `browser_list`（无参数） | `src/MCP_Server_Core.wsv:614` `否则 (方法名 == "browser_list")` → `:618` `ID清单 = FBrowser_浏览器_取ID清单 ()` → `:626-632` 逐项 `ID清单.取整数值 (取循环索引 ())` + `FBrowser_浏览器_通过ID取浏览器 (bid)` → `:657-659` 输出 `{"id":..,"url":..}`；`:664` 以 `"browsers"` 数组返回 | 高 |
| **2b.** `FBrowser_浏览器_取数量` | **ALREADY COVERED**（3 个工具均可） | `browser_meta` → `browser_count`；`mcp_status` → `browser_count`；`ping` → `browsers`（均无参数） | `src/MCP_Server_Core.wsv:3748` `元数据对象.加入整数成员 ("browser_count", FBrowser_浏览器_取数量 ())`；`:4355` `状态对象.加入整数成员 ("browser_count", FBrowser_浏览器_取数量 ())`；`src/MCP_Server_System.wsv:116` `ping结果.加入整数成员 ("browsers", FBrowser_浏览器_取数量 ())` | 高 |
| **2c.** `FBrowser_浏览器_通过ID取浏览器` | **ALREADY COVERED** | 任何工具的**请求级公共参数** `browser_id` (integer) | 取值 `src/MCP_Server.wsv:10462` `请求浏览器ID = yyjson取整数 (参数JSON, "browser_id")` → `:10464` `目标浏览器ID = 请求浏览器ID`；消费 `src/MCP_Server.wsv:7750` `方法 取主浏览器` → `:7753-7755` `如果 (目标浏览器ID > 0) { result = 取浏览器ByID (目标浏览器ID) }` → `:7747` `返回 (FBrowser_浏览器_通过ID取浏览器 (browserID))`；另有直调 `src/MCP_Server_Core.wsv:632`（browser_list）、`:599`（browser_close） | 高 |
| **2d.** `FBrowser_浏览器_通过序号取浏览器` | **ALREADY COVERED（语义等价，非字面参数）+ 一处静态不可证** | `browser_list` 按类库清单顺序返回 id → 取第 N 项后再传 `browser_id` | `src/MCP_Server_Core.wsv:626-632` `listSize = ID清单.取大小 ()` / 计次循环 / `bid = ID清单.取整数值 (取循环索引 ())`，即输出**有序** id 清单 → 配合 2c 的 `browser_id`。**无法静态证明** `FBroHsBrowserListControl_GetBrowserIDList()` 的枚举顺序与 `GetBrowserFromIndex(序号)` 的索引顺序严格一致（二者都在闭源 FBro dll 内，类库 wsv 只暴露声明：`FBroLib.wsv:513-516` / `:487-492`）。**全项目 0 命中 `通过序号取浏览器`**；且在持有 browser 族 schema 的三个分派文件（`src/MCP_Server.wsv` / `src/MCP_Server_Core.wsv` / `src/MCP_Server_System.wsv`）中，所有 `index`/`序号` 参数都属 DOM/元素/脚本索引，**没有任何工具接受「浏览器序号」参数**（检索 `属性项JSON \("(index|序号|browser_index|nth)"` 仅命中 `browser_dom_query` / `browser_dom_select` / `browser_kernel_reverse_sources` / `browser_click_text` / `browser_element_action`） | 中 |
| **2e.** `FBrowser_浏览器_通过窗口句柄取浏览器` | **ALREADY COVERED** | `browser_find_by_hwnd`，参数 `hwnd` (integer) | `src/MCP_Server.wsv:9637` `添加工具JSON ("browser_find_by_hwnd", "按句柄查找浏览器", 单参数Schema文本 ("hwnd", "integer", "窗口句柄"))`；实现 `src/MCP_Server_Core.wsv:5708` → `:5711` `hwnd = ...yyjson取整数 (参数JSON, "hwnd")` → `:5717` `found = FBrowser_浏览器_通过窗口句柄取浏览器 (hwnd)` | 高 |
| **3.** `重新载入_忽略缓存` | **ALREADY COVERED** | `browser_reload`，参数 **`ignore_cache`** (boolean, 真 即忽略缓存) | 注册 `src/MCP_Server.wsv:9526` `添加工具JSON ("browser_reload", ...)` 内含 `属性项JSON ("ignore_cache", "boolean", "忽略缓存")`；实现 `src/MCP_Server_Core.wsv:223` `否则 (方法名 == "browser_reload")` → `:229-230` `忽略缓存 = ...yyjson取逻辑 (参数JSON, "ignore_cache")` → `:234-237` `如果 (忽略缓存) { browser.重新载入_忽略缓存 () }` / `:240` `否则 { browser.重新载入 () }` | 高 |
| **4.** `开始下载` | **ALREADY COVERED** | `browser_start_download`，参数 `url` (text) | 注册 `src/MCP_Server.wsv:9564` `添加工具JSON ("browser_start_download", "触发下载 \| 仅支持 http/https 协议", 单参数Schema文本 ("url", "text", "URL"))`；实现 `src/MCP_Server_Core.wsv:1421` → `:1435` `browser.开始下载 (url)`。**落地可用性另有实证代码**：`src/MCP_BrowserEvents.wsv:633` `方法 浏览器_即将下载` → `:691` `保存路径 = 下载目录 + "\\" + 下载.取推荐文件名 ()` → `:699` `下载回调.继续 (保存路径, 假)`（自动存盘到 Downloads，不弹 OS 另存框） | 高 |
| **5.** `显示隐藏窗口` | **REAL GAP**（且项目给出的「不可能」理由**与代码不符**，见下节） | 无。最接近的替代是 `browser_set_window_style` 的 `type=-16 (GWL_STYLE)` + `style`（**不等价**，只是写 GWL_STYLE 位） | 全 `src`（排除 `*~vbak*`）对 `显示隐藏窗口` **0 命中**；`_audit/_tool_ledger.json` 中不存在 `browser_show_window`/`browser_hide_window` 之类工具名（窗口族仅有 `browser_move_window` / `browser_set_window_style` / `browser_get_window_style` / `browser_window_info` / `browser_get_window_handle` / `browser_get_window_title` / `browser_set_auto_resize`）。类库入口本身存在：`FBroLib.wsv:1071-1076` `方法 显示隐藏窗口` 参数 `显示隐藏` → `FBroHsBrowserHost_ShowWindows`。替代路径 `src/MCP_Server_System.wsv:71` `否则 (方法名 == "browser_set_window_style")` → `:89` `browser.置窗口属性 (窗口类型, ...yyjson取整数 (参数JSON, "style"))`，而类库 `FBroLib.wsv:1092-1098` `置窗口属性` → `FBroHsBrowserHost_SetWindowLong`：清 `WS_VISIBLE`(0x10000000) 位**不等价于 ShowWindow(SW_HIDE)**（未配 `SWP_FRAMECHANGED`/`ShowWindow`，可见性变更不可靠），工具自身也只**警告**不实现：`:87` `"style 不能省略 \| 省略会被当作 0 而清掉窗口样式的全部位(含 WS_VISIBLE, 可能使窗口不可见/不可用)"` | 中高（REAL GAP 判定高；「替代路径不可靠」这一判断为中，因 CEF 侧未实测） |

**注A（对应 1c）：** `browser_uri_encode` 把类库的第二个参数 `use_plus` **硬编码为 `假`**（`src/MCP_Server_Core.wsv:5168`）。类库注释（`FBroLib.wsv:405-408`）写明 `use_plus=真` 时空格转 `+`（`application/x-www-form-urlencoded` 语义）。因此「URI 编码」这个能力本身可达，但 `+`/`%20` 两种口径**只能得到一种**，属参数面收窄，不是能力缺失。同类硬编码见 `:5180`（`URI解码 (data, 真, 真)`）。详见「新发现 4」。

---

## 第 5 项专章：架构事实（任务书要求「确认或反驳」）

**结论：任务书假设的「项目把浏览器嵌在宿主托管的 GUI 窗口里」——被代码反驳（REFUTED）。当前构建是控制台程序，浏览器窗口就是程序自己的顶层桌面窗口；因此 `显示隐藏窗口` / `移动窗口` 属于「可做到」而不是「不可能」。项目现有的失败话术既不准确、也谈不上诚实报告。**

证据链（全部只读静态）：

1. `src/main.wsv:6` `# AI浏览器 MCP Server — 控制台启动入口 (无MFC窗口依赖)`
2. `src/main.wsv:11` `类 启动类 <公开 基础类 = 程序类>` —— 全 `src` 唯一的程序基础类是 `程序类`（控制台）；没有任何类以 MFC/WTL 窗口类为 `基础类`（`grep '基础类 ='` 结果全部是 `程序类` 或 `类_FBrowser_*`）。
3. `src/main.wsv:203-209`
   ```
   变量 窗口信息 <类型 = FBrowser_窗口信息>
   窗口信息.父窗口句柄 = 0
   窗口信息.横坐标 = 0
   窗口信息.纵坐标 = 0
   窗口信息.宽度 = 1000
   窗口信息.高度 = 800
   ```
   类库对该参数有明确定义：`FBroLib.wsv:1085-1087` `方法 置父窗口` / `参数 父窗口句柄 <类型 = 变整数 注释 = "要设置的新父窗口句柄，如果为0，则以桌面为父窗口">` —— **父窗口=0 即桌面**，浏览器窗口因此是顶层窗口。
4. `src/main.wsv:228` `FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, , , 浏览器事件, , )` —— 创建时传入的就是上面那份「父窗口=0」的窗口信息。
5. 生成工程佐证：`generated-cpp/release-win32/makefile:13` `/D _CONSOLE /D _VOL_CONSOLE_EXE`；`:23` `/SUBSYSTEM:CONSOLE ... /ENTRY:wmainCRTStartup`。链接的 `vol_mfc.obj` 只是类库依赖，工程内没有实例化任何主窗口。
6. 用户文档自述也与此一致：`docs/客户使用手册.md:37` `> **说明**：关闭浏览器窗口会退出整个程序（控制台版）。` —— 用户看到的那个窗口**就是浏览器窗口本身**，没有第二个「主窗口」。
7. 所谓 "GUI" 指的是浏览器自己加载的欢迎页（`http://127.0.0.1:<port>/`，即 `src/MCP_Server.wsv:206` `取欢迎页HTML` / `index.html`），并非宿主 MFC 窗口。`_audit/_tool_ledger.json` 中 `browser_list` 实测返回 `[{"id":1,"url":"http://127.0.0.1:9222/"}, ...]`，`browser_window_info` 实测返回 `"parent_hwnd":0`。

由此可推：

- `browser_move_window`、`browser_set_auto_resize` 的「⛔ …嵌入式GUI浏览器…由主窗口统一管理」是**站不住的理由**：
  - `src/MCP_Server.wsv:9579` / `:9582` 的描述文案；
  - `src/MCP_Server_Core.wsv:5332-5335` `否则 (方法名 == "browser_move_window") { 返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 嵌入式GUI浏览器不支持 move_window \| 窗口尺寸由主窗口自动管理")) }`；
  - `src/MCP_Server_Core.wsv:5560-5563` 同款硬失败分支。
  类库侧 `移动窗口`（`FBroLib.wsv:1058-1069` → `FBroHsBrowserHost_MoveWindow`）与 `置自动调整大小`（`FBroLib.wsv:1038-1048`）**在 src 中 0 调用**，是被主动禁用的，不是架构上不可行。
- `browser_restore_gui` 并不恢复任何「布局」：`src/MCP_Server_Core.wsv:5564-5568` 只调 `浏览器容器.标记需要恢复布局 ()` 并回一句成功；消费端 `src/main.wsv:173-176` `如果 (浏览器容器.需要恢复布局) { 浏览器容器.需要恢复布局 = 假; 浏览器容器.恢复欢迎页 () }` —— 只重新导航欢迎页，**没有任何窗口几何/尺寸恢复动作**。工具描述「恢复嵌入式GUI布局与欢迎页」（`src/MCP_Server.wsv:9580`）名不符实。
- 因此第 5 项应判 **REAL GAP**：`显示隐藏窗口`（类库 `FBroLib.wsv:1071-1076` → `FBroHsBrowserHost_ShowWindows`）作用的目标正是这个顶层窗口，`browser_set_window_style(type=-16)` 只能提供写 GWL_STYLE 位的**不可靠**替代，而 `browser_set_auto_resize` / `browser_move_window` 是主动禁用。同一族里 `移动窗口`、`置自动调整大小` 也应一并视为**真缺口**（原「架构主动禁用」的说法不成立）。

---

## 阅读过程中顺带发现的**新**真缺口 / 问题（未在任务书 5 项内）

1. **`window_topmost` / `window_width` / `window_height` 三个配置项是死配置。**
   `src/MCP_Server.wsv:279-281` 定义 `窗口置顶` / `窗口默认宽度` / `窗口默认高度`，`:637-653` 从 `mcp_config.json` 读入并赋给它们；但全项目**只有写入、没有任何读取点**（`grep '窗口置顶|窗口默认宽度|窗口默认高度'` 仅命中这三行定义 + 三行赋值）。真正生效的是 `src/main.wsv:205-209` 写死的 `父窗口=0 / 0,0 / 1000×800`。而 `docs/MCP工具配置说明书.md:101-102` 把它们当作可用配置项对外承诺（`window_topmost` 默认 true「浏览器窗口置顶」、`window_width`/`window_height`）。→ 用户改配置文件不会有任何效果，且文档不实。置信度：高。
2. **`browser_set_auto_resize` 对应的类库方法全项目 0 调用**（`置自动调整大小`，类库 `FBroLib.wsv:1038-1048`），工具是恒失败桩。与第 5 项同族。（原报告已列 `移动窗口`，此处把 `置自动调整大小` 明确补齐。）
3. **`FBrowser_Parser_取数据URI` 没有工具**（类库 `FBroLib.wsv:394-402`，第二参数为 `mimetype`）。旧报告以「mimetype 前缀由调用方拼接」将其视为已覆盖 —— 严格说 `browser_base64_encode` 只做裸 Base64，**不产出 `data:<mime>;base64,...` 形式的完整 data URI**。属于弱等价，建议明确标为「部分覆盖」而非「已覆盖」。置信度：中。
4. **`browser_uri_encode` 的 `use_plus` 被硬编码为 `假`**（`src/MCP_Server_Core.wsv:5168`）。类库 `FBroLib.wsv:404-410` 说明 `use_plus=真` 时空格转 `+`（表单编码语义）。工具无法表达 `真` 分支；`browser_uri_decode` 的 `convert_to_utf8` / `unescape_rule` 同样被硬编码为 `真,真`（`:5180`）。这属于**参数面收窄**而非能力缺失，但会让「application/x-www-form-urlencoded 解码（`+` → 空格）」在 `uri_decode` 路径上得不到保证（`+` 是 URI 保留规则的 `unescape_rule` 位，静态读代码无法确认 `真` 是否覆盖 `+` 语义）。置信度：中（需实测确认）。
5. **`browser_find_by_hwnd` 取的是「浏览器的窗口句柄」不是父窗口句柄**（类库 `FBroLib.wsv:494-499` 注释明写「注意这里是浏览器的窗口句柄，不是浏览器父窗口的句柄」），而 `browser_get_window_handle`（`src/MCP_Server_Core.wsv:1622` `browser.取窗口句柄 ()`）与 `browser_window_info` 的 `hwnd`（`:5322`）返回的正是同一个值 —— 组合可用，但工具描述未点明这层对应关系，AI 容易误配 `parent_hwnd`。属于可用性（非能力）问题。置信度：高。

---

## 复核局限性（如实声明）

- 全部结论来自静态阅读。**未执行任何编译、未调用任何 MCP 工具**；`_audit/_tool_ledger.json` 中记录的「上次实测结果」仅作为旁证引用，不作为本次复核的执行证据。
- 无法静态判定的两点已就地标注：(a) `GetBrowserIDList()` 与 `GetBrowserFromIndex()` 的顺序一致性（第 2d 项）；(b) 清 `WS_VISIBLE` 位在本 CEF 宿主窗口上是否真能产生可见性变化、以及 `URI解码(真,真)` 对 `+` 的处理（第 5 项、新发现 4）。
- CEF 的 CDP `Browser.setWindowBounds` 是否在本项目所用 CEF 版本中实现，无法从磁盘静态确认；旧报告断言「CDP 无隐藏宿主窗口的方法」我**既不能证实也不能证伪**，故第 5 项未把 CDP 直通计入「已覆盖」。
