# r100 静态审计 —— `browser_context_menu` 实施前 API 面清单

- 生成方式：**纯静态读取**。本轮**未编译、未调用任何 MCP 工具、未发起 HTTP 请求、未启动/重启/结束任何进程、未修改任何已存在文件**。
- ROOT = `C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp`
- 类库基准 = `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\`（8 个 `*.wsv`）
- 另有 3 份**运行时随类库一同安装、与本裁定直接相关**的只读资料（本轮首次引入，见 §3）：
  - `E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\src\env\FBrowserCEF3lib\include\cef_context_menu_handler.h`
  - `E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\src\env\FBrowserCEF3lib\include\cef_menu_model.h`
  - `E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\src\env\FBrowserCEF3lib\include\cef_types.h`
  （FBrowser 模块的 `.vgrp` 由 `AI-Fbowser-Mcp.vprj:32` 指向 `*plugins\vprj_win\classlib\sys\FBrowser\FBrowserSimple.vgrp`，故上述 `include` 目录就是本类库的编译期 CEF 头，属类库发行物。）

## 证据强度分级（本报告全文使用）

| 级别 | 含义 |
|---|---|
| `【静态-逐字】` | 直接引用了磁盘上的文件原文（行号已核对） |
| `【静态-推导】` | 由逐字原文经明确推理得出，推理步骤已写出 |
| `【未知】` | 静态判不出，需真机验证 |

**本报告不含任何"已验证/已测试"结论。** 唯一一处已由主代理实证的事实（`event_menu_enable` + CDP 右键后事件缓冲出现 `context_menu_opening`/`context_menu_run`）在本报告中按"已由主代理实证"标注，不作为我的证据。

---

# §1 `类_FBrowser_菜单模式` 全方法清单

定义位置：`FBroLib.wsv:3288` 起，类体到 `FBroLib.wsv:3624` 结束。

```
FBroLib.wsv:3288: 类 类_FBrowser_菜单模式 <公开 注释 = "CefMenuModel" @输出名 = "FBroMenuModel">
FBroLib.wsv:3624: }
```
（`_classlib_gap_verify_r98.md:58` 也独立记有"`类_FBrowser_菜单模式` 在 3288-3624"，与本轮一致。）

**方法总数 = 36。**`【静态-逐字】`
其中 `是否为空` / `置空` 是火山侧基础设施（非 CEF 方法），其余 **34 个**一对一映射到 CEF `CefMenuModel` 方法。

## 1.1 逐方法全表（方法名 + 完整参数表原文）

参数表**逐字照抄**，含 `@默认值` / `注释` / `@禁止流程检查`。返回值列取自 `类型 = xxx`，无 `类型` 者即无返回值。

| # | 行号 | 方法名 | 返回值 | 参数表原文（逐字） |
|---|---|---|---|---|
| 1 | 3303 | `是否为空` | 逻辑型 | （无参数）`<公开 类型 = 逻辑型 @禁止流程检查 = 真>` |
| 2 | 3308 | `置空` | — | （无参数）`<公开 注释 = "手动置空当前类包含的cef类指针，置空后该类将无法使用，如没有其他引用将自动释放cef类指针的资源数据">` |
| 3 | 3313 | `清空菜单` | 逻辑型 | （无参数）`注释 = "英文名：Clear"` → `FBroHsMenuModel_Clear` |
| 4 | 3319 | `取数量` | 整数 | （无参数）`注释 = "英文名：GetCount"` → `FBroHsMenuModel_GetCount` |
| 5 | 3325 | `添加分隔栏` | 逻辑型 | （无参数）`注释 = "英文名：AddSeparator"` → `FBroHsMenuModel_AddSeparator` |
| 6 | 3331 | `添加菜单` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 标签名 <类型 = 文本型>` |
| 7 | 3339 | `添加Check菜单` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 标签名 <类型 = 文本型>` |
| 8 | 3347 | `添加Radio菜单` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 标签名 <类型 = 文本型>`<br>`参数 群ID <类型 = 整数>` |
| 9 | 3356 | `添加子菜单` | 类_FBrowser_菜单模式 | `参数 命令ID <类型 = 整数>`<br>`参数 标签名 <类型 = 文本型>` |
| 10 | 3364 | `删除菜单` | 逻辑型 | `参数 命令ID <类型 = 整数>` |
| 11 | 3371 | `取菜单标签` | 文本型 | （无参数）`注释 = "英文名：GetMisspelledWord"` ← **注释英文名错标**，实际实现调 `FBroHsMenuModel_GetLable`（应为 `GetLabel`） |
| 12 | 3378 | `置菜单标签` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 标签名 <类型 = 文本型>` |
| 13 | 3386 | `取菜单类型` | 整数 | `参数 命令ID <类型 = 整数>` |
| 14 | 3392 | `取分组ID` | 整数 | `参数 命令ID <类型 = 整数>`，`注释 = "英文名：GetType"` ← **注释英文名错标**，实际调 `FBroHsMenuModel_GetGroup` |
| 15 | 3398 | `取子菜单` | 类_FBrowser_菜单模式 | `参数 命令ID <类型 = 整数>`，`注释 = "英文名：AddSubMenu"` ← **注释英文名错标**，实际调 `FBroHsMenuModel_GetSubMenu` |
| 16 | 3405 | `是否可见` | 逻辑型 | `参数 命令ID <类型 = 整数>`，`注释 = "英文名：IsVisable"`（拼写错误，CEF 为 `IsVisible`） |
| 17 | 3411 | `置可见状态` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 可见 <类型 = 逻辑型>` |
| 18 | 3418 | `是否禁止` | 逻辑型 | `参数 命令ID <类型 = 整数>`，`注释 = "英文名：IsEnable"`（应为 `IsEnabled`） |
| 19 | 3424 | `置禁止状态` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 禁止 <类型 = 逻辑型>` |
| 20 | 3431 | `是否选中` | 逻辑型 | `参数 命令ID <类型 = 整数>` |
| 21 | 3437 | `选中状态` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 选中 <类型 = 逻辑型>`，`注释 = "英文名：SetCheck"`（应为 `SetChecked`） |
| 22 | 3444 | `选中状态_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>`<br>`参数 选中 <类型 = 逻辑型>`，`注释 = "英文名：SetCheckedAt"` |
| 23 | 3451 | `存在快捷键` | 逻辑型 | `参数 命令ID <类型 = 整数>`，`注释 = "英文名："`（空） |
| 24 | 3457 | `存在快捷键_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>` |
| 25 | 3464 | `设置快捷键` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 键代码 <类型 = 整数 注释 = "key_code">`<br>`参数 是否按下shift <类型 = 逻辑型 注释 = "shift_pressed" @默认值 = 假>`<br>`参数 是否按下ctrl <类型 = 逻辑型 注释 = "ctrl_pressed" @默认值 = 假>`<br>`参数 是否按下alt <类型 = 逻辑型 注释 = "alt_pressed" @默认值 = 假>` |
| 26 | 3474 | `设置快捷键_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>`<br>其余同 #25（`键代码` / `是否按下shift` / `是否按下ctrl` / `是否按下alt`，后三者 `@默认值 = 假`） |
| 27 | 3484 | `移除快捷键` | 逻辑型 | `参数 命令ID <类型 = 整数>`，`注释 = "英文名："`（空） |
| 28 | 3490 | `移除快捷键_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>`，`注释 = "英文名："`（空） |
| 29 | 3496 | `取快捷键` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 键代码 <类型 = 整数类 注释 = "key_code，返回数据">`<br>`参数 返回是否按下shift值 <类型 = 逻辑型类 注释 = "shift_pressed，返回数据" "">`<br>`参数 返回是否按下ctrl值 <类型 = 逻辑型类 注释 = "ctrl_pressed，返回数据" "">`<br>`参数 返回是否按下alt值 <类型 = 逻辑型类 注释 = "alt_pressed，返回数据" "">` |
| 30 | 3517 | `取快捷键_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>`<br>其余同 #29（`键代码` / `返回是否按下shift值` / `返回是否按下ctrl值` / `返回是否按下alt值`，三个"类"参数为出参） |
| 31 | 3538 | `置颜色` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 颜色类型 <类型 = 整数 注释 = "color_type 参考：菜单颜色类型.">`<br>`参数 A <类型 = 整数 @默认值 = 0>`<br>`参数 R <类型 = 整数 @默认值 = 0>`<br>`参数 G <类型 = 整数 @默认值 = 0>`<br>`参数 B <类型 = 整数 @默认值 = 0>` |
| 32 | 3550 | `置颜色_索引` | 逻辑型 | `参数 索引ID <类型 = 整数 注释 = "索引为-1为设置默认颜色">`<br>`参数 颜色类型 <类型 = 整数 注释 = "color_type 参考：菜单颜色类型.">`<br>`参数 A / R / G / B <类型 = 整数 @默认值 = 0>`（各 `@默认值 = 0`） |
| 33 | 3563 | `取颜色` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 颜色类型 <类型 = 整数 注释 = "color_type 参考：菜单颜色类型.">`<br>`参数 返回A值 <类型 = 整数类>`<br>`参数 返回R值 <类型 = 整数类>`<br>`参数 返回G值 <类型 = 整数类>`<br>`参数 返回B值 <类型 = 整数类>` |
| 34 | 3586 | `取颜色_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>`<br>`参数 颜色类型 <类型 = 整数 注释 = "color_type 参考：菜单颜色类型.">`<br>`参数 返回A值 / 返回R值 / 返回G值 / 返回B值 <类型 = 整数类>` |
| 35 | 3609 | `置字体` | 逻辑型 | `参数 命令ID <类型 = 整数>`<br>`参数 字体清单 <类型 = 文本型 注释 = "\"Arial, Helvetica, Bold Italic 14px\"">`，方法级 `注释 = "待验证"` |
| 36 | 3616 | `置字体_索引` | 逻辑型 | `参数 索引ID <类型 = 整数>`<br>`参数 字体清单 <类型 = 文本型 注释 = "\"Arial, Helvetica, Bold Italic 14px\"">`，方法级 `注释 = "待验证"` |

