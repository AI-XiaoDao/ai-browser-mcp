# 类库缺口刷新核对 r117（只读静态核对）

> 本文只做**静态核对**。**未做任何真机验证**；文中一切"能/不能"均为"类库有该能力 + 本项目没有对应工具/参数"的**代码事实**陈述，不代表已验证可用。
> 未修改 `src/`、未编译、未调 MCP、未重启。唯一写入的文件是本文件。

> ## ⚠️ 重要：审计期间 `src/` 被并发改动，本报告已按最新状态重锚
>
> 本次核对于只读期间观察到 **`src/` 正在被主代理并发修改**，因此有两处结论需要按最新事实修正：
>
> 1. **`src/MCP_Server.wsv` 被整体重排**：`添加工具JSON` 区块行号整体移位。
>    - 审计开始时：**684,855 字节 / 11,501 行**（`browser_intercept` 在 `:10153`）
>    - 审计结束时：**688,180 字节 / 11,540 行**（`browser_intercept` 在 `:10192`，**+39 行**）
>    - **本文所有 `MCP_Server.wsv:行号` 均已按最新版本重锚**，并同时给出**工具名/方法名锚点**（例如"`MCP_Server.wsv:10192`（`browser_intercept`）"），行号漂移时可据此重新定位。相反，`MCP_Server_Core.wsv` / `MCP_Server_VIP.wsv` / `MCP_Server_System.wsv` / `MCP_Callbacks.wsv` / `MCP_BrowserForms*.wsv` 的行号在审计全程稳定。
> 2. **`G3`（CEF 启动期命令行开关）在本次审计进行中已被主代理实现**（`src/main.wsv` mtime 09:16:12；`src/MCP_Server.wsv` mtime 09:19:21；新增辅助脚本 `_audit/_apply_startup_switches.py` / `_audit/verify_startup_switches_r117.py` / `_audit/verify_startup_switches_r117b.py` / `_audit/diag_startup_patch.py`）。
>    → **G3 已从"真缺口"降级为"残余项"**，见 §2.0。若本报告在更晚的时间被阅读，请重新 grep 锚点确认，不要照抄行号。

---

## 0. 本次实际跑出来的数字（全部来自实读/实运行）

| 项 | 数值 | 取证方式 |
|---|---|---|
| 工具总数 | **320**（审计开始与结束时各测一次，**两次都是 320**） | `Select-String -Path 'src\MCP_Server.wsv' -Pattern '添加工具JSON \("' -Encoding utf8 \| Measure-Object` → `Count = 320`；Python `len(re.findall(...))` 亦为 320 |
| 工具名去重 | **320（无重复）** | Python `re.finditer(r'添加工具JSON \("([^"]+)"')` + 计数重复项 = `[]` |
| 其它文件里的 `添加工具JSON` | 只有 `MCP_Server_1.~vbak.wsv`(265) / `MCP_Server_2.~vbak.wsv`(265)，**均为备份，已排除** | `Select-String -Path 'src\*.wsv' … \| Group-Object Filename` |
| 交叉核对语料 | 16 个 `src/*.wsv`（排除 `*.~vbak.wsv`），共 **1,420,418 字符** | Python 读入统计 |
| 匹配口径 | 严格词边界 `(?<!\w)方法名(?!\w)`（宽口径 `substring` 会把 `取响应` 误判为被 `取响应头` 覆盖，**已弃用** —— 这正是 G2 差点被漏掉的原因） | — |

### 类库方法计数（技能书转换版：`C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\`）

| 文件 | 文件大小 | 方法总数 | `公开` 方法 | 在 `src` 中**严格匹配 0 引用** |
|---|---|---|---|---|
| `FBroLib.wsv` | 287,774 B | 622 | **613** | 287 |
| `FBroVip.wsv` | 137,695 B | 198 | **195** | 53 |
| `FBroEventControl.wsv` | 143,472 B | 166 | **150** | **3** ✅ 与任务给的"147/150"一致 |
| `FBroDataType.wsv` | 77,608 B | 63 | 63 | 13 |
| `FBroValue.wsv` | 65,183 B | 218 | 218 | 101 |

> "0 引用"**只是筛选器，不是缺口结论**。下面 §2 的每一条都是人工看过签名 + 看过调用点后确认的。

### 行号复核（定稿前做的一次全量复检）

- 定稿前把本文出现的**全部 320 个 `文件:行号` 引用**逐条对着磁盘验了一遍（类库引用按技能书目录解析、`src` 引用按 `src/` 解析）：**320/320 落在文件行数范围内，0 条越界，0 个无法解析的文件**。
- 复检期间修正了这些曾引用错的 `MCP_Server.wsv` 行号（因上述并发重排，本文已是**最新**值）：`browser_intercept` `:10192`、`browser_context_menu` `:10191`、`browser_screenshot` `:10193`、`browser_create_url_request` `:10243`、`browser_download_image` `:10157`、`browser_dom_query` `:10177`、`browser_kernel_download` `:10267`、`browser_set_preference` `:10294`、`browser_vip_fingerprint_media_devices` `:10366`、`browser_base64_encode` `:10220` / `browser_codec` `:10224` / `browser_hash` `:10226`、`browser_list` `:10129`、`方法 清理VIP拦截资源` `:9001`、`可靠回填` 注释 `:8745`。
- 类库侧引用一律指向**技能书转换版**：`…\资料\类库\FBrowser浏览器\{FBroLib,FBroVip,FBroEventControl,FBroDataType,FBroValue}.wsv`（该目录行号与 IDE 的 `.v` 原文行号**不保证一致**）。

### 编码/工具踩坑（按任务要求如实记录）

本机 `pwsh` 是 Windows PowerShell 5.1：

- `py -3 script.py > $env:TEMP\x.txt` 再 `read` 该文件 → 报 **原文**：`Error: cannot read "C:\Users\cxzxc\AppData\Local\Temp\gx_tools.txt": binary file`（PS 5.1 重定向默认 UTF-16LE）。
- 控制台直出中文 → 乱码（实测样张：`JS����`、`�쳣�ռ�`、`������`，即控制台按 GBK 解 UTF-8）。
- 规避方式：所有中文结果由 **Python 自己 `open(path,"w",encoding="utf-8")` 落盘**，再用 `read` 工具读。**本次无任何文件读取失败**，也没有出现"文件为空"的情况，故除上面两条编码报错外**无其它报错原文可贴**。

---

## 1. 基线与交叉核对方法

1. 从 `src/MCP_Server.wsv` 抓全部 `添加工具JSON ("…"` → 320 个工具名（§0）。
2. 解析 5 个类库文件，抽出每个 `方法 <名> <公开 …>` + 其全部 `参数` 行 + 所属 `类` + 行号。
3. 对每个 `公开` 方法，在 16 个 `src/*.wsv` 全文里做**严格词边界**匹配 → 命中/未命中。
4. 未命中集 → 逐条人工核对以下**前缀路由 / 参数化 / 横切**通道后剔除误报：
   - `browser_id` 横切参数、`background:true`、`ignore_cache:true`、`action=…` 枚举式工具（`browser_fingerprint` / `browser_collect` / `browser_kernel_*` / `browser_intercept` / `browser_context_menu`）；
   - `browser_cdp_call` / `browser_cdp` 的 **CDP 全量透传**（依据：`_audit/_classlib_gap_recheck.md:192` —— "只校验\"方法名含点号\"，无域白名单"）；
   - 中文关键词扫描（`命令行` / `过滤器` / `替换资源` / `取填表框架` / `媒体硬件` / `取Cookie管理器` / `离屏渲染` …）确认"能力级"是否已被别的名字覆盖。
5. 模块/链接库可行性：先看 `AI-Fbowser-Mcp.vprj` 模块表（L16–L82：视窗基本类 / MFC界面基本类 / **FBrowser浏览器（`sys\FBrowser\FBrowserSimple.vgrp`，L32-34）** / yyJSON / 仰望模块 / HPSocket / MFC扩展界面支持类库1 / MFC表格组件 / SQLite数据库），再看本机 `E:\HSPC\plugins\vprj_win\classlib\{sys,user}`。

**本机 FBrowser 族实体文件（`E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\`）**：
`FBroLib.v` 912,046 B、`FBroVip.v` 357,058 B、`FBroEventControl.v` 487,162 B、`FBroDataType.v` 361,100 B、`FBroValue.v` 255,434 B、`FBroCallback.v` 176,190 B、`FBroConst.v` 112,956 B；
链接库 `FBrowserCEF3lib.lib` / `FBrowserVIP.lib` / `libcef.lib` / `libcef_dll_wrapper.lib`（win32 与 x64 两套）**均在**。
→ 结论：**本报告涉及的 FBrowser 族缺口，没有一条是"缺模块 / 缺链接库"造成的**，不构成排除理由。

---

## 2. 缺口清单（按"实现价值 / 风险"排序）

状态图例：**🔴 真缺口（未做）** / **🟡 残余（部分已做，仍有明确缺项）** / **⚪ 已关闭（勿重复立项）**

| # | 缺口 | 状态 |
|---|---|---|
| G1 | 子框架（iframe）原生填表 | 🔴 |
| G2 | `browser_create_url_request` 无协议头/POST体/状态码 | 🔴 |
| G3 | CEF 启动期命令行开关 | 🟡 **本轮审计期间被并发实现，仅剩残余** |
| G4 | VIP 资源过滤器：二进制替换 + 响应头 + 正则地址 | 🔴 |
| G5 | 下载完成信息（落盘路径/完成判定） | 🔴 |
| G6 | `browser_vip_fingerprint_media_devices` 设备清单恒空（"假成功"） | 🔴 |
| G7 | `browser_fingerprint` 缺"只重置调用计数" | 🔴 |
| G8 | `browser_cache_dir` 疑似非 CEF 真实缓存目录 | 🔴（待实测） |
| G9 | `FBrowser_Parser_取数据URI`（data URI 组装） | 🔴 |
| G10 | 菜单模式只读 / 按索引寻址 | 🔴（高风险，先探针） |

---

### 2.0 🟡 G3（残余）—— CEF 启动期命令行开关：**主体已在本轮被并发实现**，仍缺 4 类

**⚠️ 先说结论：这一条在本报告起草过程中被主代理做掉了**，不要重复立项。以下记录**已做**与**仍缺**，供下一轮补完。

**已做（`src/main.wsv`，最新行号）**
- `main.wsv:480-548` `方法 即将处理命令行` 已从"只记日志"改成真正施加开关，门控在 `进程类型 == ""`（浏览器进程），并有 8 行注释解释门控理由与类库依据。
- 当前白名单**6 项**：`启用摄像头`（`main.wsv:503`）、`启用录音`（`:508`）、`启用自动播放`（`:513`）、`禁用GPU`（`:518`）、`禁用GPU缓存`（`:523`）、`忽略GPU禁用清单`（`:528`）；随后 `命令行.取字符串 ()` 回读原文（`:531`），结果落在 `MCP命令服务器.命令行开关已应用` / `.命令行开关原文`（`:533-534`）。
- **主代理已发现的一个类库缺陷（值得保留在结论里）**：`main.wsv:493-494` 注释 ——
  `// ⚠ 禁用类库的 启用无头模式: 它的方法体实为 FBroHsCommandLine_EnableAutoplayPoliey(与 启用自动播放 同一函数),`
  `//   是类库复制粘贴 Bug, 名实不符, 禁止接线。`
  → 与本次静态核对一致：`FBroLib.wsv:1909` `方法 启用无头模式 <公开 注释 = "命令行：--headless，无头模式">` 的方法体确实只有一行 `@ ...EnableAutoplayPoliey(...)`（见 `FBroLib.wsv:1910-1913` 区域）。**`启用无头模式` 应从缺口清单中永久剔除**（改不了，改了就变成重复施加自动播放）。

