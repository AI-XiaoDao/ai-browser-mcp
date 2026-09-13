# 窗口几何 / 可见性 API 研究报告（只读静态调查）

调查目标：本项目（火山视窗 `/SUBSYSTEM:CONSOLE`，桌面父窗口浏览器）如何移动 / 缩放 / 显示 / 隐藏浏览器窗口。

**本报告全部结论均来自静态阅读源码。未编译、未调用任何 MCP 工具、未启动或停止任何程序、未修改任何源文件。**
凡属推断之处均已显式标注「推断」；凡未找到的 API 均已注明「未找到」并给出检索范围。

---

## 0. 检索范围与方法（"未找到" 的判定依据）

| 检索对象 | 绝对路径 | 结果 |
|---|---|---|
| 类库权威定义 | `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\` | 递归列出**仅 8 个 `.wsv`**：`FBroCallback.wsv`(39069B)、`FBroConst.wsv`(36976B)、`FBroDataType.wsv`(77608B)、`FBroEventControl.wsv`(143472B)、`FBroHelp.wsv`(3753B)、`FBroLib.wsv`(287774B)、`FBroValue.wsv`(65183B)、`FBroVip.wsv`(137695B)。**目录内无任何 `.h` / `.hpp` / `.cpp` / `.lib`**（`Get-ChildItem -Recurse -Force` 全量列举确认） |
| C++ 宿主函数声明 | 全盘搜索 `*FBro*.h/*.hpp/*.lib`（根目录：项目目录、技能目录、`C:\Program Files\voldev`、`D:\voldev`、`C:\voldev`） | 仅命中项目内 Volcano **生成**头（`generated-cpp\**\vcls_*.h`）。`C:\Program Files\voldev`、`D:\voldev`、`C:\voldev` **均 NOT PRESENT**（本机火山安装目录不在这些位置）。**`FBroHsBrowserHost_*` 的 C++ 原型在磁盘上不可得** |
| 项目源码 | `...\AI-Fbowser-Mcp\src\*.wsv`（16 个，排除 `备份\`、`_int`、`~vbak`） | 见下 |
| 官方例程 | `...\资料\例子\FB浏览器模块例子\` 等全量 `资料\例子\` | 真实用法见第 5 节 |
| 项目内既有实测记录 | `...\AI-Fbowser-Mcp\_audit\_probe_result.json`、`_cold_matrix.json`、`_tool_ledger.json/.md` | 第 3 节引用（**他人先前记录，非本次实测**） |

关键正则检索（对整个 `FBrowser浏览器` 目录）：
`置窗口位置|置窗口大小|取顶层窗口句柄|最小化窗口|最大化窗口|取窗口矩形|取客户区` → **0 命中**。
`SetWindowPos|GetWindowRect|SWP_|SW_|ShowWindow|IsWindowVisible|GetTopWindow|GetAncestor` → **0 命中**（仅命中 `SetWindowLong`/`GetWindowLong`/`MoveWindow`/`ShowWindows`/`GetParent`/`SetParent` 的 `FBroHs*` 调用点）。
项目 `src\` 内 `GetAncestor|SetWindowPos|ShowWindow|MoveWindow|GetWindowRect|IsWindowVisible|user32|SetForegroundWindow` → **0 命中**。

---

## 1.(a) 窗口几何 / 可见性 API 清单

**声明类**：`类_FBrowser_浏览器`，声明处 `FBroLib.wsv:539`
> `类 类_FBrowser_浏览器 <公开 @全局类 = 真>`

该类方法体范围 `539–1461`（下一个类 `类_FBrowser_基础框架` 起于 `FBroLib.wsv:1463`）。

### 1.1 几何 / 可见性 / 父窗口 / 句柄

| # | 方法 | 完整签名（逐字） | 注释/文档 | file:line | 底层宿主调用 |
|---|---|---|---|---|---|
| 1 | `取窗口句柄` | `方法 取窗口句柄 <公开 类型 = 变整数 注释 = "英文名：GetWindowHandle 说明:Retrieve the window handle for this browser,只能主进程中使用" @禁止流程检查 = 真>` | 同上（**唯一文档就是这句注释**） | `FBroLib.wsv:817-822` | `return (M_POINTER)(FBroHsBrowserHost_GetWindowHandle(m_class));` (`:820`) |
| 2 | `取打开者窗口句柄` | `方法 取打开者窗口句柄 <公开 类型 = 变整数 注释 = "英文名：GetOpenerWindowHandle 说明:Retrieve the window handle of the browser that opened this browser" @禁止流程检查 = 真>` | 同上 | `FBroLib.wsv:824-829` | `return (int64_t)FBroHsBrowserHost_GetOpenerWindowHandle(m_class);` (`:828`) |
| 3 | **`移动窗口`** | 方法行无注释：`方法 移动窗口 <公开>`；参数：`参数 左边 <类型 = 整数>` / `参数 顶边 <类型 = 整数>` / `参数 宽度 <类型 = 整数>` / `参数 高度 <类型 = 整数>` / `参数 是否重画 <类型 = 逻辑型 @默认值 = 假>`。**无返回类型** | **该类库对本方法未提供任何 `注释`**（唯一文字是方法体内一行开发备注） | `FBroLib.wsv:1058-1069` | `FBroHsBrowserHost_MoveWindow(m_class,@<左边>,@<顶边>,@<宽度>,@<高度>,@<是否重画>);` (`:1066`)，前置 `if(IsEmpty()) return ;` (`:1065`) |
| 4 | **`显示隐藏窗口`** | `方法 显示隐藏窗口 <公开 注释 = "显示隐藏浏览器">`；参数：`参数 显示隐藏 <类型 = 逻辑型 注释 = "为真显示浏览器，为假隐藏浏览器">`。**无返回类型** | 方法注释 `显示隐藏浏览器`；参数注释 `为真显示浏览器，为假隐藏浏览器` | `FBroLib.wsv:1071-1076` | `if(!IsEmpty()) FBroHsBrowserHost_ShowWindows(m_class,@<显示隐藏>);` (`:1074`) |
| 5 | `取父窗口句柄` | `方法 取父窗口句柄 <公开 类型 = 变整数 @禁止流程检查 = 真>` | 无注释 | `FBroLib.wsv:1078-1083` | `if(!IsEmpty()) return @dt<变整数>(FBroHsBrowserHost_GetParent(m_class));` / `return 0;` (`:1080-1081`) |
| 6 | `置父窗口` | `方法 置父窗口 <公开 注释 = "设置浏览器父窗口">`；参数：`参数 父窗口句柄 <类型 = 变整数 注释 = "要设置的新父窗口句柄，如果为0，则以桌面为父窗口">` | **「如果为0，则以桌面为父窗口」——本项目 `父窗口句柄 = 0` 即桌面父窗口，故浏览器窗口是顶层窗口** | `FBroLib.wsv:1085-1090` | `if(!IsEmpty()) FBroHsBrowserHost_SetParent(m_class,(HWND)@<父窗口句柄>);` (`:1088`) |
| 7 | `置窗口属性` | `方法 置窗口属性 <公开 注释 = "设置浏览器窗口属性，通常用于设置窗口风格">`；参数：`参数 风格类型 <类型 = 整数>` / `参数 风格 <类型 = 整数>`。**无返回类型** | 注释同上 | `FBroLib.wsv:1092-1098` | `if(!IsEmpty()) FBroHsBrowserHost_SetWindowLong(m_class,@<风格类型>,@<风格>);` (`:1096`) |
| 8 | `取窗口属性` | `方法 取窗口属性 <公开 类型 = 整数 注释 = "获取浏览器窗口属性，通常用于设置窗口风格" @禁止流程检查 = 真>`；参数：`参数 风格类型 <类型 = 整数 注释 = "参考:窗口风格.">` | 注释同上 | `FBroLib.wsv:1100-1105` | `return IsEmpty()? 0 : FBroHsBrowserHost_GetWindowLong(m_class,@<风格类型>);` (`:1103`) |
| 9 | **`置自动调整大小`** | `方法 置自动调整大小 <公开 注释 = "英文名：SetAutoResizeEnabled">`；参数：`参数 启用 <类型 = 逻辑型>` / `参数 最小高度 <类型 = 整数>` / `参数 最小宽度 <类型 = 整数>` / `参数 最大高度 <类型 = 整数>` / `参数 最大宽度 <类型 = 整数>`。**无返回类型** | **全部文档只有 `注释 = "英文名：SetAutoResizeEnabled"`。5 个参数一个注释都没有** | `FBroLib.wsv:1038-1048` | `FBroHsBrowserHost_SetAutoResizeEnabled(m_class,@<启用>,@<最小高度>,@<最小宽度>,@<最大高度>,@<最大宽度>);` (`:1046`) |
| 10 | `取窗口标题` | `方法 取窗口标题 <公开 类型 = 文本型 注释 = "取当前浏览器窗口标题，非父窗口标题" @禁止流程检查 = 真>` | 注释同上 | `FBroLib.wsv:1107-1112` | `FBroHsBrowserHost_GetWindowsTitle(m_class)` (`:1110`) |
| 11 | `置焦点` | `方法 置焦点 <公开 注释 = "英文名：SetFocus 说明:Set whether the browser is focused">`；`参数 焦点 <类型 = 逻辑型>` | 同注释 | `FBroLib.wsv:809-815` | `FBroHsBrowserHost_SetFocus(m_class,@<焦点>);` (`:813`) |
| 12 | `是否浏览器视图` | `方法 是否浏览器视图 <公开 类型 = 逻辑型 注释 = "英文名：HasView 说明:Returns true if this browser is wrapped in a CefBrowserView" @禁止流程检查 = 真>` | 同注释 | `FBroLib.wsv:831-836` | `FBroHsBrowserHost_HasView(m_class)` (`:834`) |
| 13 | `取窗口运行风格` | `方法 取窗口运行风格 <公开 类型 = 窗口运行风格 @禁止流程检查 = 真>` | 无注释 | `FBroLib.wsv:1456-1460` | `return FBroHsBrowserHost_GetRuntimeStyle(m_class);` (`:1459`) |
| 14 | `取主浏览器`（**类库自身也有同名方法，勿与项目 helper 混淆**） | `方法 取主浏览器 <公开 类型 = 类_FBrowser_浏览器 注释 = "取出当前浏览器的主(父)浏览，如果不存在或者已经关闭将返回空" @禁止流程检查 = 真>` | 同注释 | `FBroLib.wsv:1443-1447` | `FBroHsBrowserHost_GetMainBrowser(m_class)` (`:1445`) |

配套类型 `窗口运行风格`（`FBroConst.wsv:750-757`，`@常量类 = 整数`）：`默认=0`(`CEF_RUNTIME_STYLE_DEFAULT 默认为谷歌风格`)、`谷歌=1`(`CEF_RUNTIME_STYLE_CHROME 谷歌风格`)、`经典=2`(`CEF_RUNTIME_STYLE_ALLOY CEF经典风格`)。

### 1.2 静态辅助（HWND ↔ 浏览器）

| 方法 | 完整签名（逐字） | file:line | 底层调用 |
|---|---|---|---|
| `FBrowser_浏览器_通过窗口句柄取浏览器` | `方法 FBrowser_浏览器_通过窗口句柄取浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 注释 = " 通过浏览器的窗口句柄取浏览器，注意这里是浏览器的窗口句柄，不是浏览器父窗口的句柄" @禁止流程检查 = 真>`；参数 `参数 窗口句柄 <类型 = 变整数>` | 声明类 `类 FBrowser辅助功能`（`FBroLib.wsv:377`），方法体 `FBroLib.wsv:494-499` | `return @dt<类_FBrowser_浏览器>(FBroHsBrowserListControl_GetBrowserFromWindowHandle((HWND)@<窗口句柄>));` (`:497`) |

### 1.3 明确「未找到」的 API（不要臆造）

以下名称在整个 `资料\类库\FBrowser浏览器\`（8 个文件全量）中 **0 命中**：

- `置窗口位置` — **未找到**
- `置窗口大小` — **未找到**
- `取窗口矩形` — **未找到**
- `取客户区`（及任何客户区尺寸获取） — **未找到**
- `取顶层窗口句柄` — **未找到**
- `最小化窗口` / `最大化窗口` — **未找到**
- 任何 `SetWindowPos` / `ShowWindow` / `GetWindowRect` / `GetAncestor` / `GetTopWindow` / `SWP_*` / `SW_*` 的类库封装 — **未找到**（整个类库目录对 `SetWindowPos|ShowWindow|GetWindowRect|GetAncestor|IsWindowVisible|GetTopWindow|SWP_|SW_` 均 0 命中）

**必须点明的同名陷阱**：`FBroLib.wsv:3405-3415` 存在 `是否可见` / `置可见状态`，但它们**不是窗口可见性**：

```
方法 是否可见 <公开 类型 = 逻辑型 注释 = "英文名：IsVisable" @禁止流程检查 = 真>
参数 命令ID <类型 = 整数>
{
    @ return IsEmpty() ? false : FBroHsMenuModel_IsVisable(m_class,@<命令ID>);
}
```

声明类为 `类_FBrowser_菜单模式`（`FBroLib.wsv:3288`，`注释 = "CefMenuModel"`），参数是 `命令ID`，底层是 `FBroHsMenuModel_*` —— **菜单项可见性**，与浏览器窗口无关。不要用它实现 show/hide。

同理 `FBrowser_矩形位置`（`FBroDataType.wsv`）与 `取边界`（`FBroLib.wsv:4295`，声明类 `类_FBrowser_DOM节点`，`注释 = "Returns the bounds of the element."`）都是 **DOM 元素**矩形，不是窗口矩形；`离屏渲染_获取根屏幕矩形` / `离屏渲染_获取视图矩形`（`FBroEventControl.wsv:1420/1437`）是 **离屏渲染事件回填**，不是可取调的窗口矩形 API。

---

## 2. 宿主层（`FBroHsBrowserHost_*` 等）相关函数

**重要前提**：这些是嵌入式 C++ 宿主函数，**类库资料内没有任何声明文件**（整目录仅 8 个 `.wsv`，无 `.h`）。下表签名是**从类库调用点（call site）反推**的，`file:line` 指向调用点，**不是**声明处。

| 宿主函数 | 调用点逐字实参 | file:line | 是否接收 HWND | 备注 |
|---|---|---|---|---|
| `FBroHsBrowserHost_GetWindowHandle` | `@ return (M_POINTER)(FBroHsBrowserHost_GetWindowHandle(m_class));` | `FBroLib.wsv:820` | 返回 HWND（返回值被强转 `M_POINTER`） | 类库注释限定「只能主进程中使用」 |
| `FBroHsBrowserHost_GetParent` | `@ if(!IsEmpty()) return @dt<变整数>(FBroHsBrowserHost_GetParent(m_class));` | `FBroLib.wsv:1080` | 返回 HWND | 32 位生成代码为 `INT(...)`，64 位为 `INT64(...)`（`generated-cpp\release-win32\vpkg_FBroLib.cpp:479` vs `release-x64\vpkg_FBroLib.cpp:479`） |
| `FBroHsBrowserHost_SetParent` | `@ if(!IsEmpty()) FBroHsBrowserHost_SetParent(m_class,(HWND)@<父窗口句柄>);` | `FBroLib.wsv:1088` | **接收 HWND**（显式 `(HWND)` 强转） | 0 = 桌面父窗口 |
| `FBroHsBrowserHost_SetWindowLong` | `@ if(!IsEmpty()) FBroHsBrowserHost_SetWindowLong(m_class,@<风格类型>,@<风格>);` | `FBroLib.wsv:1096` | 不接收（内部隐式取窗口句柄） | `风格类型` 用 Win32 GWL 索引 |
| `FBroHsBrowserHost_GetWindowLong` | `@ return IsEmpty()? 0 : FBroHsBrowserHost_GetWindowLong(m_class,@<风格类型>);` | `FBroLib.wsv:1103` | 不接收 | 同上 |
| `FBroHsBrowserHost_MoveWindow` | `@ FBroHsBrowserHost_MoveWindow(m_class,@<左边>,@<顶边>,@<宽度>,@<高度>,@<是否重画>);` | `FBroLib.wsv:1066` | 不接收 | **参数顺序：左、顶、宽、高、重画** |
| `FBroHsBrowserHost_ShowWindows` | `@ if(!IsEmpty()) FBroHsBrowserHost_ShowWindows(m_class,@<显示隐藏>);` | `FBroLib.wsv:1074` | 不接收 | 函数名是复数 `ShowWindows`（类库原文如此） |
| `FBroHsBrowserHost_SetAutoResizeEnabled` | `@ FBroHsBrowserHost_SetAutoResizeEnabled(m_class,@<启用>,@<最小高度>,@<最小宽度>,@<最大高度>,@<最大宽度>);` | `FBroLib.wsv:1046` | 不接收 | **注意：宽高顺序是「高在前、宽在后」** |
| `FBroHsBrowserHost_ShowDevTools` | `@ FBroHsBrowserHost_ShowDevTools(m_class,@<标题>.GetText(),(HWND)@<父窗口>,@<横坐标>,@<纵坐标>,@<宽度>,@<高度>,...,tempclass,@<禁用事件>.ToFBroData());` | `FBroLib.wsv:960` | **接收 HWND**（显式 `(HWND)` 强转） | 开发者工具窗口 —— 唯一「显式传入 HWND 去开一个窗口」的先例 |
| `FBroHsBrowserListControl_GetBrowserFromWindowHandle` | `@ return @dt<类_FBrowser_浏览器>(FBroHsBrowserListControl_GetBrowserFromWindowHandle((HWND)@<窗口句柄>));` | `FBroLib.wsv:497` | **接收 HWND**（显式 `(HWND)` 强转） | HWND → 浏览器对象 反查 |
| `FBroHsBrowserHost_GetRuntimeStyle` | `@ return FBroHsBrowserHost_GetRuntimeStyle(m_class);` | `FBroLib.wsv:1459` | 不接收 | 返回 `窗口运行风格` |

**结论**：真正意义上「以 HWND 为参数、且与窗口几何/可见性相关」的宿主函数只有 `SetParent`、`ShowDevTools`、`GetBrowserFromWindowHandle` 三个；**移动/缩放/显隐三个宿主函数都不接收 HWND，而是由 `m_class`（`CefRefPtr<CefBrowserHost>`）隐式定位窗口**。这意味着调用方不需要自己拿 HWND —— 只要拿到 `类_FBrowser_浏览器` 对象即可，这让「HWND 到底是不是顶层窗口句柄」这个问题对 `移动窗口`/`显示隐藏窗口` 的实现**不构成阻塞**。

`m_class` 类型由类库嵌入头确认（`FBroLib.wsv` 类定义体内 `# <> <include>` 块；同类证据见 `FBroHelp.wsv:10` `CefRefPtr<CefResourceHandler> m_resourcehandler=nullptr;` 的写法惯例）。

---

## 3. 浏览器 HWND 的正确获取方式

### 3.1 项目现有两个出口实际调用的是哪个类库方法

| 项目工具 / 字段 | 项目代码 | file:line | 实际类库调用 | 类库 file:line |
|---|---|---|---|---|
| `browser_get_window_handle` → `hwnd` | `返回 (MCP_响应构建.构建简单JSON ("hwnd", 到文本 (browser.取窗口句柄 ())))` | `src\MCP_Server_Core.wsv:1642` | `取窗口句柄` → `FBroHsBrowserHost_GetWindowHandle` | `FBroLib.wsv:817/820` |
| `browser_window_info` → `hwnd` | `win对象.加入长整数成员 ("hwnd", browser.取窗口句柄 ())` | `src\MCP_Server_Core.wsv:5342` | 同上 | 同上 |
| `browser_window_info` → `parent_hwnd` | `win对象.加入长整数成员 ("parent_hwnd", browser.取父窗口句柄 ())` | `src\MCP_Server_Core.wsv:5343` | `取父窗口句柄` → `FBroHsBrowserHost_GetParent` | `FBroLib.wsv:1078/1080` |
| `browser_window_info` → `opener_hwnd` | `win对象.加入长整数成员 ("opener_hwnd", browser.取打开者窗口句柄 ())` | `src\MCP_Server_Core.wsv:5344` | `取打开者窗口句柄` → `FBroHsBrowserHost_GetOpenerWindowHandle` | `FBroLib.wsv:824/828` |

即：**两个工具返回的是同一个值**（`GetWindowHandle`），`parent_hwnd` 是另一个值（`GetParent`）。

### 3.2 顶层 / 父窗口句柄能否单独取得

- **没有**任何「取顶层窗口句柄」类库 API（第 1.3 节，未找到）。
- `取父窗口句柄()` 在本项目里**不是**可用的顶层句柄来源：项目以 `窗口信息.父窗口句柄 = 0` 创建（`src\main.wsv:205`），而 `置父窗口` 的文档写明 **「如果为0，则以桌面为父窗口」**（`FBroLib.wsv:1086`），故它是「顶层/桌面父窗口」。已有**他人先前**的记录显示实测确实返回 0：
  - `_audit\_probe_result.json:1034`：`{"title":"Example Domain - Chromium","hwnd":4524590,"parent_hwnd":0,"opener_hwnd":0,...}`
  - `_audit\_cold_matrix.json:1021`：`"hwnd":3278390,"parent_hwnd":0,"opener_hwnd":0`
  - `_audit\_tool_ledger.json:899`：`"hwnd":6228910,"parent_hwnd":0`
  - `_audit\_tool_ledger.md:61`（`browser_get_window_handle`）：`{"success":true,"hwnd":"2952610"}`
  （**这些是先前审计批次写入的记录，本次未复现，仅供交叉参考**。注意 `browser_get_window_handle` 返回字符串、`browser_window_info` 返回数字，同一句柄两种 JSON 类型。）
- **旁证**：官方例程用 `取父窗口句柄 () == 0` 判定「浏览器是独立顶层窗口」：`资料\例子\FB浏览器模块例子\browser_event1.wsv:255`
  `如果真 (浏览器.取父窗口句柄 () == 0 && 浏览器.取窗口运行风格 () == 窗口运行风格.谷歌)` —— 该分支走 VIP `高级_创建标签浏览器`（`browser_event1.wsv:262`），说明**「父句柄为 0」在类库作者眼中就是「无宿主父窗口的顶层窗口」**。
- 若将来确实需要「从返回的 HWND 反推顶层 HWND」，类库**没有**提供路径，只能嵌入 Win32 `GetAncestor(hwnd, GA_ROOT)`。**项目已有嵌入式 C++ 先例**：`src\main.wsv:112-118`
  ```
  @ {
  @     MSG msg;
  @     while (PeekMessageW(&msg, NULL, 0, 0, PM_REMOVE)) {
  @         TranslateMessage(&msg);
  @         DispatchMessageW(&msg);
  @     }
  @ }
  ```
  即「嵌入 user32 调用」在本项目技术上已是既有做法。但**这是新逻辑、非类库调用，本报告不推荐作为首选**（见第 5 节）。

**小结（供实现决策）**：实现 `browser_move_window` / `browser_set_auto_resize` / 显隐工具**都不需要 HWND**——三个宿主函数都通过 `m_class` 隐式定位窗口（第 2 节）。HWND 只在「外部独立验证」时需要。

---

## 4. `置自动调整大小` 的文档原文 与「正确实现」的定义

### 4.1 原文逐字引用（`FBroLib.wsv:1038-1048`）

```
方法 置自动调整大小 <公开 注释 = "英文名：SetAutoResizeEnabled">
参数 启用 <类型 = 逻辑型>
参数 最小高度 <类型 = 整数>
参数 最小宽度 <类型 = 整数>
参数 最大高度 <类型 = 整数>
参数 最大宽度 <类型 = 整数>
{
    @ if(IsEmpty()) return;
    @ FBroHsBrowserHost_SetAutoResizeEnabled(m_class,@<启用>,@<最小高度>,@<最小宽度>,@<最大高度>,@<最大宽度>);

}
```

**必须明确指出的缺口**：类库对「auto resize 是什么意思」**没有任何中文说明**。全文文档就是 `注释 = "英文名：SetAutoResizeEnabled"` 一句英文名；5 个参数（启用/最小高度/最小宽度/最大高度/最大宽度）**全部无 `注释`**。因此**不能**从类库资料中引用出「auto resize 的语义定义」。

### 4.2 语义只能回到 CEF 官方定义（外部依据，非类库）

`SetAutoResizeEnabled` 是 `CefBrowserHost` 方法，语义为：启用**通过 `CefDisplayHandler::OnAutoResize` 上报的自动尺寸通知**；通知在启动时以及每次尺寸变化后发送；`min_size` 与 `max_size` 定义**允许增长的区间**；若 `min_size` 或 `max_size` 的宽或高为 0，则该维度不受约束。参考：[CefDisplayHandler::OnAutoResize](https://cef-builds.spotifycdn.com/docs/119.1/classCefDisplayHandler.html)、[IBrowserHost.SetAutoResizeEnabled](http://cefsharp.github.io/api/113.1.x/html/M_CefSharp_IBrowserHost_SetAutoResizeEnabled.htm)。

**关键风险 —— 宽高顺序可能被对调**：CEF 的 `CefSize` 成员顺序是 `{width, height}`，即官方签名等价于 `SetAutoResizeEnabled(bool, min{width,height}, max{width,height})`；而 Volcano 声明的参数顺序是**「最小高度」在「最小宽度」之前、「最大高度」在「最大宽度」之前**（`FBroLib.wsv:1040-1043`）。宿主包装函数 `FBroHsBrowserHost_SetAutoResizeEnabled` 的原型不可得（第 0 节），因此**「第 2/3 参与第 4/5 参究竟哪个是宽、哪个是高」在静态上无法确定**。官方例程也**无法**帮助消歧，因为两处调用传的都是对称值（见 5.2）。**这是实现前必须实测的项（见第 6 节）**。

### 4.3 官方例程中的实际用法（唯一引用样本）

`资料\例子\FB浏览器模块例子\main2.wsv:711-714`
```
否则 (命令代码 == 菜单.设置自动调整尺寸)
{
    browser.置自动调整大小 (真, 0, 0, 10000, 10000)
}
```
同型调用另见 `资料\例子\FB浏览器模块例子\main21.wsv:613`（同样的 `(真, 0, 0, 10000, 10000)`）。

要点：① 它是**菜单命令显式触发**的，不是挂在窗口尺寸事件里（对比 `移动窗口`，见 5.1）；② 传参 `min=(0,0)`、`max=(10000,10000)` —— **对称值，无法区分宽高**。

### 4.4 什么才算 `browser_set_auto_resize` 的「正确实现」

1. **先补 schema**。该工具目前**连参数都没有**：`src\MCP_Server.wsv:9601` 用的是两参形式
   `添加工具JSON ("browser_set_auto_resize", "⛔ 本工具恒失败: 嵌入式GUI浏览器尺寸由主窗口布局管理, 不支持自动调整| 需要改视口请用 fingerprint viewport")`
   —— 对比 `browser_move_window`（`src\MCP_Server.wsv:9604`）用了 `多属性Schema文本(...)` 五参形式。**没有 schema 就永远无法收到 enabled/min/max**。
2. **真的调用类库方法**，替换掉恒失败桩：
   `src\MCP_Server_Core.wsv:5580-5583`
   ```
   否则 (方法名 == "browser_set_auto_resize")
   {
       返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 嵌入式GUI浏览器不支持 set_auto_resize | 尺寸由主窗口 adjust_layout 管理"))
   }
   ```
3. **参数按类库声明顺序映射**：`启用→enabled`、`最小高度→第2参`、`最小宽度→第3参`、`最大高度→第4参`、`最大宽度→第5参`；**并且**在文档/schema 描述中把「高度在前」这一反直觉顺序写明，或在实测确认可对调后再决定对外语义。
4. **空/关闭守卫 + 缺参守卫**，与同族工具一致（见 5.2）。
5. **诚实报告**：`置自动调整大小` **无返回值**（`FBroLib.wsv:1038` 签名无 `类型 =`），类库内也没有任何读取当前 auto-resize 状态的 API（第 1.3 节）。故**只能报「已调用」，不能报「已生效」**；类库侧也无法回读验证。
6. **修描述**：`src\MCP_Server.wsv:9601` 的「⛔ 本工具恒失败」文案与事实不符（浏览器是桌面父窗口的顶层窗口，`src\main.wsv:205` + `FBroLib.wsv:1086`），应从工具清单与描述中撤除或改写。

---

## 5. 逐工具的最小实现建议

> **通用前提（三个工具共用）**：都用 `src\MCP_Server_System.wsv:71-93`（`browser_set_window_style`，**唯一可用的窗口族工作样板**）的结构：取浏览器 → 判空 → 校验参数 → 调类库 → 返回。
> **复用 helper（不要新写）**：`MCP命令服务器.取主浏览器 ()`，定义 `src\MCP_Server.wsv:7796`（`方法 取主浏览器 <公开 静态 类型 = 类_FBrowser_浏览器 @输出名 = "GetMainBrowser" @强制输出 = 真>`）。取空/已关闭的守卫写法直接照抄 `src\MCP_Server_Core.wsv:5337`：`如果 (browser.是否为空 () == 假 && browser.是否已关闭 () == 假)`。
> **注意区分**：`browser.取主浏览器()`（类库方法，`FBroLib.wsv:1443`）与 `MCP命令服务器.取主浏览器 ()`（项目 helper，`MCP_Server.wsv:7796`）是两个不同东西；项目既有代码一律用后者。

### 5.1 `browser_move_window`（现恒失败，`src\MCP_Server_Core.wsv:5352-5355`）

**schema 已存在，无需改**：`src\MCP_Server.wsv:9604`，参数 `x`/`y`/`width`/`height`/`repaint`，必填 `"x","y"`：
```
添加工具JSON ("browser_move_window", "⛔ 本工具恒失败: ...", 多属性Schema文本 (属性项JSON ("x", "integer", "X") + "," + 属性项JSON ("y", "integer", "Y") + "," + 属性项JSON ("width", "integer", "宽") + "," + 属性项JSON ("height", "integer", "高") + "," + 属性项JSON ("repaint", "boolean", "重绘"), "\"x\",\"y\""))
```

**建议实现（单次类库调用）**：

| 调用方传入 | → | 类库实参 |
|---|---|---|
| `x`（`yyjson取整数`） | → | `左边`（第1参） |
| `y`（`yyjson取整数`） | → | `顶边`（第2参） |
| `width`（`yyjson取整数`） | → | `宽度`（第3参） |
| `height`（`yyjson取整数`） | → | `高度`（第4参） |
| `repaint`（`yyjson取逻辑`，缺省假） | → | `是否重画`（第5参，`@默认值 = 假`） |

`browser.移动窗口 (x, y, width, height, repaint)` —— 依据 `FBroLib.wsv:1058-1066`；`@<左边>,@<顶边>,@<宽度>,@<高度>,@<是否重画>` 顺序与 schema 的 `x/y/width/height/repaint` **一一对应且同序**，无歧义。

**参数解析的现成先例**：`yyjson取整数` 用法见 `src\MCP_Server_System.wsv:79`/`:89`；`yyjson取逻辑` 用法见 `src\MCP_Server_Core.wsv:1657`。

**必须补的缺参守卫**（否则省略 `width`/`height` 会被当 0，把窗口缩成 0×0；项目已有此约定，如 `src\MCP_Server_Core.wsv:1648-1651` 的 `focus 不能省略…` 与 `src\MCP_Server_System.wsv:85-88` 的 `style 不能省略…`）：对 `x/y/width/height` 逐个用 `MCP命令服务器.参数键存在 (参数JSON, ...)` 判定并拒绝，消息给可行动建议（0 是合法坐标，但 0 宽高不是合法窗口）。

**返回值**：`移动窗口` **无返回值**，且类库内部对空对象是**静默 `return`**（`FBroLib.wsv:1065`）。故实现只能返回「已提交」语义；项目对此已有专门的响应类型：`MCP_响应构建.响应_需要刷新 (命令ID, "窗口风格已设置")`（`src\MCP_Server_System.wsv:90`）——`browser_move_window` 应使用同一响应builder（窗口几何变更属同类「需重绘」语义），**不要**用 `命令成功` 暗示已验证生效。

**工具描述**：`src\MCP_Server.wsv:9604` 的「⛔ 本工具恒失败…」前缀必须改写。

**实现依据的旁证**：官方例程就是这样调的 —— `资料\例子\FB浏览器模块例子\main2.wsv:252`
`浏览器.移动窗口 (0, 0, 取用户区宽度 (), 取用户区高度 (), 假)`（在 `我的主窗口_尺寸被改变` 事件内，`main2.wsv:244-257`）；同型一行式调用还出现在 `main.wsv:129`、`main3.wsv:141`、`main8.wsv:136`、`main10.wsv:143`（`main10.wsv` 传 `(310, 0, 取用户区宽度 () - 310, ...)` —— 说明**左/顶/宽/高确实是四个独立数值**，非布尔或标志位）。

### 5.2 `browser_set_auto_resize`（现恒失败，`src\MCP_Server_Core.wsv:5580-5583`，且无 schema）

**最小实现 = 补 schema + 一次类库调用**：
`browser.置自动调整大小 (启用, 最小高度, 最小宽度, 最大高度, 最大宽度)`，依据 `FBroLib.wsv:1038-1046`。

**对外 schema 建议**（与项目既有宽高词汇保持一致用 `width/height`，但**内部映射必须实测确认**，见第 6 节实验 E3）：
`enabled`(boolean,必填) / `min_width`,`min_height`,`max_width`,`max_height`(integer,可选)。

**建议给安全默认值**以复刻官方例程的保守用法（`main2.wsv:713` 传 `0,0,10000,10000` 即「不限下限、上限 10000」）：未传 min 时用 0、未传 max 时用 10000，避免出现 `max < min` 或 0 宽高导致的约束异常。

**必须做的守卫**：与 5.1 同（`取主浏览器` + `是否为空`/`是否已关闭`）。

**必须诚实的地方**：
- 该调用**无返回值**、且类库无「读回 auto-resize 状态」的 API（第 1.3 节），**不能报告「已生效」**；
- CEF 语义下 auto-resize 的意义是「随宿主窗口尺寸变化自动跟随并回填通知」（第 4.2 节）。本项目浏览器是**桌面父窗口的顶层窗口**，没有宿主容器会去改它的尺寸，因此**该开关在本架构下可能实际无可观察效果**——这属于必须实测的项（第 6 节实验 E4），在实测结论出来之前，工具描述应写成中性陈述而非效果承诺。

### 5.3 （可选新增）显示 / 隐藏工具

**最小实现 = 一次类库调用**：`browser.显示隐藏窗口 (显示)`，`显示` 逻辑型；语义逐字引用 —— 参数注释 `为真显示浏览器，为假隐藏浏览器`（`FBroLib.wsv:1072`），底层 `FBroHsBrowserHost_ShowWindows(m_class,@<显示隐藏>)`（`:1074`）。

**建议形态**：单个 `browser_show_window`，参数 `visible`(boolean, 必填)，映射 `visible → 显示隐藏`（与 `browser_set_focus` 的单布尔参数风格一致：`src\MCP_Server.wsv:9600` + `MCP_Server_Core.wsv:1646-1662`）。

**必须警示的两点**：
1. **本项目没有别的 UI**：隐藏浏览器窗口 = 用户看不到任何东西（程序仍是控制台进程在跑），必须在工具描述与返回消息中警示，并提供对称的「显示」路径。
2. **不要**用 `browser_set_window_style {type:-16}` 清 `WS_VISIBLE` 来替代 —— 项目源码自己已写明该路径危险且不等价（`src\MCP_Server_System.wsv:87`：`"style 不能省略 | 省略会被当作 0 而清掉窗口样式的全部位(含 WS_VISIBLE, 可能使窗口不可见/不可用) | 建议先用 browser_get_window_style 读取当前值, 按位修改后再传回"`）。写 `GWL_STYLE` 位**不等于** `ShowWindow`，可见性变更不可靠。

**先例缺口（诚实说明）**：`显示隐藏窗口` 在**整个 `资料\例子\` 语料库中 0 处调用**（正则 `显示隐藏窗口` 全量检索，仅命中类库定义本身 `FBroLib.wsv:1071`）。因此该工具将是**首次使用**，无官方调用样本可模仿（`移动窗口`、`置自动调整大小` 都有样本，见 5.1/5.2）。

---

## 6. 静态无法确定的事项 + 建议的实测实验

### 6.1 静态未定项（明确列出）

| # | 未定事项 | 为什么静态定不了 |
|---|---|---|
| U1 | **`FBroHs*` 宿主函数的精确 C++ 原型**（参数类型/顺序/返回值） | 类库资料只发 8 个 `.wsv`，**无任何 `.h/.hpp/.cpp/.lib`**；全盘搜索 `*FBro*.h` 仅命中 Volcano 生成头。签名只能由调用点反推（第 2 节），本报告已标注为「反推」 |
| U2 | **`置自动调整大小` 的最小/最大「高度 vs 宽度」到底哪个在前** | 声明顺序是高在前（`FBroLib.wsv:1040-1043`），CEF 的 `CefSize` 是宽在前；官方两处样本都传对称值 `(0,0,10000,10000)`（`main2.wsv:713`、`main21.wsv:613`），**无法消歧** |
| U3 | `取窗口句柄()` 返回的**是顶层 HWND 还是 CEF 内部子 HWND** | 类库只转发 `GetWindowHandle`（`FBroLib.wsv:820`），无任何说明其窗口层级；先前记录的 `parent_hwnd == 0`（`_audit\_probe_result.json:1034` 等）**只是旁证**，未做层级判定实验 |
| U4 | `移动窗口` 在**顶层 CEF 窗口**上是否真的生效（尤其 `是否重画=假` 时是否会不重绘而看起来没动） | 类库无返回值、无错误码，宿主函数语义不可见；项目从未调用过（见 U6） |
| U5 | `置自动调整大小` 在本架构（无宿主容器改尺寸）下**是否有可观察效果** | CEF 语义依赖「宿主尺寸变化 → `OnAutoResize` 通知」；本项目无宿主，静态无法判断该开关是否变成 no-op |
| U6 | 这三个方法**是否已从类库生成到可执行体** | 本项目是「按引用生成」的：生成的 `vpkg_FBroLib.cpp` 里**只有被引用方法的方法体**。已核实（win32 与 x64 两份一致）：存在 `rg_ZhiChuangKouShuXing`/`rg_QuChuangKouShuXing`（`generated-cpp\release-win32\vpkg_FBroLib.cpp:488-496`）、`rg_QuFuChuangKouGouBing`（`:477-481`）、`rg_ZhiFuChuangKou`（`:483-486`）、`GetWindowHandle`（`:340`）；**不存在** `rg_YiDongChuangKou`（移动窗口）、`rg_XianShiYinCangChuangKou`（显示隐藏窗口）、`rg_ZhiZiDongTiaoZhengDaXiao`（置自动调整大小）—— 正则 `rg_YiDongChuangKou|rg_XianShiYinCangChuangKou|rg_ZhiZiDongTiaoZhengDaXiao|MoveWindow|SetAutoResizeEnabled|ShowWindows` 在 `generated-cpp\` 全目录 **0 命中这三个方法**。生成头同样只声明了 `void rg_ZhiChuangKouShuXing (INT, INT);` / `INT rg_QuChuangKouShuXing (INT);`（`generated-cpp\release-win32\vcls_rg_class_FBrowser_LiuLanQi.h:70-71`）。**结论：这三个方法目前是「纯未使用」，从未进入过任何构建产物；首次接线后必须重编译才能验证** |
| U7 | 窗口是否本就**可被用户拖动/缩放**（`WS_THICKFRAME` 等） | `src\main.wsv:203-209` 只设了 `父窗口句柄/横坐标/纵坐标/宽度/高度`，**从未设 `风格`/`额外风格`**（`FBrowser_窗口信息` 有这两个字段，`FBroDataType.wsv:160/158`），故实际风格位由 CEF 默认值决定；只能运行时用现有工具回读 |
| U8 | `移动窗口` 的 `是否重画` 参数语义 | 类库无注释；方法体内留有开发备注 `// 后面还有离屏渲染未添加`（`FBroLib.wsv:1067`），暗示该包装**只处理窗口渲染路径、未处理离屏渲染**。本项目正是窗口渲染（非 OSR），故该备注对项目**有利**，但不足以证明参数语义 |

### 6.2 建议的实测实验（供验证方执行；本报告不做任何「已验证」声明）

**E1 — 基线采集（零风险，先做）**
调用：`browser_get_window_handle`、`browser_window_info`、`browser_get_window_style {type:-16}`、`browser_get_window_style {type:-20}`、`browser_status`。
测量：记下 `hwnd` 与 `GWL_STYLE`/`GWL_EXSTYLE` 原始值（**先存下来**，因为 E6 之类实验若弄坏样式需要还原）。
目的：为 U7 提供基线，并拿到后续实验要用的 HWND。

**E2 — HWND 层级判定（解 U3；用外部 Win32，不依赖类库）**
对 E1 拿到的 HWND 外部调用 `GetAncestor(hwnd, GA_ROOT)` 与 `GetParent(hwnd)`：
若 `GA_ROOT` 结果 == `hwnd` 且 `GetParent(hwnd) == 0` → 该 HWND 就是顶层窗口，U3 判定为「顶层」；
若不等 / `GetParent != 0` → 它是子窗口，`browser_move_window` 移动的将是子窗口（届时才需要 `GetAncestor` 方案）。
同时外部 `IsWindowVisible(hwnd)` 记录基线可见性（供 E5 用）。
**为什么必须外部测**：类库**没有**任何窗口矩形/层级读取 API（第 1.3 节），`browser_window_info` 只给句柄不给层级。

**E3 — auto-resize 宽高顺序消歧（解 U2）**
步骤：① 用**非对称**值调用 `browser_set_auto_resize {enabled:true, min_width:400, min_height:200, max_width:1600, max_height:800}`；② 再用 `browser_move_window` 把窗口设到**两个维度都低于下限**，例如 `{x:100,y:100,width:200,height:100}`；③ 外部测量最终窗口矩形。
判读：若最终宽度被抬到 400、高度抬到 200 → 映射为「宽在前」；若宽度 200、高度 100 未被约束或约束方向与预期相反 → 说明实参被对调，需要在项目侧交换映射。
**注意**：这是唯一能决定性判定的做法；用对称值（`0,0,10000,10000`，官方例程的做法）**永远测不出来**。

**E4 — auto-resize 是否真的有效（解 U5）**
在 `enabled:true` 与 `enabled:false` 两种状态下，各做一次相同的 `browser_move_window` 改尺寸，外部对比窗口矩形是否被 min/max 约束。
若两种状态行为完全相同 → 该开关在本架构下无实际作用，工具应改为如实说明（而不是宣称「支持自动调整」）。

**E5 — 显示/隐藏（验证 5.3 建议）**
① 外部记 `IsWindowVisible(hwnd)`；② 调 `browser_show_window {visible:false}`；③ 外部复查 `IsWindowVisible` 与（用 `browser_screenshot`）页面是否仍在渲染；④ 调 `{visible:true}` 并复查恢复。
**风险提示**：隐藏后本程序**没有任何其他可见 UI**，需确保「显示」路径可用（例如通过 HTTP 接口或 stdio 调用），否则会把自己锁死。

**E6 — 移动是否生效 + 重画语义（解 U4/U8）**
`browser_move_window {x:120,y:120,width:900,height:700,repaint:true}` → 外部 `GetWindowRect` 比对；再以 `repaint:false` 重复一次。
判读：`repaint` 只应影响重绘，不应影响最终矩形；若 `repaint:false` 导致矩形不变，则该参数语义与直觉不同，需在工具描述中说明。

**E7 — 编译验证（解 U6）**
首次接线后必须重新编译并确认 `generated-cpp\**\vpkg_FBroLib.cpp` 中**新出现** `rg_YiDongChuangKou` / `rg_XianShiYinCangChuangKou` / `rg_ZhiZiDongTiaoZhengDaXiao` 方法体（当前三者在生成产物中 0 命中，见 U6）。**未出现即说明类库调用没被真正生成**，工具会退化成静默 no-op。

**E8 — 进程/窗口生命周期边界**
浏览器可能被关闭后重建（`src\main.wsv:162-171`：`如果 (浏览器容器.需要重建浏览器)` → 重建后 `待创建URL`），说明 HWND 会变。实测应覆盖「`browser_shutdown` → 重新 `browser_create` → 再调窗口工具」，确认工具在重建后仍作用于**新**窗口（而不是缓存的旧句柄）。

---

## 7. 一页速查

| 想做的事 | 类库调用（声明类 `类_FBrowser_浏览器`） | file:line | 参数顺序 |
|---|---|---|---|
| 移动 + 缩放 | `移动窗口` | `FBroLib.wsv:1058-1069` | 左边, 顶边, 宽度, 高度, 是否重画(默认假) |
| 显示 / 隐藏 | `显示隐藏窗口` | `FBroLib.wsv:1071-1076` | 显示隐藏(真=显示) |
| 自动尺寸跟随 | `置自动调整大小` | `FBroLib.wsv:1038-1048` | 启用, 最小高, 最小宽, 最大高, 最大宽 |
| 取窗口句柄 | `取窗口句柄` | `FBroLib.wsv:817-822` | 无参 → 变整数 |
| 取父窗口句柄 | `取父窗口句柄` | `FBroLib.wsv:1078-1083` | 无参 → 变整数（本项目实测为 0） |
| 改父窗口（0=桌面） | `置父窗口` | `FBroLib.wsv:1085-1090` | 父窗口句柄 |
| 读写窗口风格 | `置窗口属性` / `取窗口属性` | `FBroLib.wsv:1092-1098` / `1100-1105` | 风格类型(GWL索引), 风格 |
| HWND → 浏览器 | `FBrowser_浏览器_通过窗口句柄取浏览器`（静态） | `FBroLib.wsv:494-499` | 窗口句柄 |

**唯一可照抄的项目样板**：`browser_set_window_style`（`src\MCP_Server_System.wsv:71-93`）。
**唯一该复用的 helper**：`MCP命令服务器.取主浏览器 ()`（`src\MCP_Server.wsv:7796`）。
**未找到、不得臆造**：`置窗口位置`、`置窗口大小`、`取窗口矩形`、`取客户区`、`取顶层窗口句柄`、`最小化窗口`、`最大化窗口`。