## 1.2 "同方法多重重载 / `_索引` 变体"的精确区分

类库里**没有任何火山意义上的重载**（同名方法只有一个）。所谓"变体"是**CEF 的 `At(index)` 家族**被单独封装成带 `_索引` 后缀的独立方法，**参数表不同（第一个参数从 `命令ID` 换成 `索引ID`）**。

`_索引` 变体共 **8 个**（第 1 参数为 `索引ID <类型 = 整数>`）：

| 后缀变体 | 行号 | 对应的 CEF 方法 | 该 CEF 方法的 `命令ID` 版是否也被封装 |
|---|---|---|---|
| `选中状态_索引` | 3444 | `SetCheckedAt` | 是 → `选中状态`(3437) = `SetChecked` |
| `存在快捷键_索引` | 3457 | `HasAcceleratorAt` | 是 → `存在快捷键`(3451) = `HasAccelerator` |
| `设置快捷键_索引` | 3474 | `SetAcceleratorAt` | 是 → `设置快捷键`(3464) = `SetAccelerator` |
| `移除快捷键_索引` | 3490 | `RemoveAcceleratorAt` | 是 → `移除快捷键`(3484) = `RemoveAccelerator` |
| `取快捷键_索引` | 3517 | `GetAcceleratorAt` | 是 → `取快捷键`(3496) = `GetAccelerator` |
| `置颜色_索引` | 3550 | `SetColorAt` | 是 → `置颜色`(3538) = `SetColor` |
| `取颜色_索引` | 3586 | `GetColorAt` | 是 → `取颜色`(3563) = `GetColor` |
| `置字体_索引` | 3616 | `SetFontListAt` | 是 → `置字体`(3609) = `SetFontList` |

**`添加*` 系列没有任何 `_索引` 变体**（CEF 有 `InsertItemAt`/`InsertSubMenuAt`/`InsertSeparatorAt`/`InsertCheckItemAt`/`InsertRadioItemAt`，类库**一个都没封装**）。因此 `browser_context_menu` **没有"在指定位置插入"的能力**，只能"追加"。`【静态-逐字】`

## 1.3 类库未封装的 CEF 方法（22 个）—— 设计时必须避开的"想当然"

对 `cef_menu_model.h:66-488` 的 56 个 `virtual` 方法与类库实际调用的 34 个 `FBroHsMenuModel_*` 做了集合差（注意类库的 messenger 名有拼写偏差：`GetLable`/`SetLable`/`IsVisable`/`SetVisable`/`IsEnable`/`SetEnable`/`SetCheck`/`GetGroup` 分别对应 CEF 的 `GetLabel`/`SetLabel`/`IsVisible`/`SetVisible`/`IsEnabled`/`SetEnabled`/`SetChecked`/`GetGroupId`，已按语义归并）：

`【静态-逐字 + 集合差推导】`

| 未封装 CEF 方法 | 对 `browser_context_menu` 的影响 |
|---|---|
| `IsSubMenu` | 无法判断某子菜单对象本身是不是子菜单 |
| `InsertSeparatorAt` / `InsertItemAt` / `InsertCheckItemAt` / `InsertRadioItemAt` / `InsertSubMenuAt` | **无插入能力**，只能尾部追加（见 1.2） |
| `RemoveAt` | 只能按 `命令ID` 删（`删除菜单`），不能按索引删 |
| `GetIndexOf` / `GetCommandIdAt` / `SetCommandIdAt` | 无法做"命令ID ↔ 索引"换算，也无法改已存在项的 ID |
| `GetLabelAt` / `SetLabelAt` / `GetTypeAt` / `GetGroupIdAt` / `SetGroupIdAt` / `GetSubMenuAt` / `IsVisibleAt` / `SetVisibleAt` / `IsEnabledAt` / `SetEnabledAt` / `IsCheckedAt` | 除 `SetCheckedAt` 外，**索引版读写全部缺失**（读侧尤其致命：无法枚举菜单全貌） |
| `SetGroupId` | 无法改分组（`取分组ID` 只有读，没有写） |

**结论**：类库把"改"做得比"读"全。若工具要提供 `query_tree`（回读菜单树），**缺少 `GetCommandIdAt`/`GetLabelAt`/`GetTypeAt`/`GetSubMenuAt`，无法按索引遍历**——只能由工具侧用自己的规格 JSON 复述，不能从 CEF 侧反查。这一点必须在工具文档中写明，否则 AI 会以为 `query_tree` 是从 CEF 读的真值。

## 1.4 常量类（施加规格时需要的取值域）

| 类 | 位置 | 常量（逐字） |
|---|---|---|
| `菜单类型` | `FBroConst.wsv:208` | `无=0` / `页面=1` / `框架=2` / `链接=4` / `媒体=8` / `文本=16` / `编辑框=32`（`注释 = "多种类型叠加位或"`） |
| `菜单颜色类型` | `FBroConst.wsv:565` | `文本=0` / `文本_激活=1` / `文本_快捷键=2` / `文本_快捷键_激活=3` / `背景=4` / `背景_激活=5` / `计数=6` |