**仍缺（4 类，都是同一套已建好的通道里加分支即可）**

| 类库文件:行 | 完整签名（原文抄录） | 为什么仍值得加 |
|---|---|---|
| `FBroLib.wsv:1888` | `方法 启用跨框架操作模式 <公开 注释 = "跨框架操作，解除框架和框架直接不能直接操作的限制，存在不安全性">` | **与 G1（子框架填表）强互补**：G1 让原生填表能定位到 iframe，本开关解除跨域框架的操作限制。当前 0 引用 |
| `FBroLib.wsv:1968` | `方法 禁用代理 <公开 注释 = "命令行：--no-proxy-server，禁止使用代理和系统的自动检测代理功能">` | 排障"代理设坏了导致全站打不开"的唯一干净手段；当前只有 `browser_clear_proxy`（运行期、需刷新） |
| `FBroLib.wsv:1916` | `方法 设置远程调试端口 <公开 注释 = "命令行：--remote-debugging-port">`<br>`参数 端口号 <类型 = 整数>` | 主进程内已有 CDP 通道，故价值中；但外部工具（如 Playwright/Selenium 调试器）接入时是唯一入口。另有等价配置字段 `FBrowser_初始化配置.远程端口`（`FBroDataType.wsv:28`，映射见 `:68`），当前 0 引用 |
| `FBroLib.wsv:1835` / `:1865` / `:1857` | `方法 置项值 <公开 注释 = "英语名：AppendSwitchWithValue 说明：name默认前面要加\"--\"">`<br>`参数 项目名 <类型 = 文本型>`<br>`参数 项目值 <类型 = 文本型>`<br><br>`方法 插入值 <公开>`<br>`参数 值 <类型 = 文本型>`<br><br>`方法 置额外参数 <公开 注释 = "英语名：AppendArgument 说明：设置额外参数 Add an argument to the end of the command line" @禁止流程检查 = 真>`<br>`参数 参数文本 <类型 = 文本型>` | **白名单式任意 switch**（不是自由文本透传）：例如 `--disable-blink-features=AutomationControlled`、`--disable-features=…`、`--lang=…` 等，是排障/反检测的万能钥匙。主代理已建好"白名单 + 回读原文"的骨架（`main.wsv:531`），加一张"名→值"白名单表即可复用 |
| （`FBroLib.wsv:1874` `启用单进程模式`、`:1945`/`:1955` 全局代理） | — | **不建议加**：类库自述单进程模式"存在各种问题，不建议发布软件使用"；全局代理已有运行期 `browser_set_proxy` / `browser_set_s5_proxy` 覆盖 |

| 项 | 内容 |
|---|---|
| **已有工具里最接近的** | `browser_set_preference`（`MCP_Server.wsv:10294`）、`browser_set_proxy` / `browser_clear_proxy` / `browser_set_s5_proxy`、`browser_fingerprint_*`、`browser_set_window_style` |
| **为什么不能替代** | 这些都是**运行期/渲染期**语义；命令行开关是 **CEF 进程级、必须在初始化前（或 `即将处理命令行` 回调内且仅浏览器进程）施加**，运行期改无效。 |
| **建议** | 在 `main.wsv:501-529` 的白名单后追加上述 3~4 个 if 分支 + 对应 `启动开关_*` 静态开关与 `mcp_config.json` 字段；`置项值` 一类做成"受控表"而非自由文本。工具的 `list` 回执已由 `MCP命令服务器.命令行开关已应用`（`main.wsv:533`）提供。 |
| **价值** | 残余部分：**中-高**（`启用跨框架操作模式` 与 G1 组合后价值升为高） |
| **风险** | **低**（通道已建好、已有门控与回读；只需遵守"白名单 + 浏览器进程门控"两条既有约定） |
| **是否需要启动期** | **是** |

---

### 2.1 🔴 G1 —— 子框架（iframe）原生填表：填表框架只认"主框架"

| 项 | 内容 |
|---|---|
| **能力** | 对**任意子框架**（iframe）取"填表框架"句柄，从而用**原生 CEF DOM/填表 API**（非 JS 注入）读写 iframe 内的元素 |
| **类库文件:行** | `FBroLib.wsv:1406`、`FBroLib.wsv:1414`、`FBroLib.wsv:1422`、`FBroLib.wsv:1561` |
| **完整签名（原文抄录）** | `FBroLib.wsv:1406`<br>`方法 取焦点填表框架 <公开 类型 = 类_FBrowser_填表框架 注释 = "英文名：GetFocusedFrame 说明：Returns the focused frame for the browser window."`<br><br>`FBroLib.wsv:1414`<br>`方法 取填表框架_ID <公开 类型 = 类_FBrowser_填表框架 注释 = "英文名：GetFrame 说明：必须使用取框架ID取出的ID标识，ID错误会导致返回值为空，用类的是否为空判断，类为空而执行操作会导致奔溃"`<br>`参数 ID <类型 = 文本型>`<br><br>`FBroLib.wsv:1422`<br>`方法 取填表框架_名称 <公开 类型 = 类_FBrowser_填表框架 注释 = "英文名：GetFrame 说明：必须使用取框架名称取出的框架名，名称会导致返回值为空，用类的是否为空判断，类为空而执行操作会导致奔溃." @禁止流程检查 = 真>`<br>`参数 名称 <类型 = 文本型>`<br><br>`FBroLib.wsv:1561`（`类_FBrowser_基础框架`）<br>`方法 取填表框架 <公开 类型 = 类_FBrowser_填表框架 注释 = "取出当前填表框架，如果已经是填表框架了，调用相当于复制了一份" @禁止流程检查 = 真>` |
| **现有工具里最接近的** | ① `browser_fill_*` 共 **12 个**（`browser_fill_set_value` / `_click` / `_focus` / `_scroll` / `_exists` / `_attr_get` / `_get_text` / `_set_text` / `_attr_set` / `_trigger` / `_select` / `_form`）；② `browser_dom_query` / `browser_dom_click` / `browser_dom_set_value` / …；③ `browser_frame_by_name` / `browser_frame_by_id` / `browser_get_frames` |
| **为什么不能替代** | ②③ 全部只吃**主框架**：`src` 全量 **23 处**填表/DOM 入口**无一例外**写死 `取主填表框架 ()` —— `MCP_Server_Form.wsv:27,56,85,114,143,190,261,379,410,474`（10 处）；`MCP_Server_Core.wsv:467,1747,1789,1851,1889,1936,1977,2022,2067,2098,2133`（11 处）；`MCP_Callbacks.wsv:140,202`（2 处，回调内点击用）。<br>③ 的 `browser_frame_by_name` / `browser_frame_by_id` **只回框架信息**（`MCP_Server_Core.wsv:6483` `frame = browser.取框架_名称 (frameName)`、`:6524` `frame = browser.取框架_ID (frameId)`、`:6539` 只回 `found:false + hint`），**不返回任何可用于读写元素的句柄**。<br>12 个 `browser_fill_*` 的 Schema 里**没有 frame 类参数**（`MCP_Server.wsv:10245`（`browser_fill_set_value`）/ `:10251`（`browser_fill_get_text`）/ `:10252`（`browser_fill_set_text`）/ `:10468`（`browser_fill_form`））。<br>唯一能进 iframe 的是 `browser_vip_execute_js_context target=all_frames/frame_index`，但那是**纯 JS**（跨域 iframe 会被同源策略挡住），且其工具自述"⚠ 该三个 target 属 VIP 高级功能，**需先 browser_vip_enable_js_env** … 该开关会破坏本会话 CDP 通道且需重启恢复"（`MCP_Server.wsv:10371`）——代价不可接受，**不能替代原生填表**。<br>另注意：`browser_vip_key_input` 工具自述"**警告: 本工具实测每次调用都会让 CDP 通道在本会话内失效**"这类"VIP 高级 target 有副作用"的既有教训，说明走 VIP 环境不是免费路径。 |
| **建议** | 给 12 个 `browser_fill_*` 增加**可选参数** `frame`（取值：`frame_id` / `frame_name` / `focused`），内部按 `取填表框架_ID` / `取填表框架_名称` / `取焦点填表框架` 取句柄，缺省仍走 `取主填表框架()`。或单开 `browser_fill_frame_resolve` 做解析+回读。 |
| **价值** | **高** —— 登录/支付/验证码/嵌入式报表大量在 iframe 内；且本通道是"原生非 JS 注入"，正是本项目防检测定位所在 |
| **风险** | **低-中**。纯增量参数；唯一硬约束是类库原文警告"**类为空而执行操作会导致奔溃**"，必须 `是否为空()` 判空后再用（`FBroLib.wsv:1414`/`:1422` 注释） |
| **是否需要启动期** | **否**（与 G3 残余的 `启用跨框架操作模式` 组合时可选加启动期开关） |