自定义命令ID 的合法区间 `【静态-逐字】`：`cef_types.h:1730-1731`
```
  MENU_ID_USER_FIRST = 26500,
  MENU_ID_USER_LAST = 28500,
```
同文件 `:1727-1728`：
```
  // All user-defined menu IDs should come between MENU_ID_USER_FIRST and
  // MENU_ID_USER_LAST to avoid overlapping the Chromium and CEF ID ranges
```
官方例程也遵守该区间：`资料\例子\FB浏览器模块例子\browser_event11.wsv:157` 用 `26500`。
**类库与项目 `src` 都没有做这个校验** → 校验必须落在新工具里。

## 1.5 类库官方支持的标准用法（唯一 canonical 形态）

`资料\例子\FB浏览器模块例子\browser_event.wsv:121-135`（`【静态-逐字】`）——**全部用法都是"在回调内就地构建"，没有一例是保存对象**：
```
    方法 浏览器_即将打开菜单 <公开 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器>
    参数 框架 <类型 = 类_FBrowser_框架>
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境>
    参数 菜单模式 <类型 = 类_FBrowser_菜单模式>
    {
        调试输出 (取当前语句位置 (), 菜单环境.取类型 ())
        变量 自定义子菜单 <类型 = 类_FBrowser_菜单模式>

        自定义子菜单 = 菜单模式.添加子菜单 (10001, "自定义菜单")
        自定义子菜单.添加菜单 (10002, "打开开发者")
        自定义子菜单.添加菜单 (10003, "检查")


    }
```
同类写法在 `browser_event1.wsv:454` / `browser_event4.wsv:156` / `browser_event7.wsv:100` / `browser_event11.wsv:148` / `browser_event13.wsv:127` / `browser_event28.wsv:104` / `SwEx综合案例\SwEx浏览器原生容器\main.wsv:575` 重复出现，全部一致。**这是支持方给出的"该怎么用"的唯一样板。**

---

# §2 事件 override 逐字引出

## 2.1 类库侧事件定义（`FBroEventControl.wsv`）

`浏览器_即将打开菜单` 的 CEF 绑定行 `FBroEventControl.wsv:1088`（逐字，单行）：
```
    # void @sn<current_class>::OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,CefRefPtr<CefFrame> frame,CefRefPtr<CefContextMenuParams> params,CefRefPtr<CefMenuModel> model){@<浏览器_即将打开菜单>(@dt<类_FBrowser_浏览器>(browser),@dt<类_FBrowser_框架>(frame),@dt<类_FBrowser_菜单环境>(params),@dt<类_FBrowser_菜单模式>(model));};
```

事件声明 `FBroEventControl.wsv:1090-1097`（逐字）：
```
    方法 浏览器_即将打开菜单 <公开 注释 = "英文名：OnBeforeContextMenu" @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器>
    参数 框架 <类型 = 类_FBrowser_框架>
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境>
    参数 菜单模式 <类型 = 类_FBrowser_菜单模式>
    {

    }
```

### 同族三个事件（全部存在，逐字）

`浏览器_菜单被调用`（`FBroEventControl.wsv:1109-1117`）——CEF `RunContextMenu`：
```
    方法 浏览器_菜单被调用 <公开 类型 = 逻辑型 注释 = "英文名：RunContextMenu" 返回值注释 = "返回真阻止当前操作，返回假继续" @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器>
    参数 框架 <类型 = 类_FBrowser_框架>
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境>
    参数 菜单模式 <类型 = 类_FBrowser_菜单模式>
    参数 运行命令菜单回调 <类型 = 类_FBrowser_运行命令菜单回调>
    {
        返回 (假)
    }
```
`FBroEventControl.wsv:1101-1107`（CEF 绑定，逐字）：
```
    # bool @sn<current_class>::RunContextMenu(CefRefPtr<CefBrowser> browser,
    #  CefRefPtr<CefFrame> frame,
    #  CefRefPtr<CefContextMenuParams> params,
    #  CefRefPtr<CefMenuModel> model,
    #  CefRefPtr<CefRunContextMenuCallback> callback) {
    #  return @<浏览器_菜单被调用>(@dt<类_FBrowser_浏览器>(browser),@dt<类_FBrowser_框架>(frame),@dt<类_FBrowser_菜单环境>(params),@dt<类_FBrowser_菜单模式>(model),@dt<类_FBrowser_运行命令菜单回调>(callback));
    #  };
```

`浏览器_菜单被点击`（`FBroEventControl.wsv:1127-1135`）——CEF `OnContextMenuCommand`：
```
    方法 浏览器_菜单被点击 <公开 类型 = 逻辑型 注释 = "英文名：OnContextMenuCommand" 返回值注释 = "返回真阻止当前操作，返回假继续" @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器>
    参数 框架 <类型 = 类_FBrowser_框架>
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境>
    参数 命令ID <类型 = 整数 注释 = "command_id">
    参数 事件标识 <类型 = 整数 注释 = "参考：事件标识.xxx 用位或判断">
    {
        返回 (假)
    }
```

`浏览器_菜单被关闭`（`FBroEventControl.wsv:1142-1145`）——CEF `OnContextMenuDismissed`：
```
    方法 浏览器_菜单被关闭 <公开 注释 = "英文名：OnContextMenuDismissed" @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器>
    参数 框架 <类型 = 类_FBrowser_框架 "">
```
（注意：`框架` 参数行在类库源码里带 `""`，无参数注释；类体此处**没有方法体 `{ }`**。）

## 2.2 项目侧 override（`ROOT\src\MCP_BrowserEvents.wsv`）

`浏览器_即将打开菜单` override，`MCP_BrowserEvents.wsv:2658-2668`，**逐字**：
```
    方法 浏览器_即将打开菜单 <公开 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境 @输出名 = "MenuParams">
    参数 菜单模式 <类型 = 类_FBrowser_菜单模式 @输出名 = "MenuModel">
    {
        如果 (MCP命令服务器.是否监控菜单事件)
        {
            记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), "")
        }
    }
```
**方法体现在做的全部事情**（`MCP_BrowserEvents.wsv:2664-2667`）：只有一句"若 `是否监控菜单事件` 为真则写一条空数据的事件日志"。**形参 `菜单模式`（:2662）与 `菜单环境`（:2661）在整个方法体内零次出现。**`【静态-逐字】`

`浏览器_菜单被调用` override，`MCP_BrowserEvents.wsv:2670-2683`，逐字：
```
    方法 浏览器_菜单被调用 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境 @输出名 = "MenuParams">
    参数 菜单模式 <类型 = 类_FBrowser_菜单模式 @输出名 = "MenuModel">
    参数 运行命令菜单回调 <类型 = 类_FBrowser_运行命令菜单回调 @输出名 = "RunMenuCallback">
    {
        如果 (MCP命令服务器.是否监控菜单事件)
        {
            记录监控事件 (真, "context_menu_run", 浏览器.取ID (), "")
        }
        // 逻辑型事件: 返回假 = 不阻止浏览器默认行为
        返回 (假)
    }
```

`浏览器_菜单被点击` override，`MCP_BrowserEvents.wsv:2685-2702`，逐字：
```
    方法 浏览器_菜单被点击 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境 @输出名 = "MenuParams">
    参数 命令ID <类型 = 整数 @输出名 = "CommandID">
    参数 事件标识 <类型 = 整数 @输出名 = "EventFlags">
    {
        如果 (MCP命令服务器.是否监控菜单事件)
        {
            变量 事件数据 <类型 = YYJSON对象类>
            事件数据.创建自文本 ("{}")
            事件数据.加入文本成员 ("command_id", 到文本 (命令ID))
            事件数据.加入文本成员 ("event_flags", 到文本 (事件标识))
            记录监控事件 (真, "context_menu_command", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))
        }
        // 逻辑型事件: 返回假 = 不阻止浏览器默认行为
        返回 (假)
    }
```

`浏览器_菜单被关闭` override，`MCP_BrowserEvents.wsv:2704-2712`，逐字：
```
    方法 浏览器_菜单被关闭 <公开 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">
    {
        如果 (MCP命令服务器.是否监控菜单事件)
        {
            记录监控事件 (真, "context_menu_dismissed", 浏览器.取ID (), "")
        }
    }
```

**三个同族 override 全部存在，且全部只记录。**`【静态-逐字】`（与 `_audit/_classlib_gap_recheck.md:105` 的记载一致。）

## 2.3 该项目 override 在生成 C++ 中的真实形态（证明"形参是引用/副本"的载体）

`_int\AI-Fbowser-Mcp\release\x64\project\vpkg_MCP_BrowserEvents.cpp:1038-1044`（逐字）：
```
void MCPBrowserEvent::rg_LiuLanQi_JiJiangDaKaiCaiChan (rg_FBrowser_LiuLanQi::rg_class_FBrowser_LiuLanQi& Browser, rg_FBrowser_LiuLanQi::FBroFrame& Frame, rg_FBrowser_LiuLanQi::FBroContextMenuParams& MenuParams, rg_FBrowser_LiuLanQi::FBroMenuModel& MenuModel)
{
    if (MCPCommandServer::IsMonitorContextMenu)
    {
        RecordMonitorEvent (TRUE, _CT2 (_T ("context_menu_opening")), Browser.rg_QuID (), _CT2 (_T ("")));
    }
}
```
派发侧 `generated-cpp\release-win32\vpkg_FBroEventControl.cpp:665`（逐字）：
```
void rg_class_FBrowser_llqshj::OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,CefRefPtr<CefFrame> frame,CefRefPtr<CefContextMenuParams> params,CefRefPtr<CefMenuModel> model){rg_LiuLanQi_JiJiangDaKaiCaiChan(rg_FBrowser_LiuLanQi::rg_class_FBrowser_LiuLanQi(browser),rg_FBrowser_LiuLanQi::FBroFrame(frame),rg_FBrowser_LiuLanQi::FBroContextMenuParams(params),rg_FBrowser_LiuLanQi::FBroMenuModel(model));};
```
**关键读法**：`FBroMenuModel(model)` 是**在回调栈上按值构造的临时包装对象**，其成员 `CefRefPtr<CefMenuModel> m_class` 由 `model` 拷贝而来（`CefRefPtr` 拷贝 = `AddRef`）。火山类对象在生成代码里以**引用**跨方法传递（`FBroMenuModel&`），因此项目 override 里的 `菜单模式` 引用的是这个临时包装对象。

---

# §3 【最关键一问】`菜单模式` 在回调返回之后还能不能用？

## 3.1 结论

# **B —— 只能在回调期间使用；延迟调用不安全（延迟调用有风险）**

裁定：**B**。`【静态-逐字】`（依据为上游 CEF 官方契约）+ `【静态-推导】`（类库实现细节）。

并且我明确标注：**B 中的"崩溃"在本轮无法证实**；能证实的是"**官方契约明确禁止**"。详见 3.4 的反证与 3.5 的定案办法。

## 3.2 据以判断的逐字源码行

### 证据 1（决定性）：CEF 头文件明确写"不要在回调之外保留 `model` 引用"

`E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\src\env\FBrowserCEF3lib\include\cef_context_menu_handler.h:98-109`：
```
  ///
  /// Called before a context menu is displayed. |params| provides information
  /// about the context menu state. |model| initially contains the default
  /// context menu. The |model| can be cleared to show no context menu or
  /// modified to show a custom menu. Do not keep references to |params| or
  /// |model| outside of this callback.
  ///
  /*--cef()--*/
  virtual void OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
                                   CefRefPtr<CefFrame> frame,
                                   CefRefPtr<CefContextMenuParams> params,
                                   CefRefPtr<CefMenuModel> model) {}
```
**逐字关键句（`:102-103`）：`Do not keep references to |params| or |model| outside of this callback.`**

同一约束在 `RunContextMenu`（即本项目 `浏览器_菜单被调用`）里**重复了一遍**，`cef_context_menu_handler.h:111-126`：
```
  ///
  /// Called to allow custom display of the context menu. |params| provides
  /// information about the context menu state. |model| contains the context
  /// menu model resulting from OnBeforeContextMenu. For custom display return
  /// true and execute |callback| either synchronously or asynchronously with
  /// the selected command ID. For default display return false. Do not keep
  /// references to |params| or |model| outside of this callback.
  ///
  /*--cef()--*/
  virtual bool RunContextMenu(CefRefPtr<CefBrowser> browser,
                              CefRefPtr<CefFrame> frame,
                              CefRefPtr<CefContextMenuParams> params,
                              CefRefPtr<CefMenuModel> model,
                              CefRefPtr<CefRunContextMenuCallback> callback) {
    return false;
  }
```
**逐字关键句（`:116-117`）：`Do not keep references to |params| or |model| outside of this callback.`**

### 证据 2：CEF 明确声明这些方法**只能在浏览器进程 UI 线程**访问

`cef_menu_model.h:44-51`：
```
///
/// Supports creation and modification of menus. See cef_menu_id_t for the
/// command ids that have default implementations. All user-defined command ids
/// should be between MENU_ID_USER_FIRST and MENU_ID_USER_LAST. The methods of
/// this class can only be accessed on the browser process the UI thread.
///
/*--cef(source=library)--*/
class CefMenuModel : public virtual CefBaseRefCounted {
```
**逐字关键句（`:48`）：`The methods of this class can only be accessed on the browser process the UI thread.`**

回调线程定义，`cef_context_menu_handler.h:88-93`：
```
///
/// Implement this interface to handle context menu events. The methods of this
/// class will be called on the UI thread.
///
/*--cef(source=client)--*/
class CefContextMenuHandler : public virtual CefBaseRefCounted {
```
**逐字关键句（`:89-90`）：`The methods of this class will be called on the UI thread.`**

### 证据 3（本项目侧）：MCP 工具调用**确实不在** CEF UI 线程上

`ROOT\src\MCP_Stdio.wsv:324`（逐字）：
```
 类 类_MCP_Stdio服务线程 <公开 基础类 = 缓存线程类 @输出名 = "MCPStdioServiceThread">
```
`ROOT\src\MCP_Server_HTTP.wsv:239`（逐字片段）：
```
            // 防止 HTTP/WS/stdio 多线程并发交错写入 工具列表构建缓冲区 导致工具列表JSON损坏
```
→ HTTP/WS/stdio **三条入口均为多线程**，MCP 工具分派发生在非 UI 线程。

**证据 2 + 证据 3 的合成**：`【静态-推导】`若把 `菜单模式` 存成静态字段、由后续任意一次 MCP 工具调用去调 `菜单模式.添加菜单 (...)`，那就是**在非 UI 线程访问 `CefMenuModel`**，直接违反 `cef_menu_model.h:48`。这一条**独立于生命周期问题**就已经足以否决"延迟调用"。

### 证据 4：类库是否给出"副本/仅回调期间有效/是否有效"的说明？——**没有**

| 检查项 | 结果 |
|---|---|
| 类库内是否有 `Do not keep` / `outside of this callback` / `有效范围` / `生命周期` / `仅回调` / `回调期间` 字样？ | **无。** 全 8 个 `*.wsv` grep 该组关键词，唯一命中是 `FBroDataType.wsv:1529` `变量 禁用生命周期事件`（浏览器生命周期开关，与菜单无关）、`FBroValue.wsv:304` / `FBroLib.wsv:2725` 的局部变量名 `临时类`（无关） |
| 该类是否有 `是否有效` 方法？ | **没有。** 只有 `是否为空 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`（`FBroLib.wsv:3303`），实现 `@ return IsEmpty();`，即 `m_class.get () == nullptr` |
| 是否在回调外被置空（自动）？ | **没有任何自动置空。** 只有**手动**置空：`FBroLib.wsv:3308-3311` `方法 置空` / `@ m_class = nullptr;` |
| 是否只是包装 CEF 指针？ | **是。** `FBroLib.wsv:3291-3301` 的内嵌 C++ 段： |