---

### 2.2 🔴 G2 —— `browser_create_url_request` 空心：无自定义协议头 / 无 POST 体 / 不回状态码

| 项 | 内容 |
|---|---|
| **能力** | 主进程发起 URL 请求时：① 自定义协议头（含来路 Referrer）② POST 表单体（文本或文件）③ **读回 HTTP 状态码 / 错误码 / 响应头 / 是否来自缓存** |
| **类库文件:行** | 便捷入口 `FBroLib.wsv:2407`；分项 `FBroLib.wsv:2319` / `2349` / `2366` / `2373` / `2381` / `2398`；POST 体 `2508` / `2538`、`2602` / `2617`；读回 `5579` / `5585` / `5591` / `5597`；带请求头导航 `1669`；状态枚举类 `FBroConst.wsv:718` |
| **完整签名（原文抄录）** | `FBroLib.wsv:2407`（`类_FBrowser_请求`）<br>`方法 设置 <公开 注释 = "英文名：GetHeaderMap">`<br>`参数 地址 <类型 = 文本型>`<br>`参数 类型 <类型 = 文本型 注释 = "大写POST或者GET">`<br>`参数 POST数据 <类型 = 类_FBrowser_POST数据 注释 = "类型为POST,此项不能为空" @默认值 = 空对象>`<br>`参数 协议头数据 <类型 = FBrowser_双文本 @默认值 = 空对象>`<br><br>`FBroLib.wsv:2319`<br>`方法 置来路 <公开 注释 = "英文名：SetReferrer">`<br>`参数 来路地址 <类型 = 文本型>`<br>`参数 来路类型 <类型 = 整数 注释 = "参考：来路策略." @默认值 = 0>`<br><br>`FBroLib.wsv:2373`<br>`方法 置协议头数据 <公开 注释 = "英文名：SetHeaderMap">`<br>`参数 头数据 <类型 = FBrowser_双文本>`<br><br>`FBroLib.wsv:2381`<br>`方法 置协议头数据_数组 <公开 注释 = "英文名：SetHeaderMap">`<br>`参数 头数据 <类型 = FBrowser_双文本数组>`<br>`参数 删除其他数据 <类型 = 逻辑型 注释 = "为真设置的时候将会删除其他头数据，只保留当前设置的值，反之保留其他头数据" @默认值 = 假>`<br><br>`FBroLib.wsv:2398`<br>`方法 置协议头_名称 <公开 注释 = "英文名：SetHeaderByName">`<br>`参数 协议名 <类型 = 文本型>`<br>`参数 值 <类型 = 文本型>`<br>`参数 覆盖 <类型 = 逻辑型 @默认值 = 假>`<br><br>`FBroLib.wsv:2349`<br>`方法 置POST数据 <公开 注释 = "英文名：SetPostData">`<br>`参数 POST数据 <类型 = 类_FBrowser_POST数据>`<br><br>`FBroLib.wsv:2538`（`类_FBrowser_POST数据`）<br>`方法 增加元素 <公开>`<br>`参数 POST元素 <类型 = 类_FBrowser_POST元素>`<br><br>`FBroLib.wsv:2617`（`类_FBrowser_POST元素`）<br>`方法 置数据_文本 <公开>`<br>`参数 文本数据 <类型 = 文本型>`<br><br>`FBroLib.wsv:2602`（`类_FBrowser_POST元素`）<br>`方法 置数据_文件 <公开>`<br>`参数 文件名 <类型 = 文本型>`<br><br>`FBroLib.wsv:5579`（`类_FBrowser_URL请求`）<br>`方法 取请求状态码 <公开 类型 = URL请求状态 @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:5585`<br>`方法 取请求错误码 <公开 类型 = 整数 @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:5591`<br>`方法 取响应 <公开 类型 = 类_FBrowser_响应 @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:5597`<br>`方法 是否带缓存响应 <公开 @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:1669`（`类_FBrowser_框架`）<br>`方法 载入请求 <公开 注释 = "英文名：LoadRequest">`<br>`参数 请求 <类型 = 类_FBrowser_请求>` |
| **现有工具里最接近的** | `browser_create_url_request`（`MCP_Server.wsv:10243`）：Schema 只有 `url` + `method`，"仅支持 http/https 协议" |
| **为什么不能替代** | 现实现只用了类库的 2 个 setter：`MCP_Server_Core.wsv:6922-6925`<br>`变量 请求 <类型 = 类_FBrowser_请求>` / `请求.创建 ()` / `请求.置地址 (reqURL)` / `请求.置类型 (reqMethod)`<br>回调只回 **success + 响应体正文**：`MCP_Callbacks.wsv:800-833`（`包装对象.加入逻辑值成员 ("success", 真)`、`("message", 结果文本)`、`("data_size", …)`、`("truncated", …)`）——**全程没读 `取请求状态码` / `取请求错误码` / `取响应` / `是否带缓存响应`**（严格匹配下这些名字在 `src` 命中数为 0；宽口径之所以显示"命中"，是因为 `取响应头`（`MCP_Kernel.wsv:1897`）把 `取响应` 包了进去 —— 典型的伪覆盖）。<br>→ 调用方**无法区分 404 与 200**，无法拿到响应头，无法发 POST 表单，无法带 Authorization。<br>替代品均不成立：`browser_network` / `browser_network_body` 是**被动抓包**（只能看页面自己发的请求）；`browser_execute_js` 里的 `fetch` 走**渲染进程**，受 CORS/同源约束且对页面可见（与反检测定位相冲）。 |
| **建议** | 扩展现有 `browser_create_url_request`：新增 `headers`（JSON 对象）/ `body` / `content_type` / `referrer` 参数，实现侧改用 `请求.设置(地址, 类型, POST数据, 协议头数据)`；回调侧补 `status` / `error_code` / `response_headers` / `from_cache`。另可让 `browser_navigate` 支持 `extra_headers`（走 `FBroLib.wsv:1669 载入请求`）。 |
| **价值** | **高-中** —— API 直连取数、带认证头请求、表单 POST、判定 301/404，都是自动化刚需；且顺手修掉一个"只回成功不回状态"的语义盲区 |
| **风险** | **低**。setter 与 getter 都是现成公开方法，改动面 = 1 个 Schema + 1 个分支 + 1 个回调类多读几个 getter。唯一注意：响应头/状态码需在 `即将完成`（`MCP_Callbacks.wsv:797`）内读取 —— 当前回调已经在 `即将完成` 里，位置正确 |
| **是否需要启动期** | **否** |

---

### 2.3 🔴 G4 —— VIP 资源过滤器：二进制整体替换 + 自定义响应头 + 正则地址匹配