`FBroLib.wsv:3291-3301`（逐字）：
```
    # @begin
    # <> <include>
    # CefRefPtr<CefMenuModel> m_class;
    # inline_ @sn<current_class> (CefRefPtr<CefMenuModel> object) : @sn<current_class> () { m_class = object; }
    # inline_ void @an<_CopySelfFromExtra> (const @sn<current_class>& objCopyFrom) { m_class = objCopyFrom.m_class; }
    # inline_ BOOL @an<_IsSelfEqualExtra> (const @sn<current_class>& objCompare) const { return (m_class.get () == objCompare.m_class.get ()); }
    # inline_ BOOL IsEmpty () const { return m_class.get () == nullptr; }
    # inline_ void Set (CefRefPtr<CefMenuModel> object) { m_class = object; }
    # ~@sn<current_class>(){};
    # <> </include>
    # @end
```
正确性旁证（生成的头文件）= `generated-cpp\release-win32\vcls_FBroMenuModel.h:15-21`（逐字）：
```
    CefRefPtr<CefMenuModel> m_class;
    inline_ FBroMenuModel (CefRefPtr<CefMenuModel> object) : FBroMenuModel () { m_class = object; }
    inline_ void _CopySelfFromExtra (const FBroMenuModel& objCopyFrom) { m_class = objCopyFrom.m_class; }
    inline_ BOOL _IsSelfEqualExtra (const FBroMenuModel& objCompare) const { return (m_class.get () == objCompare.m_class.get ()); }
    inline_ BOOL IsEmpty () const { return m_class.get () == nullptr; }
    inline_ void Set (CefRefPtr<CefMenuModel> object) { m_class = object; }
    ~FBroMenuModel(){};
```
`置空` 的类库注释还反向印证了"包装对象持有资源引用"，`FBroLib.wsv:3308`（逐字）：
```
    方法 置空 <公开 注释 = "手动置空当前类包含的cef类指针，置空后该类将无法使用，如没有其他引用将自动释放cef类指针的资源数据">
```

## 3.3 反证：这一条为什么**不能**升级成"A"

必须诚实记录：`CefRefPtr` 是**引用计数智能指针**，所以从纯 C++ 对象存活角度看——
- `【静态-逐字】` `m_class` 是 `CefRefPtr<CefMenuModel>`（`FBroLib.wsv:3293`），拷贝会 `AddRef`；
- `【静态-推导】` 因此把 `菜单模式` 赋给字段后，**`CefMenuModel` 这个 CEF 对象的引用计数不会归零**，看上去"对象不会立刻析构"。

但 A 依然不成立，因为：
1. `CefRefPtr` 保证的只是**包装器（wrapper）对象**存活，**不保证包装器内部指向的底层菜单模型（Chromium 侧的 `ui::SimpleMenuModel`）存活**。CEF 官方文档（证据 1）正是在这个意义上说"Do not keep references"。`【静态-推导】`
2. `cef_menu_model.h:48`（证据 2）是**线程约束**，与引用计数无关。MCP 侧调用必然跨线程（证据 3）。`【静态-逐字】`
3. 语义上：菜单一旦显示完成，再改模型对**已经显示的菜单**不会有效果；若在 `RunContextMenu` 之前改，则与 CEF UI 线程形成数据竞争。两条路都无收益。`【静态-推导】`
4. **类库自述的官方样板（§1.5，8 个例子文件）没有一例保存对象** —— 支持方的用法范式本身就是"就地用完即弃"。`【静态-逐字】`

## 3.4 为什么不选 C

C 的定义是"静态判不出"。本轮**判得出**：`cef_context_menu_handler.h:102-103` 与 `:116-117` 是**对 `|model|` 的指名禁止**，`cef_menu_model.h:48` 是**对 `CefMenuModel` 的指名线程约束**，两条都在随类库安装的编译期头文件里，逐字可引。所以不是 C。`【静态-逐字】`

**但必须声明两个 `【未知】`**（B 结论不依赖它们，工具设计必须绕开它们）：
1. `【未知】` 延迟调用**究竟会不会立刻崩溃**（`CefRefPtr` 引用计数这一层是否恰好把底层模型也钉住了）。本轮无法证实，也不打算证实——因为即便不崩也是违反契约 + 跨线程，不该做。
2. `【未知】` 在 `浏览器_菜单被调用`（`RunContextMenu`）**回调内**先执行 `运行命令菜单回调.继续(...)` 再改 `菜单模式`，改动是否还生效（`CefRunContextMenuCallback` 的语义，见 `FBroCallback.wsv:281-292` `方法 继续` / `方法 取消`）。

## 3.5 一句话真机定案办法（交给主代理；本轮**未执行**）

> **在 `浏览器_即将打开菜单` 的方法体里加两行探针：① `MCP命令服务器.菜单探针快照 = 菜单模式.取数量 ()`（回调内读，作为基线 N）；② `MCP命令服务器.暂存菜单模式 = 菜单模式`（保存句柄）。再新增一个极小的探针动作 `browser_collect {action:"menu_probe"}`，其实现为 `如果 (暂存菜单模式.是否为空 () == 假) { 返回 到文本(暂存菜单模式.取数量 ()) }`。流程：配置 → 重启进程 → `browser_collect {action:"event_menu_enable"}` → CDP 右键一次（已知会触发 context_menu_opening）→ 再用 `browser_collect {action:"menu_probe"}` 查一次。判读：若返回 N（与回调内基线一致且进程未崩）→ 对象在回调后仍可读，指针层安全（此时仍需面对 `cef_menu_model.h:48` 的跨线程问题，故实现方案不变）；若进程崩溃 → B 被实证；若返回"暂存菜单模式 为空" → 类库/CEF 在回调后释放了引用计数。**

**注意**：该探针必须重启进程才生效（本报告禁止启动进程，故未执行）。且它**最多能证伪 B 的"崩溃"部分，不能推翻 B 作为实施口径**——因为线程约束（证据 2+3）与官方契约（证据 1）是独立成立的。

---

# §4 两套实现方案（只给设计，不写实现代码）

## 4.0 两套方案对 Q3 的依赖

| 方案 | 是否依赖 Q3=A |
|---|---|
| **方案甲**（预置规格 + 回调内施加） | **不依赖**。Q3=B 下**唯一可用**的方案。 |
| **方案乙**（保存句柄 + 即时增删） | **只在 Q3=A 时才有意义**。当前结论 B ⇒ **方案乙不应实施**，仅作为"若 3.5 探针推翻 B 时"的备用设计保留。 |

## 方案甲 —— "预置菜单规格"，事件到达时在回调内一次性施加

### A. 需要新增的工具动作

工具名建议 `browser_context_menu`（`src` 中零命中，无重名：`grep browser_context_menu|browser_menu_build` → `No matches found`）。`【静态-逐字】`

| 动作 | 语义 | 是否碰 CEF |
|---|---|---|
| `set_spec` | 整体下发/覆盖一棵菜单规格树（JSON），写入静态字段 | 否（纯暂存） |
| `get_spec` | 回读当前暂存规格 | 否 |
| `clear_spec` | 清空暂存规格（恢复到 CEF 默认右键菜单） | 否 |
| `enable` / `disable` | 是否启用"事件到达时施加" | 否 |
| `status` | 返回：是否启用、规格是否为空、规格项数、**已施加次数**、上次施加时刻、上次施加的浏览器ID、上次错误、与 `browser_kernel_menu` 的互斥告警 | 否 |
| `apply_now`（可选） | 方案甲下**只能返回"规格已暂存，待下次右键生效"**，不得假装立即生效（禁止假成功） | 否 |
| `set_spec` 的 `one_shot` 子选项 | 施加一次后自动清空 | 否 |

**不新增**任何"立刻改菜单"的动作——因为那正是 B 禁止的路径。

规格 JSON 的字段面（对齐 §1 的参数表）：
```
items[] :
  type      : item | check | radio | submenu | separator
  id        : 整数（26500..28500，必填，separator 除外）
  label     : 文本（separator 除外）
  group_id  : 整数（type=radio 必填）
  checked   : 逻辑
  visible   : 逻辑
  enabled   : 逻辑
  accel     : { key_code:整数, shift:逻辑, ctrl:逻辑, alt:逻辑 }
  color     : { color_type:0..5, a,r,g,b:整数 }
  font      : 文本
  items[]   : 子菜单递归（type=submenu）
spec 顶层 :
  mode      : replace | append   （replace 才调用 清空菜单；缺省 append）
  one_shot  : 逻辑（缺省 假）
  only_when : 可选过滤 —— 菜单环境.取类型 () 位与 菜单类型.xxx == 0 时跳过施加
```

### B. 需要暂存规格的类级字段

加在 `MCP命令服务器`（`MCP_Server.wsv:239-241` 的类，`@全局类 = 真 @输出名 = "MCPCommandServer"`），**紧邻现有 `MCP_Server.wsv:393` 的 `是否监控菜单事件`**，保持同一区块风格：

| 字段（建议名） | 类型 | 作用 |
|---|---|---|
| `是否启用自定义菜单` | 逻辑型 静态 | 总开关；`是否监控菜单事件` **不承担**这个职责 |
| `菜单规格JSON` | 文本型 静态 | 整棵规格树 |
| `菜单规格版本` | 整数 静态 | `set_spec` 递增；便于 status 判断"是否已施加最新版本" |
| `菜单规格已施加版本` | 整数 静态 | 回调内写回 |
| `菜单规格施加次数` | 整数 静态 | 观察"事件到底来了几次" |
| `菜单规格上次施加时刻` | 长整数 静态 | 配合 `取启动时间 ()`（用法见 `MCP_Server.wsv:7708`） |
| `菜单规格上次施加浏览器ID` | 整数 静态 | 确认施加到哪只浏览器 |
| `菜单规格上次错误` | 文本型 静态 | 承接逐项返回假/校验失败的明细（避免静默成功） |
| `菜单规格一次性` | 逻辑型 静态 | one_shot 标志 |

### C. 施加时机（唯一落点）

`ROOT\src\MCP_BrowserEvents.wsv` 的 `浏览器_即将打开菜单` override，**在现有 `如果 (MCP命令服务器.是否监控菜单事件) { ... }`（`:2664-2667`）之后、方法体 `}` 之前**插入对施加过程的调用。

施加顺序（严格按此，因为 `添加子菜单` 返回子对象、后续置位必须作用在**正确的对象**上）：
1. 若 `mode == replace` → `菜单模式.清空菜单 ()`
2. 递归添加：`添加菜单` / `添加Check菜单` / `添加Radio菜单` / `添加分隔栏`；`submenu` 用 `添加子菜单` 拿返回值**在同一回调栈内**继续递归
3. 逐项 `置菜单标签` / `置可见状态` / `置禁止状态` / `选中状态`
4. `设置快捷键`（`Shift/Ctrl/Alt` 三个逻辑参数）
5. `置颜色` / `置字体`
6. 汇总：把所有返回假的项写入 `菜单规格上次错误`；`菜单规格施加次数` +1

### D. 施加时机——必须同时遵守的两条

- **绝不在** `browser_context_menu` 的工具处理函数里直接调 `菜单模式.*`（B + 跨线程）。工具只写字段。
- **也不要**把施加挪到 `浏览器_菜单被调用`（`RunContextMenu`）：该方法当前 `返回 (假)`（`MCP_BrowserEvents.wsv:2682`）即"走 CEF 默认显示"，`cef_context_menu_handler.h:114-116` 说明此时 `model` 是 `OnBeforeContextMenu` 的结果——在 `OnBeforeContextMenu` 内改完最干净。

### E. 失败 / 边界情况（逐条）

| # | 情况 | 处置 |
|---|---|---|
| 1 | **事件没来**（右键一次都没发生） | 规格留在内存，不阻塞、不报错；`status` 回报 `施加次数=0` + `pending=true`。禁止为了"让事件快来"而在工具里伪造右键或自动触发事件 |
| 2 | **菜单规格为空** | **必须"跳过"，绝不能"清空"**。若在规格为空时误调 `清空菜单`，结果是**右键菜单彻底消失**（`cef_context_menu_handler.h:100-101` 原文："The \|model\| can be cleared to show no context menu"）。这是本方案最大的单点事故，需在施加过程入口做 `规格为空 → 立即返回` 的硬短路 |
| 3 | **多次打开菜单是否要重复施加** | **要，每次都必须重施**。`OnBeforeContextMenu` 每次右键都会拿到模型（`cef_context_menu_handler.h:99-101` 说 `\|model\| initially contains the default context menu`——即每次都是新的默认模型），所以"只施加一次"会导致第二次右键菜单恢复默认。`菜单规格施加次数` 递增可用作观察 |
| 4 | **规格施加后是否清空** | 默认**不清空**（一次下发、长期生效）。提供 `one_shot`：施加成功后自动清空 `菜单规格JSON` 并把 `是否启用自定义菜单` 置假（AI 想"只显示一次"时用）。`clear_spec` 为显式清空。清空动作**只能发生在回调内施加完成之后**，不能在工具线程里清 |
| 5 | **子菜单对象跨回调用** | 禁止。`添加子菜单` 的返回值必须在**同一次回调栈内**用完（§1.5 官方样板即如此）。规格树递归深度需限幅（建议 ≤4 层） |
| 6 | **命令ID 越界** | `cef_types.h:1727-1731` 要求 26500..28500。`set_spec` 阶段就校验并拒绝（返回明确错误），不要留到回调里（回调里出错的反馈链路更长） |
| 7 | **与 `browser_kernel_menu` 冲突** | `MCP_Kernel.wsv:41` `变量 屏蔽快捷菜单 <公开 静态 类型 = 逻辑型 值 = 假 ...>` + `MCP_Kernel.wsv:514-538` `分派_菜单管理`（`disable` → `屏蔽快捷菜单 = 真`）。两者同时开启时**没有任何代码定义优先级**。建议：`status` 输出互斥告警；`是否启用自定义菜单 = 真` 时自动把 `屏蔽快捷菜单` 置假（因为屏蔽 = 整块干掉右键菜单，与自定义菜单语义相反），并把该动作写进 `status` 供 AI 观察 |
| 8 | **逐项返回值被忽略 → 静默成功** | 34 个方法中所有 `添加*` / `置*` 都是 `IsEmpty() ? false : FBroHsMenuModel_xxx(...)`（如 `FBroLib.wsv:3335-3336`）。对象一旦为空就**静默返回假**，不抛错。施加过程必须逐项收集返回假 并写入 `菜单规格上次错误`；`status` 必须暴露该字段 |
| 9 | **不要依赖 `是否监控菜单事件`** | 覆盖函数**无论开关真假都会被调用**（`MCP_BrowserEvents.wsv:2664` 的 `如果` 只包住日志写入，不包住整个方法体）。因此施加路径不应以该开关为前提，否则会出现"AI 以为没开监控所以菜单不会改"的误判 |
| 10 | **Radio 群组一致性** | `添加Radio菜单` 需要 `群ID`（`FBroLib.wsv:3350`）。同一群内应只允许一个 `checked=真`，`set_spec` 阶段校验 |
| 11 | **颜色默认值陷阱** | `置颜色` 的 `A/R/G/B` 全部 `@默认值 = 0`（`FBroLib.wsv:3541-3544`）。若规格只给 `color_type` 而不给 RGB，会得到 A=0 全透明黑。规格校验应对"给了 `color` 却缺 RGB"直接报错，而不是用 0 兜底 |
| 12 | **快捷键只是显示，不触发** | 类库原文 `FBroLib.wsv:3464`：`注释 = "只是用于显示快捷键，触发需自行用键盘事件实现"`（`设置快捷键_索引` 同，`:3474`）。工具描述必须逐字转达，否则 AI 会以为设置快捷键就能响应 |
| 13 | **`置字体` 类库自标"待验证"** | `FBroLib.wsv:3609` / `:3616` 均为 `注释 = "待验证"`。建议规格中 `font` 字段默认不暴露，或标注 experimental 并如实说明未经验证 |
| 14 | **`query_tree` 无法从 CEF 反查** | 见 §1.3：缺 `GetLabelAt`/`GetCommandIdAt`/`GetTypeAt`/`GetSubMenuAt`，无法按索引遍历。`get_spec` 只能返回"我方暂存的规格"，**不是** CEF 侧真值，工具描述必须写明 |
| 15 | **多浏览器** | 规格是单个全局静态字段。多浏览器场景下所有浏览器共用一棵菜单树；`菜单规格上次施加浏览器ID` 用于观察。若需分浏览器，规格可扩展 `by_browser_id` 映射（本轮不建议，先做单规格） |
| 16 | **事件族未开启时事件是否仍然到达** | `【静态-逐字】` 覆盖函数不受开关限制（边界 9）；但"CEF 是否回调本方 OnBeforeContextMenu"取决于事件注册，**本轮未验证**。已由主代理实证的是"开启监控后右键确实产生 `context_menu_opening`"，未实证的是"未开启监控时是否仍然回调" → 因此 `enable` 动作应当**顺带把 `是否监控菜单事件` 置真**（见 §5） |