| 项 | 内容 |
|---|---|
| **能力** | ① 用**任意字节集/本地文件**整体替换某 URL 的资源（图片/字体/wasm/zip 等**非文本**）② 同时指定该响应的 **MIME 类型与响应协议头** ③ URL 匹配支持 完全/模糊/模糊头/模糊尾/**正则** ④ 文本改写支持"插入"模式 |
| **类库文件:行** | 全局静态 `FBroVip.wsv:114` / `126` / `133` / `139` / `150` / `161` / `168`；控制器级（每浏览器）`FBroVip.wsv:1134` / `1147` / `1162` / `1174` / `1186` |
| **完整签名（原文抄录）** | `FBroVip.wsv:139`（`FBrowserVIP全局功能`）<br>`方法 FBrowser_VIP过滤器_替换资源_数据 <公开 静态 注释 = "VIP高级功能，需赞助后才能使用，非VIP用户可通过资源处理器自行分包处理，此功能更方便更快；"`<br>`注释 = "用数据直接将整体链接资源替换，在资源加载前设置，也可在初始化后设置，使用该方法后对应请求目标地址的\"浏览器_获取资源处理器\"事件将不会被触发"`<br>`参数 匹配模式 <类型 = 整数 注释 = "地址匹配模式，参考：VIP过滤器地址." @默认值 = VIP过滤器地址.完全匹配>`<br>`参数 目标地址 <类型 = 文本型 注释 = "要替换目标资源链接地址，地址要为完整地址">`<br>`参数 MINI类型 <类型 = 文本型 注释 = "mini_type，资源类型，和协议头的content-type对应，例如：\"application/javascript\"或\"text/html\"，如果不设置默认为download">`<br>`参数 响应协议头 <类型 = FBrowser_双文本数组 注释 = "要设置的资源响应的协议头" @默认值 = 空对象>`<br>`参数 替换的数据 <类型 = 字节集类>`<br><br>`FBroVip.wsv:150`<br>`方法 FBrowser_VIP过滤器_替换资源_文件 <公开 静态 注释 = "VIP高级功能，需赞助后才能使用，非VIP用户可通过资源处理器自行分包处理，此功能更方便更快；"`<br>`参数 匹配模式 <类型 = 整数 注释 = "地址匹配模式，参考：VIP过滤器地址." @默认值 = VIP过滤器地址.完全匹配>`<br>`参数 目标地址 <类型 = 文本型 注释 = "要替换目标资源链接地址，地址要为完整地址">`<br>`参数 MINI类型 <类型 = 文本型 注释 = "mini_type，资源类型，和协议头的content-type对应，例如：\"application/javascript\"或\"text/html\"，如果不设置默认为download">`<br>`参数 响应协议头 <类型 = FBrowser_双文本数组 注释 = "要设置的资源响应的协议头" @默认值 = 空对象>`<br>`参数 替换的文件 <类型 = 文本型 注释 = "完整的路径+文件名，例如：\"F:\\\\xxx\\\\xxx\\\\xxx.txt\"">`<br><br>`FBroVip.wsv:114`<br>`方法 FBrowser_VIP过滤器_修改内容 <公开 静态 注释 = "VIP高级功能，需赞助后才能使用，非VIP用户可通过资源过滤器自行分包处理，此功能更方便更快；"`<br>`注释 = "对目标地址通过匹配目标文本修改内容，在资源加载前设置，也可在初始化后设置，使用该方法后对应请求目标地址的\"浏览器_获取资源过滤器\"事件将不会被触发；"`<br>`注释 = "如果同一个目标存在多个需要修改的数据，多次调用本方法即可，但要注意目标地址和匹配模式要保持一致，否则可能会出错">`<br>`参数 匹配模式 <类型 = 整数 注释 = "地址匹配模式，参考：VIP过滤器地址." @默认值 = VIP过滤器地址.完全匹配>`<br>`参数 目标地址 <类型 = 文本型 注释 = "要替换目标资源链接地址，地址要为完整地址">`<br>`参数 替换模式 <类型 = 整数 注释 = "VIP过滤器.xxx;如果模式为插入，将会在查找到的目标文本后面插入替换的文本；模式为修改，将会将目标文本删除替换为新文本；">`<br>`参数 目标文本 <类型 = 文本型 注释 = "要查找的文本">`<br>`参数 替换文本 <类型 = 文本型 注释 = "要替换或插入的文本">`<br><br>`FBroVip.wsv:126`（按 URL 单条撤销修改）<br>`方法 FBrowser_VIP过滤器_取消修改内容 <公开 静态 注释 = "在资源加载前设置，取消全局之前设置的对应目标地址的修改内容">`<br>`参数 目标地址 <类型 = 文本型 注释 = "和之前设置的目标地址一一对应">`<br><br>`FBroVip.wsv:161`（按 URL 单条撤销替换）<br>`方法 FBrowser_VIP过滤器_取消替换资源 <公开 静态 注释 = "在资源加载前设置，取消之前设置的对应目标地址的替换资源">`<br>`参数 目标地址 <类型 = 文本型 注释 = "和之前设置的目标地址一一对应">`<br><br>`FBroVip.wsv:133` / `:168`<br>`方法 FBrowser_VIP过滤器_取消全部修改内容 <公开 静态 注释 = "在资源加载前设置，取消全局所有的修改内容">`<br>`方法 FBrowser_VIP过滤器_取消全部替换资源 <公开 静态 注释 = "在资源加载前设置，取消之前设置的所有替换的资源，包括通过浏览器设置的资源">`<br><br>控制器级同形：`FBroVip.wsv:1162 过滤器_替换资源_数据` / `:1174 过滤器_替换资源_文件` / `:1134 过滤器_修改内容` / `:1147 过滤器_取消修改内容` / `:1186 过滤器_取消替换资源` |
| **现有工具里最接近的** | `browser_intercept`（`MCP_Server.wsv:10192`），action：`modify` / `replace_data` / `replace_file` / `block` / `line_replace` / `unmodify` / `unreplace` / … |
| **为什么不能替代** | 现工具**明确只走手写 ResponseFilter 通道**：`MCP_Server_Core.wsv:2558` 注释 `// -- 资源拦截 (手写过滤器通道, 不依赖VIP官方过滤器) --`；工具描述自述 **"url一律按子串匹配, **无正则模式**"**、"modify…**仅文本类MIME**"、"replace_file…**需文本类文件**"（`MCP_Server.wsv:10192`）。<br>**二进制不成立的代码级证据**：手写篡改过滤器的输出路径全程走文本 —— `MCP_Callbacks.wsv:1152-1154`<br>`变量 输出字节 <类型 = 字节集类>` / `输出字节 = 文本到UTF8 (尝试文本, 假)` / `内存复制 (输出指针, 取字节集指针 (输出字节), 取字节集长度 (输出字节))`<br>（`获取数据`（`MCP_Callbacks.wsv:1087`）收到的原始字节被当数据缓存，但**吐回时按 UTF-8 文本重编码**，输出缓冲还按"字符数"做二分切分 —— `MCP_Callbacks.wsv:1114-1151`）。<br>→ **图片/字体/wasm/zip 无法替换；响应协议头完全无法设置**（想给某响应注入 `Access-Control-Allow-Origin` 之类只能靠 VIP 这条）。<br>**须如实说明的前置轮次结论**：`_audit/_cg2_verdict.json` 已把这 4 条判为 **B2（覆盖）** —— `FBrowser_VIP过滤器_修改内容` → `browser_intercept action=modify`；`替换资源_数据` → `action=replace_data`；`替换资源_文件` → `action=replace_file`；`取消全部*` → `action=clear`。**本次是就"二进制载荷 / 响应头 / 正则地址"这三个更窄的差异点申请改判**，不是新发现；请主代理按改判处理。<br>（同轮被判 A 的"只能整串清空、无按 URL 单条撤销"**已经在本项目实现**：`browser_intercept` 现有 `unmodify` / `unreplace`，见 `MCP_Server.wsv:10192` 与 `MCP_Server_Core.wsv:2634` / `:2641` —— **此条不再是缺口，勿重复立项**。） |
| **其它旁证** | `main.wsv:52-53` 已强制解禁 VIP 门控：`// 免VIP: 强制解锁类库VIP门控标志 …` / `FBrowser初始化控制.是否为VIP = 真` —— 所以这些 `@<FBrowser初始化控制.是否为VIP>` 门（`FBroVip.wsv:123` / `:147` / `:158` 等内联判断）在本项目不构成阻断。<br>项目**只接了取消侧、没接设置侧**：`MCP_Server.wsv:9001` `方法 清理VIP拦截资源` 调 `vip_ctrl.过滤器_取消全部修改内容 ()` / `vip_ctrl.过滤器_取消全部替换资源 ()`，而全 `src` **没有任何一处调用** `过滤器_修改内容` / `过滤器_替换资源_数据` / `过滤器_替换资源_文件`。 |
| **建议** | 给 `browser_intercept` 增加 `engine` 参数（缺省 `"manual"` 保持现状，`"vip"` 走 VIP 通道）+ 新 action：`vip_replace_data`（`data_b64` + `mime` + `headers`）、`vip_replace_file`、`vip_modify`（`match_mode`: exact/fuzzy/fuzzy_head/fuzzy_tail/regex + `insert` 模式）、`vip_cancel`（按 URL）。 |
| **价值** | **高** —— ① 二进制资源替换（图片/字体/wasm/zip）② **响应头注入**（CORS、缓存策略）③ 正则地址匹配；这三样手写通道做不到，且是逆向/取数场景的硬需求。已解禁的 VIP 能力白白闲置 |
| **风险** | **中**。类库原文两条约束必须尊重：① "使用该方法后对应请求目标地址的**浏览器_获取资源过滤器事件将不会被触发**"（`FBroVip.wsv:115` / `:140`）—— 即 VIP 规则会**抢占**手写通道对同一 URL 的处理，必须按 URL 严格分流，否则会把现有 `browser_intercept cache` 抓包打断；② 是**全局静态**语义（`FBrowserVIP全局功能`），进程内所有浏览器共享，需在工具响应里写明作用域。 |
| **是否需要启动期** | **否**（类库原文"在资源加载前设置，**也可在初始化后设置**"，只需在目标资源加载/刷新前施加） |

---

### 2.4 🔴 G5 —— 下载完成信息全缺：拿不到落盘路径、拿不到完成/取消判定

| 项 | 内容 |
|---|---|
| **能力** | 下载结束后读取 **落盘完整路径 / 结束时间 / 原始地址 / Content-Disposition / 是否已完成 / 是否已取消 / 是否仍在进行 / 当前速度** |
| **类库文件:行** | `FBroLib.wsv:3710` / `3699` / `3729` / `3743` / `3658` / `3663` / `3653` / `3668` |
| **完整签名（原文抄录）** | `FBroLib.wsv:3710`（`类_FBrowser_下载`）<br>`方法 取存储位置 <公开 类型 = 文本型 注释 = "英文名：GetFullPath" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3658`<br>`方法 是否已下载完成 <公开 类型 = 逻辑型 注释 = "英文名：IsComplete" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3663`<br>`方法 是否已取消 <公开 类型 = 逻辑型 注释 = "英文名：IsCanceled" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3653`<br>`方法 是否仍在下载中 <公开 类型 = 逻辑型 注释 = "英文名：IsInProgress" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3668`<br>`方法 取现行下载速度 <公开 类型 = 长整数 注释 = "英文名：GetCurrentSpeed" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3699`<br>`方法 取结束时间 <公开 类型 = 文本型 注释 = "英文名：GetEndTime" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3729`<br>`方法 取原始地址 <公开 类型 = 文本型 注释 = "英文名：GetOriginalUrl" @禁止流程检查 = 真>`<br><br>`FBroLib.wsv:3743`<br>`方法 取内容描述 <公开 类型 = 文本型 注释 = "英文名：GetContentDisposition" @禁止流程检查 = 真>` |
| **现有工具里最接近的** | `browser_start_download` / `browser_download_image` / `browser_kernel_download`；事件 `browser_event` 查 `download_*` |
| **为什么不能替代** | 现有两处下载回调只读了 **6 个** getter：<br>`MCP_BrowserEvents.wsv:649` / `:655` / `:657`（`即将下载`：`取推荐文件名` / `取总长度`）<br>`MCP_BrowserEvents.wsv:743` / `:745` / `:755-761`（`正在下载`：`取下载百分比` / `取推荐文件名` / `取已下载长度` / `取总长度`）<br>`MCP_BrowserEvents.wsv:771`（`取关联标识符` / `取地址`）<br>事件全集里**没有完成/取消事件**：`download_request`（`MCP_BrowserEvents.wsv:2309`）、`download_start`（`:697` / `:709`）、`download_progress`（`:763`）、`download_start_error`（`:677`）；启用文案也自认只有三种 —— `MCP_Server_Core.wsv:3819` `"下载事件监控已启用 (download_request/start/progress)"`。<br>`browser_kernel_download` 只做 pause/resume/cancel（`MCP_Server.wsv:10267`）。<br>→ **一个自动化客户端永远不知道文件下到哪、有没有下完**；`browser_download_image` 只能拿到"保存路径"这种特例（`MCP_Server.wsv:10157` 描述"异步, 用 mcp_result 取保存路径"），普通下载无对应能力。 |
| **建议** | 在 `浏览器_正在下载`（`MCP_BrowserEvents.wsv:725`）内补读 `取存储位置` / `是否已下载完成` / `是否已取消` / `取现行下载速度` / `取原始地址` / `取内容描述`，并在状态跃迁时经现有 `记录监控事件` 通道发 `download_complete` / `download_canceled`。或并入 `browser_kernel_download` 的 `action=list` 回包。 |
| **价值** | **中-高** —— "下载这个文件然后告诉我它在哪"是下载类任务的收口，现在收不了口 |
| **风险** | **低**。纯读 getter + 多一个事件名；注意 `正在下载` 是高频回调，需沿用现有"里程碑节流"写法（`MCP_BrowserEvents.wsv:747` `是否为里程碑进度`）避免刷爆事件日志 |
| **是否需要启动期** | **否** |

---

### 2.5 🔴 G6 —— `browser_vip_fingerprint_media_devices` 空心：设备清单**恒未传入**（"假成功"）

| 项 | 内容 |
|---|---|
| **能力** | 虚拟媒体设备指纹（摄像头/麦克风/扬声器清单）——需要**填入 驱动ID / 硬件名 / 分组ID** 的清单数组 |
| **类库文件:行** | `FBroVip.wsv:557` / `569` / `581`（接收方）；`FBroDataType.wsv:1626`（类）、`1731` / `1739` / `1745` / `1751` / `1757` / `1763`（清单容器 API） |
| **完整签名（原文抄录）** | `FBroVip.wsv:569`<br>`方法 指纹_虚拟VideoInput设备 <公开 注释 = "VIP功能，需要赞助后才能使用，虚拟媒体输出设备硬件信息，如播放设备等信息，注意虚拟媒体设备可能会照成浏览器声音或麦克风异常无法获取到真实设备">`<br>`参数 类型 <类型 = 整数 注释 = "0为清空，1为添加，2为覆盖,如果为0，下面修改数据设不设置都不会生效">`<br>`参数 媒体硬件清单 <类型 = FBrowser_媒体硬件数组`<br>`        注释 = "硬件信息中的驱动ID和分组ID，驱动ID除了设置成default和communications为，设置的ID值其实是硬件的ID，不是JS通过命令显示的ID，这个ID和下面的分组ID一样，可以在你的硬件驱动里面取查找，设置后JS所获取的也会改变;"`<br>`        @默认值 = 空对象>`<br><br>（`FBroVip.wsv:557 指纹_虚拟AudioInput设备`、`FBroVip.wsv:581 指纹_虚拟AudioOutput设备` 同形同参）<br><br>`FBroDataType.wsv:1731`<br>`方法 加入数据 <公开 类型 = 整数 注释 = "加入数据，并返回数据ID，ID为累加唯一标识" @禁止流程检查 = 真>`<br>`参数 驱动ID <类型 = 文本型>`<br>`参数 硬件名 <类型 = 文本型>`<br>`参数 分组ID <类型 = 文本型>`<br><br>`FBroDataType.wsv:1763`<br>`方法 清空全部数据 <公开 @禁止流程检查 = 真>` |
| **现有工具里最接近的** | `browser_vip_fingerprint_media_devices`（`MCP_Server.wsv:10366`），Schema 只有 `target` + `type` |
| **为什么不能替代** | 类库实现体对清单做了空对象短路 —— `FBroVip.wsv:576-578`：<br>`@ CWString temp = @an<CVolString>(@<类型>) + _CT(";");`<br>`@ if(!@<媒体硬件清单>.IsNullObject()) temp += @<媒体硬件清单>.MapToString();`<br>`@ FBroHsVIPControl_SetVirVideoInput(m_class,temp.GetText());`<br>（`FBroVip.wsv:564-566` 与 `:588-590` 同理）<br>而调用点只传了第一个参数：`MCP_Server_VIP.wsv:1064` / `:1068` / `:1072`<br>`vipMD.指纹_虚拟AudioInput设备 (MCP命令服务器.yyjson取整数 (参数JSON, "type"))` / `vipMD.指纹_虚拟AudioOutput设备 (…)` / `vipMD.指纹_虚拟VideoInput设备 (…)`<br>工具 Schema（`MCP_Server.wsv:10366`）**没有任何字段可以传设备清单**；工具成功后返回 `响应_需要刷新 ("媒体设备指纹已设置")`（`MCP_Server_VIP.wsv:1078`）。<br>`FBrowser_媒体硬件数组::加入数据` 在 `src` **严格匹配 0 命中**（同类 `删除数据`（`FBroDataType.wsv:1739`）/ `取驱动ID`（`:1745`）/ `取驱动名`（`:1751`）/ `取分组ID`（`:1757`）/ `清空全部数据`（`:1763`）同样 0 命中）—— 也**没有任何其它工具**会去构造该数组。<br>→ **静态结论**：`type=1(添加)` / `type=2(覆盖)` 恒定作用在"空清单"上；`target`+`type` 的组合无法携带设备信息。（这是"**有工具但能力空心**"，不是"没工具"。**未做真机验证** —— 是否真的无副作用留待主代理实测。） |
| **建议** | 给 `browser_vip_fingerprint_media_devices` 增加 `devices` 参数（JSON 数组 `[{"driver_id":"…","name":"…","group_id":"…"},…]`），实现侧先 `媒体硬件数组.清空全部数据 ()` 再逐条 `加入数据`，再把数组传入对应方法。 |
| **价值** | **中-高** —— 媒体设备数是常见指纹维度；现状等于该维度**不可用** |
| **风险** | **低**（纯增量参数）。注意类库原文警告"虚拟媒体设备可能会照成浏览器声音或麦克风异常无法获取到真实设备"（`FBroVip.wsv:557`）—— 需在工具描述里照抄 |
| **是否需要启动期** | **否** |

---

### 2.6 🔴 G7 —— `browser_fingerprint` 缺"只重置调用计数"

| 项 | 内容 |
|---|---|
| **能力** | 清零"指纹被调用次数"计数，**不影响**已设的指纹数据 |
| **类库文件:行** | `FBroVip.wsv:211`（对照 `FBroVip.wsv:216 指纹_取调用计数`、`FBroVip.wsv:205 清理数据`） |
| **完整签名（原文抄录）** | `FBroVip.wsv:211`<br>`方法 指纹_清空调用计数 <公开>`<br>`{`<br>`    @ if(@<FBrowser初始化控制.是否为VIP> && !IsEmpty()) FBroHsVIPControl_ClearFingerCount(m_class);`<br>`}` |
| **现有工具里最接近的** | `browser_fingerprint action=count` / `action=clear`（`MCP_Server.wsv:10190` 附近的 `browser_fingerprint` 注册；分派在 `MCP_Server_Core.wsv:2198`） |
| **为什么不能替代** | `count` 只读：`MCP_Server_Core.wsv:2215-2218` `返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))`。<br>`clear` 是**全清**：`MCP_Server_Core.wsv:2210-2213` `vip_ctrl.清理数据 ()` → `返回 (响应_需要刷新 (命令ID, "指纹已清除"))`，而 `清理数据` 的类库注释是"清理**全部**VIP设置的参数，包括指纹、代理、wss、debugger、isTrusted相关参数数据"（`FBroVip.wsv:205`）。<br>→ 想"保留指纹、只把计数归零"做不到；`指纹_清空调用计数` 在 `src` 严格匹配 0 命中。 |
| **建议** | `browser_fingerprint` 增 `action="clear_count"`（1 行分支）。 |
| **价值** | **低-中**（诊断/对照实验用） |
| **风险** | **极低** |
| **是否需要启动期** | **否** |

---

### 2.7 🔴 G8 —— `FBrowser_取初始化缓存目录`：`browser_cache_dir` 可能报的不是 CEF 真正用的目录

| 项 | 内容 |
|---|---|
| **能力** | 取"**初始化设置的真实缓存路径**"（内核解析后的），而非配置里写的路径 |
| **类库文件:行** | `FBroLib.wsv:252`（对照现用的 `FBroLib.wsv:2045`） |
| **完整签名（原文抄录）** | `FBroLib.wsv:252`<br>`方法 FBrowser_取初始化缓存目录 <公开 静态 类型 = 文本型 注释 = "取出初始化设置的真实缓存路径" @禁止流程检查 = 真>`<br>`{`<br>`    @ if(IsEmpty()) return CVolString();`<br>`    @ CefRefPtr<FBroString> fbrostring = FBroHsGetSetCachePath();`<br>`    @ return FBroUnit::FBroStringToCWString(fbrostring);`<br>`}`<br><br>`FBroLib.wsv:2045`（`类_FBrowser_请求环境`，**当前项目用的就是它**）<br>`方法 取缓存路径 <公开 类型 = 文本型 @禁止流程检查 = 真>`<br>`{`<br>`    @ if(IsEmpty()) return CVolString();`<br>`    @ CefRefPtr<FBroString> fbrostring = FBroHsRequestContext_GetCachePath(m_class);`<br>`    @ return FBroUnit::FBroStringToCWString(fbrostring);`<br>`}` |
| **现有工具里最接近的** | `browser_cache_dir`（`MCP_Server_Core.wsv:7115-7129`，返回 `reqCtx.取缓存路径 ()`）、`browser_get_global_cache_dir`（`MCP_Server_System.wsv:47-52`，**硬编码** `取运行目录 () + "\\CacheData\\GlobalData"`，连 `_Stdio` 分支都不认，见 `main.wsv:84-91`） |
| **为什么不能替代** | 两个 getter 走的是**不同的内核 API**：`FBroHsGetSetCachePath` vs `FBroHsRequestContext_GetCachePath`（`FBroLib.wsv:255` / `:2048`）。而项目**已开启自动多例模式**：`main.wsv:100 设置.启用自动多例模式 = 真`，该字段类库注释为"启用后多exe运行会自动在缓存目录下创建以 **temp** 开头的子缓存目录，避免缓存文件冲突"（`FBroDataType.wsv:37`）。<br>→ 有理由怀疑 `browser_cache_dir` 回的是**配置值**而 CEF 实际用的是 `…\temp*` 子目录。**这是本次唯一一条"疑似不准确"而非"缺功能"的项，需真机实测确认后才算成立。**<br>另外 `browser_get_global_cache_dir` 的 `_Stdio` 分支缺失是**已确认的硬编码缺陷**（不受实测影响）。 |
| **建议** | `browser_cache_dir` 回包增加 `real_cache_dir` 字段（两个 API 并列返回，差异自现）；顺手修 `browser_get_global_cache_dir` 的 `_Stdio` 分支。 |
| **价值** | **低-中**（涉及"清理缓存 / 取证 / 落盘"类操作的准确性） |
| **风险** | **低** |
| **是否需要启动期** | **否** |

---

### 2.8 🔴 G9 —— `FBrowser_Parser_取数据URI`：没有 data URI 组装

| 项 | 内容 |
|---|---|
| **能力** | 由 MIME + 数据直接构造 `data:<mime>;base64,…` 形式的 URI |
| **类库文件:行** | `FBroLib.wsv:394` |
| **完整签名（原文抄录）** | `FBroLib.wsv:394`<br>`方法 FBrowser_Parser_取数据URI <公开 静态 类型 = 文本型 @禁止流程检查 = 真>`<br>`参数 mimetype <类型 = 文本型>`<br>`参数 数据 <类型 = 文本型>` |
| **现有工具里最接近的** | `browser_base64_encode`（`MCP_Server.wsv:10220`，工具序 108）/ `browser_codec`（`MCP_Server.wsv:10224`，工具序 112）/ `browser_time_convert` / `browser_hash`（`MCP_Server.wsv:10226`） |
| **为什么不能替代** | 现有能力只出**裸 base64**，没有 `data:<mime>;base64,` 前缀组装（`FBrowser_Parser_取数据URI` 在 `src` 严格匹配 0 命中）。调用方自己拼要处理 MIME 缺省（类库实现里对空 mimetype 有兜底逻辑），属易错点。 |
| **建议** | 并入 `browser_codec`（新增 `op="data_uri"`，参数 `mime` + `data`）。 |
| **价值** | **低** |
| **风险** | **极低** |
| **是否需要启动期** | **否** |

---

### 2.9 🔴 G10 —— `类_FBrowser_菜单模式`：只读 / 按**索引**寻址 / 颜色字体 全缺（价值中，风险高，建议**先做可行性探针**）

| 项 | 内容 |
|---|---|
| **能力** | ① 读回菜单条目（标签/类型/分组ID/子菜单/快捷键）② 按**位置索引**寻址菜单条目（`_索引` 族）③ 条目颜色/字体 |
| **类库文件:行** | 读回 `FBroLib.wsv:3371` / `3386` / `3392` / `3398`；索引族与快捷键 `3444` / `3457` / `3474` / `3490` / `3496` / `3517`；颜色 `3538` / `3550` / `3563` / `3586`；字体 `3609` / `3616` |
| **完整签名（原文抄录，代表项）** | `FBroLib.wsv:3398`（`类_FBrowser_菜单模式`）<br>`方法 取子菜单 <公开 类型 = 类_FBrowser_菜单模式 注释 = "英文名：AddSubMenu" @禁止流程检查 = 真>`<br>`参数 命令ID <类型 = 整数>`<br><br>`FBroLib.wsv:3444`<br>`方法 选中状态_索引 <公开 类型 = 逻辑型 注释 = "英文名：SetCheckedAt" @禁止流程检查 = 真>`<br>`参数 索引ID <类型 = 整数>`<br>`参数 选中 <类型 = 逻辑型>`<br><br>`FBroLib.wsv:3496`<br>`方法 取快捷键 <公开 类型 = 逻辑型 注释 = "只是用于显示快捷键，触发需自行用键盘事件实现" @禁止流程检查 = 真>`<br>`参数 命令ID <类型 = 整数>`<br>`参数 键代码 <类型 = 整数类 注释 = "key_code，返回数据">`<br>`参数 返回是否按下shift值 <类型 = 逻辑型类 注释 = "shift_pressed，返回数据" "">`<br>`参数 返回是否按下ctrl值 <类型 = 逻辑型类 注释 = "ctrl_pressed，返回数据" "">`<br>`参数 返回是否按下alt值 <类型 = 逻辑型类 注释 = "alt_pressed，返回数据" "">`<br><br>`FBroLib.wsv:3538`<br>`方法 置颜色 <公开 类型 = 逻辑型 @禁止流程检查 = 真>`<br>`参数 命令ID <类型 = 整数>`<br>`参数 颜色类型 <类型 = 整数 注释 = "color_type 参考：菜单颜色类型.">`<br>`参数 A <类型 = 整数 @默认值 = 0>` / `参数 R <类型 = 整数 @默认值 = 0>` / `参数 G <类型 = 整数 @默认值 = 0>` / `参数 B <类型 = 整数 @默认值 = 0>` |
| **现有工具里最接近的** | `browser_context_menu`（`MCP_Server.wsv:10191`），已支持 `item/check/radio/sep/sub` + `del/relabel/vis/dis/mark/accel/noaccel` |
| **为什么不能替代** | 现工具的寻址口径**只有命令ID**，且已实测"指向浏览器默认菜单项（标准 ID 100..130 或其别名 back/reload/copy 等）的修改类**不会生效**"（`MCP_Server.wsv:10191` 描述 + `MCP_Server_Core.wsv:2971-2973` 的 `cm警告`）。<br>而 `_索引` 族是**按位置寻址**（英文名即 `SetCheckedAt` / `HasAcceleratorAt` / `SetAcceleratorAt`），是绕过"改不动默认项"的**唯一现成路径**。`取菜单标签` 等只读方法也不存在任何工具，导致 `browser_context_menu action=get` 只能回自建规格、无法回读 CEF 实际菜单。<br>（CEF 明确禁止在回调之外持有菜单对象 —— 现工具自述"**不能即时修改当前已打开的菜单**，只能先 set 预置规格"，所以 `_索引` 族只能**在右键回调内**使用。） |
| **建议** | **先做可行性探针**：在 `类_MCP_浏览器事件` 的右键回调内对默认条目按索引施加 `dis`/`vis`，看是否生效（这是对整个 `_索引` 族的一次性判定）。生效则给 `browser_context_menu` 的规格行增加 `@索引ID` 写法 + 新增 `action=read` 读回。 |
| **价值** | **中**（把"查看源代码 / 另存为"等内置项从菜单里去掉、读回真实菜单） |
| **风险** | **中-高**：整个菜单领域已多轮实测（`_audit/_menu_api_r100.md`、`_audit/shot_menu_visual_truth.py`、`_audit/shots/arm_hide_find.png` 等），按命令ID改默认项**已证伪**，按索引**未测**；`置颜色` / `置字体` 类库自带 `注释 = "待验证"`（`FBroLib.wsv:3609` / `:3616`），纯渲染，价值低。**不建议直接开工，先探针。** |
| **是否需要启动期** | **否** |

---

## 3. 主动排除项与依据（历史误报高发区）

### 3.1 事件侧剩余 3 项（`FBroEventControl.wsv`，150 公开方法 → 147 已接，3 未接）

| 方法 | 行 | 判定 | 依据 |
|---|---|---|---|
| `即将查询` | `FBroEventControl.wsv:1790` | **排除（已实现过 → 已移除 / 旧轮次判覆盖）** | `_audit/add_js_query_bridge.py`（第 2 行标题即写"实现 non-CDP 的 JS↔宿主查询通道（**A 组第 3 缺口**: FBrowser_JS交互_注册/删除）"）→ 落地了 `browser_js_query`；随后 `_audit/remove_js_query_bridge.py`（第 56 / 84 / 86 / 87 行专门删除 `类_MCP_JS交互事件`、`添加工具JSON ("browser_js_query"`、命令注册表项、双变体）**把它移除了**。旧轮次判定覆盖路径：`_audit/_classlib_gap_confirmed2.md:378-379`（`browser_kernel_ipc_queue` / `browser_ipc_send_to` 构成的双工 IPC）、同文件 `:432-437`；`_audit/_cg2_verdict.json` 中 `类_FBrowser_JS交互事件::即将查询` 亦判 **B1**。另有轮次主张"值得做"：`_audit/_gap_events_r114.md:427` —— "**值得，但需要页面侧配合**（网页必须自己调 `cefQuery`，项目无法单方面触发）。属\"能力扩展\"而非\"缺陷修补\""。<br>→ **不是"没做过"，是"做过又被撤了 + 被判覆盖"**。是否重开请主代理定，本报告不将其列为新缺口。 |
| `即将取消查询` | `FBroEventControl.wsv:1808` | 同上 | 同上（`_audit/_classlib_gap_confirmed2.md:437`；`_audit/_gap_events_r114.md:423`；`_audit/_events_patch_plan_r115.md:562` 明确写"不在本轮 12 项清单内；且接入需要**新建第三个子类**（项目 `src/` 内 `类_FBrowser_JS交互回调` **0 命中**）"） |
| `上传进度` | `FBroEventControl.wsv:2314` | **排除（需 flags 形参，本机永不回调）** | 签名 `FBroEventControl.wsv:2314`<br>`方法 上传进度 <公开>`<br>`参数 标识 <类型 = 长整数>` / `参数 URL请求 <类型 = 类_FBrowser_URL请求>` / `参数 当前大小 <类型 = 长整数>` / `参数 合计大小 <类型 = 长整数>`<br>本项目 URL 请求走 GET 下载路径（`MCP_Server_Core.wsv:6900-6933` 只设地址/类型，从不设 POST 体），且已接的是**下载**进度（`MCP_Callbacks.wsv:856 方法 下载进度`）。`_audit/_events_patch_plan_r115.md:144` 亦写"剩余 3 项不是本轮范围：`类_FBrowser_JS交互事件`(2) + `上传进度`(1)" |
| 其余 147 已接 | — | **排除** | `_audit/event_gap.py` 已覆盖到 147/150。**衍生收益**：若 G2 支持 POST 体，`上传进度` 才会有意义 —— 可一并考虑 |

### 3.2 项目**刻意不实现**（有守卫分支，勿再报）

- `browser_create_tab` —— `MCP_Server_System.wsv:16-19`：`// VIP 标签页入口: 本项目**不开放**远程建标签页` → `返回 (响应构建.命令失败 (… "⛔ 远程创建标签页已禁用 | 原因: 本工具**刻意不实现**…"))`
- `browser_task_runner_post` —— `MCP_Server_System.wsv:20-23`：`"⛔ 远程 task_runner 创建浏览器已禁用 | 原因: 本工具**刻意不实现**…"`
  → **连带排除** `类_FBrowser_任务运行器` 全部 **12 个**公开方法 —— 逐行抄录（均 `FBroLib.wsv`）：`FBrowser_任务运行器_取当前 :2771`、`FBrowser_任务运行器_取指定线程 :2777`、`FBrowser_任务运行器_是否指定线程上调用 :2784`、`FBrowser_任务运行器_投递任务 :2791`、`FBrowser_任务运行器_投递任务_延迟 :2804`、`是否为空 :2818`、`置空 :2823`、`是否相同 :2830`、`是否为当前线程 :2837`、`是否为指定线程 :2843`、`投递任务 :2850`、`投递延时任务 :2865`；以及依赖它的 `FBrowser_创建浏览器_同步`（`FBroLib.wsv:573`，类库注释"只能通过：FBrowser_任务运行器_投递任务 的方式创建"）、`FBrowser_创建后台浏览器_同步`（`FBroLib.wsv:615`）

### 3.3 本机不适用 / 永不回调

| 项 | 行 | 排除依据 |
|---|---|---|
| **OSR 离屏渲染族（17 个）** | `FBroLib.wsv:1160` / `1166` / `1174` / `1183` / `1194` / `1204` / `1213` / `1225` / `1252` / `1267` / `1278` / `1287` / `1301` / `1312` / `1321` / `1331` / `1346` | 初始化未开离屏：`FBrowser_初始化配置::启用离屏渲染`（`FBroDataType.wsv:15`）在 `src` 0 命中；项目走窗口浏览器（`main.wsv:233`）或**后台无窗口浏览器**（`main.wsv:226`），OSR 回调不产生；截图能力已由 `browser_screenshot` 覆盖（`MCP_Server.wsv:10193` 描述 `format=png/jpeg/webp`） |
| `FBrowser_启用异常收集` | `FBroLib.wsv:531` | **类库自带注释即判死**：`方法 FBrowser_启用异常收集 <公开 静态 注释 = "火山版本内置已经设置了，所有这个没用" @嵌入式方法 = "">`；且是 `@嵌入式方法`。历史审计曾反复把它当缺口，**本次明确排除** |
| `FBrowser_消息循环_*`（4 个） | `FBroLib.wsv:121` / `127` / `133` / `139` | 项目**自建消息泵**：`main.wsv:112-144`（手写 `PeekMessageW` 循环）+ `main.wsv:95 设置.启用系统消息循环 = 真` |
| `FBrowser_设置程序DPI模式` | `FBroLib.wsv:260` | 类库注释"**在程序入口初始化之前调用**"；本项目是控制台程序（`MCP_Stdio.wsv:214` 起检测 `--mcp-stdio`），无 DPI 感知需求 |
| `FBrowser_初始化_设置V8环境默认堆栈大小` | `FBroLib.wsv:184` | 类库注释"**必须在初始化之前设置**"，且同一语义已由初始化配置字段 `uncaught_exception_stack_size`（`FBroDataType.wsv:29`，映射见 `:69`）覆盖 —— 该字段当前 0 引用，**归入 G3 残余的"启动期配置面"一并处理**，不单列 |
| `FBrowser_取初始化缓存目录` | `FBroLib.wsv:252` | **不排除**（→ G8） |
| **渲染进程专用** | `FBroLib.wsv:1685 取V8环境`（注释"**只能在渲染进程中调用**"）、`FBroLib.wsv:1698 访问DOM对象`（注释"VisitDOM，**只能在渲染进程中调用**"）、`FBroLib.wsv:1676 发送进程消息`（需自建 `类_FBrowser_进程消息`）、`FBroLib.wsv:1017 发送触摸事件`（主进程触摸注入，已由 CDP `browser_touch_press` / `browser_touch_release` / `browser_touch_move` + `browser_vip_touch_emulation` / `browser_vip_touch_cancel` 覆盖） | 主进程侧不可达 / 已有等价路径 |
| **生命周期绑回调栈的类型** | `类_FBrowser_V8环境`（`FBroLib.wsv:3838`-`3905`）、`类_FBrowser_V8异常`（`:3952`-`3986`）、`类_FBrowser_V8堆栈踪迹/框架`（`:4024`-`4105`）、`类_FBrowser_同步辅助类`（`:4904`-`5107`）、`类_FBrowser_读取流`（`:4834`-`4885`）、`类_FBrowser_事件智能指针`（`:281`-`319`）、`类_FBrowser_请求/响应/POST数据/POST元素`（作为**参数类型**已在 G2 使用，其余 getter 在回调内才有意义） | 这些对象只能从事件/回调栈内取得，主进程无法独立构造；`FBroValue.wsv` 101 条 0 引用方法绝大多数属于此类 |
| **纯界面/样式，或不缺工具** | `类_FBrowser_菜单模式::置颜色/置字体` 族（`FBroLib.wsv:3538`-`3616`，类库自带 `注释 = "待验证"`）→ 归 G10；`类_FBrowser_图片::取图片数据_BMP`（`:2184`）/`取图片数据_JPG`（`:2206`）→ 截图已支持 `format=png/jpeg/webp`（`MCP_Server.wsv:10193`），BMP 无等价但价值低；`FBrowser_浏览器::显示隐藏窗口`（`FBroLib.wsv:1071`）/`移动窗口`（`:1058`）/`置窗口属性`（`:1092`）/`取窗口属性`（`:1100`）→ 均已有工具（`browser_show_window` / `browser_move_window` / `browser_set_window_style` / `browser_get_window_style`） | 等价工具已存在或价值过低 |
| **服务端连接生命周期** | `类_FBrowser_服务器::发送Http200响应`（`FBroLib.wsv:4740`）/`404`（`:4753`）/`500`（`:4761`）、`关闭连接`（`:4789`）、`是否有效连接`（`:4733`）、`是否存在连接`（`:4727`）、`是否运行中`（`:4712`）、`取服务器地址`（`:4720`） | 这是 CEF 服务器**连接事件内**的应答 API，已由 `类_MCP_服务器事件`（`MCP_Server_HTTP.wsv:7`，含 `服务器即将创建` `:9`）在服务器事件通道内处理；绑定成败已由 `服务器.是否为空()` 回填（`MCP_Server.wsv:89` 变量注释"由 服务器即将创建 事件写入: 服务器对象非空即绑定成功"；`MCP_Server.wsv:8745` 注释 `// 服务器.是否为空() 可靠回填(CEF 仅在绑定成功时才传入有效服务器对象)。`；创建点 `MCP_Server.wsv:8755`）—— 属只读诊断，价值低，不列缺口 |
| **DOM 节点/文档 getter（约 40 个）** | `类_FBrowser_DOM节点`（`FBroLib.wsv:4145`-`4295`）、`类_FBrowser_DOM文档`（`:4336`-`4401`） | **`browser_cdp_call` 是 CDP 全量透传**（依据 `_audit/_classlib_gap_recheck.md:192`）→ `DOM.getDocument` / `DOM.getAttributes` / `DOM.querySelectorAll` / `DOM.getBoxModel` 全覆盖；原生侧另有 `browser_dom_query`（`MCP_Server.wsv:10177`，带 `attribute` 参数）、`browser_fill_attr_get`、`browser_dom_rect`、`browser_dom_inner_html`、`browser_vip_dom_get_document`（`MCP_Server.wsv:10373`）、`browser_vip_dom_search`（`MCP_Server.wsv:10374`）。仅 `取全部属性值`（`FBroLib.wsv:4273`）无同位原生工具，但 CDP 等价存在 |
| `FBrowser_浏览器_通过序号取浏览器` | `FBroLib.wsv:487` | `browser_list`（`MCP_Server.wsv:10129`，工具序 17）已给 id 清单，按序号取无增量。**这是"只按工具名精确匹配"的典型误报样例** |
| `FBrowser_启用自带调试提示` | `FBroLib.wsv:27` | 类库注释"**仅调试模式下有用**"，且自述"全部类初始化在全局所以该设置屏蔽不到已经初始化的事件类" —— 调试噪音控制，非能力 |
| `FBrowser_Parser_字节值解析为JSON` / `写入JSON` | `FBroLib.wsv:443` / `450` | 参数类型是 `类_FBrowser_字节集` / `类_FBrowser_值` —— 内部 CEF value 对象，主进程无从构造（现有 JSON 走 yyjson 模块：`MCP_Server.wsv` 的 `yyjson取文本` 等） |
| `类_FBrowser_拖拽数据` 族（约 17 条） | `FBroValue.wsv:1549`-`1696` | 主进程拖拽需 OSR/窗口拖拽事件源；CDP `Input.dispatchDragEvent` 可经 `browser_cdp_call` 透传 |
| `FBrowser_文本数组::到火山文本数组` | `FBroDataType.wsv:1057` | 纯转换助手；现有代码用 `取成员数` / `取成员` 循环读（`MCP_Server_Core.wsv:6891`），功能已达成 |
| `FBrowser_双文本数组::取当前位置数据_关键字` / `取当前位置数据_数据` / `置当前位置数据` / `删除数据` | `FBroDataType.wsv:867` / `875` / `884` / `901` | 游标式容器 API，无调用方需求 |
| `FBrowser_文本数组::置当前位置数据` / `删除数据` | `FBroDataType.wsv:1033` / `1041` | 同上 |
| `指纹_清空调用计数` | `FBroVip.wsv:211` | **不排除**（→ G7） |
| `指纹_虚拟*设备` 接收方本身 | `FBroVip.wsv:557` / `569` / `581` | **不排除**（→ G6：工具在，清单恒空） |
| `过滤器_取消修改内容` / `过滤器_取消替换资源`（**按 URL 单条撤销**） | `FBroVip.wsv:1147` / `1186` | **排除（本项目已实现等价能力）**：`browser_intercept` 现有 `unmodify` / `unreplace`（`MCP_Server.wsv:10192`；实现 `MCP_Server_Core.wsv:2634` / `:2641`）。旧轮次 `_cg2_verdict.json` 把它判为 **A（缺口）**，**该缺口现已关闭，勿重复立项** |
| `高级_设置触发鼠标触摸事件` / `高级_发送触摸事件` / `高级触摸_单击` / `高级_发送键盘事件` | `FBroVip.wsv:623` / `866` / `920` / `932` | CDP 等价：`Emulation.setEmitTouchEventsForMouse` / `Input.dispatchTouchEvent` / `Input.dispatchKeyEvent` 均可经 `browser_cdp_call` 透传；项目亦已有 `browser_vip_touch_emulation` / `browser_vip_touch_cancel` / `browser_touch_*` / `browser_vip_key_*` |
| `类_FBrowserVIP_开发者DOM` 写方法族 | `FBroVip.wsv:1503`-`1666`（`置焦点元素 1503` / `移除节点属性 1509` / `移除节点 1517` / `置节点属性文本 1523` / `置节点属性值 1531` / `置节点值 1539` / `置节点源码 1546` / `清除查找 1553` / 取节点属性 `1577` / 取节点源码 `1595` / 取节点_查询选择器 `1612` / 取全部节点_查询选择器 `1630` / 置节点名 `1648` / 取节点容器 `1666`） | CDP 全量透传（`DOM.removeNode` / `DOM.setAttributeValue` / `DOM.setOuterHTML` / `DOM.querySelectorAll` / `DOM.getAttributes`）已覆盖；原生侧另有 `browser_dom_set_html` / `browser_fill_attr_set` / `browser_get_text` / `browser_dom_query` |
| `FBrowser_浏览器::尝试关闭浏览器` | `FBroLib.wsv:796` | `browser_close` / `browser_close_try` 已存在 |
| `FBrowser_浏览器::进程间消息_取渲染进程数量` | `FBroLib.wsv:1137` | `browser_ipc_renderer_count` / `browser_ipc_renderer_ids` 已存在（后者从清单逐项取数，见 `MCP_Server_Core.wsv:6891`） |
| `类_FBrowser_下载图片回调` + `取图片数据_PNG` | `MCP_Callbacks.wsv:946` 起 | 已在用（`browser_download_image`，`MCP_Server.wsv:10157`）；BMP/JPG 变体见上 |
| **`browser_create_url_request` 之外的请求环境族**：`类_FBrowser_请求环境::创建_其他`（`FBroLib.wsv:2023`）、`取Cookie管理器`（`:2053`）、`是否为全局`（`:2010`）、`是否为分享`（`:2037`）、`VIP_高级_取插件名`（`:2117`） | — | **列为"候选但本轮不立项"**：`创建`（`FBroLib.wsv:2016`）+ `创建_其他` 理论上可做**每浏览器独立 Cookie/缓存（多账号隔离）**，但当前 `browser_create` 不接请求环境（`main.wsv:226` / `:233` 第 4 实参留空）、`browser_request_context` 只回 `has_context`（`MCP_Server_Core.wsv:6587-6594`）—— 这是**高价值但高风险**（独立缓存目录、与 `启用自动多例模式`、VIP 代理"独立缓存才独立"注释 `FBroVip.wsv:631` 相互纠缠）的架构级改动；且全局 Cookie 管理器已覆盖绝大多数需求（`FBrowser_Cookie管理器_取全局` 用于 `browser_get_cookies`（`MCP_Server_Core.wsv:1089`）、`browser_set_cookie`（`:1262`）、`browser_delete_cookies`（`:1273`）、`browser_refresh_cookies`（`MCP_Server_VIP.wsv:1275`）、`browser_get_all_cookies`（`:1285`））。**建议单开一轮做可行性评估，不并入本轮。** |

---

## 4. 我认为最该做的 3 项及理由（供下一轮排期）

> 说明：原本的"第 3 项"是 G3（CEF 启动期命令行开关），**它已在本次审计期间被主代理实现**（见 §2.0）。因此下面第 3 项改为**补完 G3 残余**（复用刚建好的通道，成本极低、价值仍高）。

### 第 1 项：G1 —— 给 12 个 `browser_fill_*` 加 `frame` 参数（子框架原生填表）

**理由**
- **性价比最高**：改动面 = 12 个 Schema 各加 1 个可选参数 + 一个统一的"填表框架解析"函数（`取填表框架_ID` / `取填表框架_名称` / `取焦点填表框架`），**不新增工具名、不改架构、不需要启动期**。
- **覆盖面大**：`src` 里 **23 处**填表/DOM 入口**全部**硬编码 `取主填表框架 ()`，这是一条**结构性天花板**，不是零散小缺口。iframe 内的表单在真实站点里占比极高。
- **唯一必须尊重的约束已在类库原文里写明**（`FBroLib.wsv:1414` / `:1422`："类为空而执行操作会导致奔溃"）—— 判空即可，属可控风险。
- 与项目的反检测定位一致：走**原生非 JS**通道，不像 `browser_vip_execute_js_context` 那样"会破坏本会话 CDP 通道且需重启恢复"（`MCP_Server.wsv:10371`）。

### 第 2 项：G2 —— 把 `browser_create_url_request` 从"只回正文"补成"完整 HTTP 客户端"

**理由**
- **修的是语义盲区，不只是缺功能**：当前回调**连 HTTP 状态码都不读**（`MCP_Callbacks.wsv:800-833`），工具描述里的 `success:true` 无法区分 200 与 404 —— 这是会**误导 AI 调用方**的缺陷。
- **全部能力都是类库现成公开方法**：`类_FBrowser_请求::设置(地址, 类型, POST数据, 协议头数据)`（`FBroLib.wsv:2407`）一次给全；读回侧 `取请求状态码` / `取请求错误码` / `取响应` / `是否带缓存响应`（`FBroLib.wsv:5579` / `5585` / `5591` / `5597`）。改动面小、风险低。
- **顺带解锁两件事**：① POST 表单 + 认证头请求；② 接上 `上传进度` 事件（见 §3.1）—— 目前它因"项目从不发 POST 体"而无意义。
- 与既有工具**边界干净**：`browser_network*` 是被动抓包、`browser_execute_js` 的 fetch 受 CORS 且在渲染进程。三者不可互替，补齐后形成"被动观察 / 渲染侧 / 主进程侧"三条清晰路径。

### 第 3 项：G3 残余 —— 在刚建好的启动期通道上补完 3 个高价值开关

**理由**
- **通道已经建好，边际成本极低**：`main.wsv:499-532` 已有"浏览器进程门控 + 白名单 if 分支 + `取字符串` 回读 + `命令行开关已应用` 回执"的完整骨架；补一项 = 一个 if 分支 + 一个 `启动开关_*` 静态开关 + 一个配置字段。
- **优先补这三项**：
  1. `启用跨框架操作模式`（`FBroLib.wsv:1888`）—— **与第 1 项组合后价值升为高**：G1 让原生填表能定位 iframe，本开关解除跨域框架的操作限制，两者合起来才真正打通 iframe 自动化；
  2. `禁用代理`（`FBroLib.wsv:1968`）—— 排障"代理设坏了全站打不开"的唯一干净手段；
  3. `置项值` / `插入值` / `置额外参数`（`FBroLib.wsv:1835` / `1865` / `1857`）做成**受控白名单表**（不是自由文本），覆盖 `--disable-blink-features=AutomationControlled`、`--lang=…` 一类排障/反检测开关。
- **两条既有约定必须继续遵守**（主代理已写在 `main.wsv:487-494`）：① 只在 `进程类型 == ""`（浏览器进程）施加；② 白名单，绝不自由文本透传。
- **⚠️ 必须记住的类库 Bug（主代理已发现，勿重复踩）**：`FBroLib.wsv:1909` `启用无头模式` 的方法体实为 `FBroHsCommandLine_EnableAutoplayPoliey`（与 `启用自动播放` 同一函数），**名实不符，禁止接线**（`main.wsv:493-494`）。

### 另附：3 个「1 小时级、可顺手做掉」的项

1. **G6 修"假成功"** —— `browser_vip_fingerprint_media_devices` 的设备清单**恒未传入**（`MCP_Server_VIP.wsv:1064` / `1068` / `1072` 只传 `type`；类库按 `IsNullObject()` 短路 `MapToString()`，`FBroVip.wsv:565` / `577` / `589`）。加 `devices` 参数 + 3 行 `加入数据` 即修好；现在这个工具在"1添加/2覆盖"上是空动作却回"已设置"。**优先于 G7/G9。**
2. **G7** `browser_fingerprint` 加 `action=clear_count`（1 行分支）。
3. **G8 的第二半** —— `browser_get_global_cache_dir`（`MCP_Server_System.wsv:47-52`）**硬编码 `CacheData\GlobalData`**，不认 `_Stdio` 分支（`main.wsv:84-91` 实际会用 `GlobalData_Stdio`）—— 这是**不受实测影响的已确认缺陷**，顺手修。

---

## 5. 本次未做的事 / 待主代理真机验证的点

- **未做任何真机验证**：G1–G10 全部是静态核对结论。特别需要实测确认的：
  - G6：`type=1/2` + 空清单是否真的无任何效果（静态看是"没东西可加"，但内核侧会不会有副作用需实测）；
  - G8：`FBrowser_取初始化缓存目录` 与 `取缓存路径` 是否真的不同（有 `启用自动多例模式`（`main.wsv:100`）作旁证，但未证）；
  - G10：`_索引` 族对**默认菜单项**是否生效（决定这一族值不值得做）；
  - G4：VIP 过滤器与手写通道在同一 URL 上的抢占行为（类库原文只给了"事件将不会被触发"这一句）。
- **未读/未纳入**：`FBroCallback.wsv`（176,190 B，回调基类集合）、`FBroConst.wsv`（112,956 B）、`FBroHelp.wsv` —— 任务只指定了 4+1 个文件；`FBroConst.wsv` 仅在需要枚举名时按行引用（`URL请求状态` `FBroConst.wsv:718`、`DPI模式` `FBroConst.wsv:759`）。
- **并发改动导致的结论时效性**：本文对 `MCP_Server.wsv` 的行号取证截止于该文件 **688,180 字节 / 11,540 行** 的版本；`main.wsv` 截止于 **`即将处理命令行` 已含 6 项开关** 的版本。**若这两处行号对不上，请以本报告中同时给出的工具名/方法名锚点重新 grep 定位。**
- **`_audit/_cg2_verdict.json` 改判请求**：仅 G4 一条（4 个方法从 B2 申请改判），理由与差异点已在 §2.3 "为什么不能替代"里写明。
- **对 `_audit/verify_startup_switches_r117*.py` 的说明**：本文**未调用、未读取其运行结论**（它们是主代理的并发工作产物，不在本任务的只读清单内）；§2.0 的判定完全基于我自己对 `main.wsv:480-548` 的实读。