## 方案乙 —— 保存句柄 + 即时增删（**当前结论 B 下不建议实施**）

保留设计，供 3.5 探针若推翻 B 时启用。

### A. 工具动作

`browser_context_menu` 的动作直接映射类库方法：`attach`（在回调内保存句柄）/ `detach` / `add_item` / `add_submenu` / `add_separator` / `add_check` / `add_radio` / `remove` / `set_visible` / `set_enabled` / `set_checked` / `set_checked_at` / `set_accel` / `remove_accel` / `set_color` / `set_font` / `clear` / `query_tree` / `status`。
其中 `query_tree` 在方案乙下**才**能从 CEF 侧读真值（但仍受 §1.3 的索引读缺失限制——只能按已知 `命令ID` 逐项 `是否可见`/`是否禁止`/`是否选中`/`取菜单标签`/`取菜单类型`/`取分组ID`/`取子菜单` 递归）。

### B. 类级字段

| 字段 | 类型 | 作用 |
|---|---|---|
| `暂存菜单模式` | `类_FBrowser_菜单模式` 静态 | 回调内 `暂存菜单模式 = 菜单模式` |
| `暂存菜单模式浏览器ID` | 整数 静态 | 归属校验 |
| `暂存菜单模式时刻` | 长整数 静态 | TTL 判定 |
| `暂存菜单模式有效` | 逻辑型 静态 | `浏览器_菜单被关闭` 里置假（显式失效，不依赖 CEF） |

### C. 施加时机

- **写入句柄的时机**：`浏览器_即将打开菜单`（`MCP_BrowserEvents.wsv:2663`）方法体开头。
- **失效时机**：`浏览器_菜单被关闭`（`MCP_BrowserEvents.wsv:2704`）里置 `暂存菜单模式有效 = 假`。
- **真正生效的时机**：`浏览器_菜单被调用`（`MCP_BrowserEvents.wsv:2670`，即 `RunContextMenu`）。这才是唯一能让"工具线程改的对象"对本次显示生效的窗口——但也意味着工具必须在**同一次右键的这两次回调之间**完成写入，**MCP 的请求-响应模型做不到这件事**（工具调用是异步的独立请求）。这是方案乙在工程上不可用的根本原因，**即使 Q3=A 也不成立**。

### D. 失败 / 边界

| # | 情况 | 后果 |
|---|---|---|
| 1 | 句柄在菜单关闭后被延迟使用 | 违反 `cef_context_menu_handler.h:102-103`；或无效/崩溃 → 这正是 B |
| 2 | 跨线程调用（工具线程） | 违反 `cef_menu_model.h:48` |
| 3 | 菜单已显示后再改 | 对已显示的菜单无效果，产生"成功但无效"的假成功 |
| 4 | 多次打开菜单覆盖句柄 | 旧句柄悬空；需 TTL + `浏览器_菜单被关闭` 显式失效 |
| 5 | 时序窗口（C 节） | 工具调用无法落在 `OnBeforeContextMenu` 与 `RunContextMenu` 的间隙内 → 即时增删在设计上就打不中目标 |

---

# §5 与该事件相关的现有基础设施（`文件:行号` + 原文）

## 5.1 `是否监控菜单事件` 标志

`ROOT\src\MCP_Server.wsv:393`（逐字）：
```
    变量 是否监控菜单事件 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_即将打开菜单/菜单被调用/菜单被点击/菜单被关闭 → browser_event:context_menu*" @输出名 = "IsMonitorContextMenu">
```
宿主类：`MCP_Server.wsv:239-241`
```
239: 类 MCP命令服务器 <公开 @全局类 = 真 @视窗.附属文件 = "..\\docs > docs" @视窗.附属文件 = "mcp_config.json" @视窗.附属文件 = "..\\mcp_config.README.md"
241:         @视窗.附属文件 = "..\\workflows > workflows" @输出名 = "MCPCommandServer">
```
同类标志组（同一区块，`MCP_Server.wsv:383-404`）共 20 余个 `是否监控xxx` 静态变量 —— 新字段应加在此区块内，风格对齐。

## 5.2 `记录监控事件`（统一写入口）

`ROOT\src\MCP_BrowserEvents.wsv:29-55`（逐字）：
```
    方法 记录监控事件 <类型 = 逻辑型 @输出名 = "RecordMonitorEvent" @强制输出 = 真>
    参数 开关 <类型 = 逻辑型 @输出名 = "Switch2">
    参数 事件类型 <类型 = 文本型 @输出名 = "EventType">
    参数 浏览器ID <类型 = 整数 @输出名 = "BrowserID">
    参数 数据JSON <类型 = 文本型 @默认值 = "" @输出名 = "DataJSON">
    {
        如果 (开关)
        {
            MCP命令服务器.记录浏览器事件 (事件类型, 浏览器ID, 数据JSON)
        }
        // 反应器钩子: 必须放在"是否记录该事件族"的开关**之外** —— 反应器是独立功能,
        // 放在 如果(开关) 内会退化成"只有先开启事件记录族才会触发", 而用户注册规则时并不知道这个隐式前提。
        MCP_内核分派.检查反应器 (事件类型)
        返回 (开关)
    }
```
下游落库：`MCP_Server.wsv:7699-7714` `方法 记录浏览器事件 <公开 静态 @输出名 = "RecordBrowserEvent" @强制输出 = 真>`，最终 `记录事件日志 ("browser_event", 事件类型, 浏览器ID, ...)`（`MCP_Server.wsv:7713`）。

反应器钩子：`MCP_Kernel.wsv:814-817`
```
814:     # 钩子: 记录监控事件 内调用 (事件被记录时触发规则动作)
816:     方法 检查反应器 <公开 静态 @输出名 = "CheckReactor" @强制输出 = 真>
817:     参数 事件类型 <类型 = 文本型 @输出名 = "EventType">
```

## 5.3 `browser_collect` 的 `event_menu_enable` 分支

分派入口：`MCP_Server_Core.wsv:3371-3374`
```
3371:         否则 (方法名 == "browser_collect")
3372:         {
3373:             变量 action <类型 = 文本型>
3374:             action = MCP命令服务器.yyjson取文本 (参数JSON, "action")
```
分支本体：`MCP_Server_Core.wsv:3501-3505`（逐字）
```
            否则 (action == "event_menu_enable")
            {
                MCP命令服务器.是否监控菜单事件 = 真
                返回 (MCP_响应构建.命令成功 (命令ID, "右键菜单事件监控已启用 (context_menu_opening/run/command/dismissed)"))
            }
```
工具注册：`MCP_Server.wsv:9732`（`添加工具JSON ("browser_collect", ...)`，action 枚举里含 `event_menu_enable`）。
命令注册表登记：`MCP_Server.wsv:1074` `命令注册表.置整数值 ("browser_collect", 900)`。

**两个必须知道的口径缺口** `【静态-逐字】`：
- `event_all_enable`（`MCP_Server_Core.wsv:3606-3619`）**不含** `是否监控菜单事件`；
- `event_all_disable`（`:3626-3641`）也**不含**它。
即"全开"并不会打开菜单族监控，新工具不能假定 `event_all_enable` 已经打开了它。

## 5.4 `browser_event` 查询入口

工具注册：`MCP_Server.wsv:9952` `添加工具JSON ("browser_event", ...)`；命令注册表：`MCP_Server.wsv:1176` `命令注册表.置整数值 ("browser_event", 912)`。
处理器：`MCP_Server_Core.wsv:4480-4552`，核心两行：
```
4480:         否则 (方法名 == "browser_event")
4483:             evtType = MCP命令服务器.yyjson取文本 (参数JSON, "event_type")
4542:                     evtResult = MCP命令服务器.查询事件日志 ("browser_event", evtType, evt查询BID, evtLimit)
```
**关键**：`browser_event` 按 **`event_type` 精确匹配** 查询（内部 `查询事件日志`），例如 `browser_event {event_type:"context_menu_opening"}`。主代理实证走的正是这条路径。

## 5.5 旧工具 `browser_kernel_menu`（语义相反，必须做互斥）

注册：`MCP_Server.wsv:9802`
```
        添加工具JSON ("browser_kernel_menu", "内核层: 右键快捷菜单屏蔽。action=disable屏蔽页面右键菜单(内核事件拦截), enable恢复, status查状态(触发条件以实际内核为准)", 单参数Schema文本 ("action", "text", "disable/enable/status"))
```
实现：`MCP_Kernel.wsv:514-538` `方法 分派_菜单管理 <公开 静态 类型 = 文本型 @输出名 = "DispatchMenuManage" @强制输出 = 真>`；状态字段 `MCP_Kernel.wsv:41`：
```
    变量 屏蔽快捷菜单 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "为真时屏蔽右键快捷菜单(触发条件以实际内核为准)" @输出名 = "BlockContextMenu">
```

## 5.6 新工具应如何与上述基础设施协作（**零前置**口径）

1. **注册位置**：`MCP_Server.wsv` 工具注册区，建议紧邻 `:9802` 的 `browser_kernel_menu`（同属右键菜单能力域），名 `browser_context_menu`，action 用 `多属性Schema文本`（同 `:9797`/`:9799` 的写法）。
2. **分派位置**：`MCP_Server_Core.wsv` 分支区（`browser_collect` 在 `:3371`、`browser_event` 在 `:4480`），新增 `否则 (方法名 == "browser_context_menu")`。若按项目现有习惯放到内核域，也可在 `MCP_Kernel.wsv` 的 `分派_菜单管理` 旁新增同类 `分派_*` 静态方法并注册路由。
3. **注册表登记**：`MCP_Server.wsv:1074` 一带的 `命令注册表.置整数值 ("...", N)`，取一个未占用编号。
4. **零前置（必须做）**：`browser_context_menu` 的 `enable` / `set_spec` 动作里，**顺带 `MCP命令服务器.是否监控菜单事件 = 真`**。
   - 先例（项目既有"自动开启前置"惯例）：`MCP_Server_Core.wsv:3476-3479`
     ```
     3476:                 如果 (MCP命令服务器.是否记录控制台 == 假)
     3477:                 {
     3478:                     MCP命令服务器.是否记录控制台 = 真
     3479:                 }
     ```
     （`console_get` 自动打开控制台记录）
   - 收益：即使 CEF 侧回调与监控开关无关（边界 9），工具也让 AI 能立刻用 `browser_event {event_type:"context_menu_opening"}` 自证"事件到了、规格施加了"，无需额外前置步骤。
   - **同时**在 `status` 里回报 `是否监控菜单事件` 与 `event_all_enable` 不含菜单族这一事实，避免 AI 误以为全开就够。
5. **不要**把新工具做成 `browser_collect` 的新 action —— `browser_collect` 的语义是"开关/收集"，而 `browser_context_menu` 是"下发配置"，且 action 枚举已经很长（`MCP_Server.wsv:9732` 的枚举串）。`【静态-推导】`
6. **与 `browser_kernel_menu` 的协作**：见方案甲边界 7。

---

# §6 本轮无法静态判定 / 明确未做的事项

1. `【未知】` 未开启 `是否监控菜单事件` 时，CEF 是否仍然回调 `OnBeforeContextMenu`（覆盖函数本身不受开关约束，但事件注册链路未验证）。
2. `【未知】` 延迟调用 `菜单模式` 是否**立即崩溃**（见 §3.4、§3.5）。B 的裁定不依赖此项。
3. `【未知】` `运行命令菜单回调.继续(...)`（`FBroCallback.wsv:281-287`）之后再改 `菜单模式` 是否生效。
4. `【未知】` `置字体`（`FBroLib.wsv:3609`，类库自标"待验证"）在真机上是否真的改变观感。
5. **未执行**（受本轮硬性禁止约束）：任何编译、任何 MCP 工具调用、任何 HTTP 请求、任何进程启停。因此**本报告不含任何"已验证/已测试"结论**。
6. **未修改任何已存在文件**；本报告是唯一新增文件。

## 附：本轮只读访问过的路径清册

- `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\{FBroLib,FBroEventControl,FBroConst,FBroCallback,FBroHelp,FBroDataType,FBroValue,FBroVip}.wsv`
- `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\例子\FB浏览器模块例子\{browser_event,browser_event1,browser_event4,browser_event7,browser_event11,browser_event13,browser_event28}.wsv`
- `ROOT\src\{MCP_BrowserEvents,MCP_Server,MCP_Server_Core,MCP_Kernel,MCP_Stdio,MCP_Server_HTTP}.wsv`
- `ROOT\AI-Fbowser-Mcp.vprj`
- `ROOT\generated-cpp\release-win32\{vcls_FBroMenuModel.h,vpkg_FBroEventControl.cpp}`
- `ROOT\_int\AI-Fbowser-Mcp\release\x64\project\vpkg_MCP_BrowserEvents.cpp`
- `ROOT\_audit\{probe_menu_event_feasibility.py,_classlib_gap_confirmed.md,_classlib_gap_confirmed2.md,_classlib_gap_recheck.md,_classlib_gap_verify_r98.md,_window_api_research.md}`
- `E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\src\env\FBrowserCEF3lib\include\{cef_context_menu_handler.h,cef_menu_model.h,cef_types.h}`
