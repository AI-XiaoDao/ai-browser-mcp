# 命令行(开关)能力面缺口审计 — R114

- **范围**: 只读分析。未编译、未调用 MCP、未访问 127.0.0.1:9222、未重启程序、未改 `src/` 及任何其它 `_audit` 文件。
- **权威 API 面**: `C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroLib.wsv`(下称 FBroLib)、`FBroConst.wsv`、旁证 `FBroDataType.wsv` / `FBroEventControl.wsv`。
- **项目侧**: `src/*.wsv`(`*~vbak.wsv` 备份已排除)。
- **工具总数核对**: 按 `添加工具JSON (` 提取 = **316**,全部注册在 `src/MCP_Server.wsv`(10262–10613 区间)。与题面一致。
- **验证边界**: 本报告只做**静态**判定。任何"实际是否生效"均需主代理真机验证,本报告**不声称已验证可用**。

---

## A. `类 类_FBrowser_命令行` 公开方法全量清单(31 个)

类定义: `FBroLib.wsv:1733` `类 类_FBrowser_命令行 <公开 @输出名 = "FBroCommandLine" @全局类 = 真 "">`,类体 `1733–1974`。
内部封装 `CefRefPtr<CefCommandLine> m_class`(`FBroLib.wsv:1738`)。

### A1. 静态构造/取用(2)

| # | 行号 | 原文声明 | 完整签名 |
|---|---|---|---|
| 1 | 1747 | `方法 FBrowser_命令行_创建 <公开 静态 类型 = 类_FBrowser_命令行 @禁止流程检查 = 真>` | `FBrowser_命令行_创建() → 类_FBrowser_命令行`;体内 `FBroHsCommandLine_CreateCommandLine()`(1749) |
| 2 | 1753 | `方法 FBrowser_命令行_取全局 <公开 静态 类型 = 类_FBrowser_命令行 @禁止流程检查 = 真>` | `FBrowser_命令行_取全局() → 类_FBrowser_命令行`;体内 `FBroHsCommandLine_GetGlobalCommandLine()`(1755) |

### A2. 通用开关读写(18)

| # | 行号 | 原文声明 | 完整签名 | CEF 对应 |
|---|---|---|---|---|
| 3 | 1758 | `方法 是否为空 <公开 类型 = 逻辑型>` | `是否为空() → 逻辑型` | IsEmpty |
| 4 | 1763 | `方法 置空 <公开>` | `置空() → 无返回` | — |
| 5 | 1770 | `方法 是否有效 <公开 类型 = 逻辑型 注释 = "英语名：IsValid"` | `是否有效() → 逻辑型` | IsValid |
| 6 | 1778 | `方法 是否只读 <公开 类型 = 逻辑型 注释 = "英语名：IsReadOnly"` | `是否只读() → 逻辑型` | IsReadOnly |
| 7 | 1784 | `方法 取字符串 <公开 类型 = 文本型 注释 = "英语名：GetCommandLineString"` | `取字符串() → 文本型` | GetCommandLineString |
| 8 | 1792 | `方法 取程序 <公开 类型 = 文本型 注释 = "英语名：GetProgram 说明：取出执行程序名，包含路径"` | `取程序() → 文本型` | GetProgram |
| 9 | 1800 | `方法 置程序 <公开 注释 = "英语名：SetProgram"` | `置程序(程序名:文本型) → 无返回`(参数 1801,`注释="带路径"`) | SetProgram |
| 10 | 1806 | `方法 是否存在项 <公开 类型 = 逻辑型 注释 = "英语名：HasSwitches"` | `是否存在项() → 逻辑型` | HasSwitches |
| 11 | 1811 | `方法 是否存在某项 <公开 类型 = 逻辑型 注释 = "英语名：HasSwitch 说明：name前面不用加\"--\""` | `是否存在某项(项目名:文本型) → 逻辑型`(参数 1812) | HasSwitch |
| 12 | 1819 | `方法 取项值 <公开 类型 = 文本型 注释 = "英语名：GetSwitchValue 说明：name前面不用加\"--\""` | `取项值(项目名:文本型) → 文本型`(参数 1820) | GetSwitchValue |
| 13 | 1828 | `方法 置值 <公开 注释 = "英语名：AppendSwitch 说明：value默认前面要加\"--\""` | `置值(值:文本型) → 无返回`(参数 1829) | AppendSwitch |
| 14 | 1835 | `方法 置项值 <公开 注释 = "英语名：AppendSwitchWithValue 说明：name默认前面要加\"--\""` | `置项值(项目名:文本型, 项目值:文本型) → 无返回`(参数 1836–1837) | AppendSwitchWithValue |
| 15 | 1843 | `方法 是否存在额外参数 <公开 类型 = 逻辑型 注释 = "英语名：HasArguments"` | `是否存在额外参数() → 逻辑型` | HasArguments |
| 16 | 1849 | `方法 取额外参数 <公开 类型 = 文本型 注释 = "英语名：GetArguments"` | `取额外参数() → 文本型` | GetArguments |
| 17 | 1857 | `方法 置额外参数 <公开 注释 = "英语名：AppendArgument"` | `置额外参数(参数文本:文本型) → 无返回`(参数 1858) | AppendArgument |
| 18 | 1865 | `方法 插入值 <公开 注释 = "英语名：PrependWrapper 说明：在当前命令之间插入值..."` | `插入值(值:文本型) → 无返回`(参数 1867) | PrependWrapper |

### A3. 语义化开关(11)

| # | 行号 | 类库注释原文(节录) | 完整签名 |
|---|---|---|---|
| 19 | 1874 | `命令行--single-process，只为了方便多进程模拟调试，仅调试模式下有用，单进程模式存在各种问题，不建议发布软件使用` | `启用单进程模式() → 无返回` |
| 20 | 1881 | `命令行enable-media-stream,允许浏览使用摄像头` | `启用摄像头() → 无返回` |
| 21 | 1888 | `跨框架操作，解除框架和框架直接不能直接操作的限制，存在不安全性` | `启用跨框架操作模式() → 无返回` |
| 22 | 1895 | `命令行：enable-speech-input,允许浏览使用话筒` | `启用录音() → 无返回` |
| 23 | 1902 | `命令行：autoplay-poliey，支持绝对部分视频网站自动播放视频，各别有限制的除外` | `启用自动播放() → 无返回` |
| 24 | 1909 | `命令行：--headless，无头模式` | `启用无头模式() → 无返回` ⚠**见下** |
| 25 | 1916 | `命令行：--remote-debugging-port` | `设置远程调试端口(端口号:整数) → 无返回`(参数 1917) |
| 26 | 1924 | `禁用后，网页渲染将由CPU处理，会提高CPU占用，不兼容的显卡只能禁用GPU否者网页可能渲染失败` | `禁用GPU() → 无返回` |
| 27 | 1931 | `禁止GPU创建缓存文件及文件夹` | `禁用GPU缓存() → 无返回` |
| 28 | 1938 | `内核内置不兼容部分显卡，设置后忽略内核这个设置，能有效解决部分显卡不兼容的问题...只有禁用GPU` | `忽略GPU禁用清单() → 无返回` |
| 29 | 1945 | `设置全局代理，只能设置一个，如果需要认证则需要设置账号密码；不支持带账号密码的S5代理，如要使用带账号密码的S5代理，请使用"VIP_高级_设置全局代理"` | `设置全局代理(代理地址:文本型, 代理账号:文本型="", 代理密码:文本型="") → 无返回`(参数 1946–1948) |
| 30 | 1955 | `设置全局代理，只能设置一个，如果需要认证则需要设置账号密码；带账号密码的S5代理，需赞助会员才可使用` | `VIP_高级_设置全局代理(代理地址:文本型, 代理账号:文本型="", 代理密码:文本型="", 关闭S5错误提示:逻辑型=假) → 无返回`(参数 1956–1959);体内有 VIP 门控 `if(@<FBrowser初始化控制.是否为VIP> && !IsEmpty())`(1961) |
| 31 | 1968 | `命令行：--no-proxy-server，禁止使用代理和系统的自动检测代理功能` | `禁用代理() → 无返回` |

### A4. 读类库原文发现的两处类库自身缺陷(影响工具设计,非本报告臆测)

| 缺陷 | 证据 | 后果 |
|---|---|---|
| **`启用无头模式` 未加 `--headless`** | `FBroLib.wsv:1909` 声明注释写 `--headless`;但其方法体 `1912` 为 `@ FBroHsCommandLine_EnableAutoplayPoliey (m_class);` —— 与 `启用自动播放` 的方法体 `1905` **完全相同**(复制粘贴未改) | 即使按名接线,"无头"也只会设成自动播放策略,**永远进不了无头**。包一个同名工具=功能名实不符 |
| **`插入值` 未做 Prepend** | `FBroLib.wsv:1865` 声明注释写 `英语名：PrependWrapper`;但方法体 `1870` 为 `@ FBroHsCommandLine_AppendArgument(m_class,@<值>.GetText());` —— 与 `置额外参数` 的 `1861` 相同 | 该方法是 `置额外参数` 的**重复实现**,PrependWrapper 语义缺失 |

> 附带未致命瑕疵: `是否存在项`(1806, HasSwitches) 方法体 `1808` 为 `if(!IsEmpty()) return ...;`,**IsEmpty 时无返回兜底**——虽然标注了 `@禁止流程检查`,调用方仍会拿到未定义返回值。

---

## B. 交叉核对主表

**"我们是否已有"的判据**: 除工具名精确匹配外,已按题面要求在 `src/*.wsv` 全文(排除 `*~vbak*`)搜索 `方法名 == "..."` 分派、以及中文/英文关键词。搜索为**(936 GBK 与 UTF-8 双路)全文件扫描**,结果见每行"依据"。

**关键词命中总表(排除 `*~vbak*` 后的真实命中数)**:

| 关键词 | 命中 | 命中的唯一位置 |
|---|---|---|
| `命令行` | 9 | `main.wsv:475,477,490`(仅参数声明与监控名)、`MCP_Server.wsv:415`(监控注释)、`MCP_Stdio.wsv:214,217,218,220,224`(**MCP 自身 argv**,非 CEF) |
| `单进程` / `single-process` | **0** / **0** | — |
| `无头` | 3 | `main.wsv:215`(注释)、`MCP_Server.wsv:10275`(注释)、`MCP_Stdio.wsv:20`(注释) —**均为注释/说明,无实现** |
| `headless` | 5 | `MCP_Server.wsv:437,8891`、`MCP_Server_Reverse.wsv:1872,1878`、`MCP_Stdio.wsv:225` —全是 **MCP 自身启动参数/说明**,无 CEF 开关 |
| `摄像头` | 4 | `MCP_BrowserEvents.wsv:2950`、`MCP_Server.wsv:418,10342`、`MCP_Server_Core.wsv:3754` —**均为"感知/告警"**,非启用 |
| `录音` / `speech-input` | **0** / **0** | — |
| `自动播放` / `autoplay` | **0** / **0** | — |
| `media-stream` | **0** | — |
| `GPU`(作为开关) | 2 | `MCP_BrowserEvents.wsv:1021`(注释)、`MCP_Server.wsv:10449`(读进程类型) —**无禁用/清单开关** |
| `禁用代理` / `NoProxy` | **0** / **0** | — |
| `跨框架` / `CrossFrame` | **0** / **0** | — |
| `远程调试` / `remote-debugging` | **0** / **0** | — |
| `AppendSwitch` / `HasSwitch` / `GetGlobalCommandLine` / `取全局命令行` | **0** | — |

**结论性事实**: `类_FBrowser_命令行` 在 `src/` 中**从未被实例化、从未调用任何方法**。它只作为 `main.wsv:477`、`main.wsv:490` 两个虚方法的**形参类型**出现,而这两处方法体(`479–487`、`492–496`)都只在 `是否监控启动流程` 为真时记录一条监控事件,`命令行` 形参**完全未被使用**。

### 主表

| 能力 | 类库方法原文+行号 | 完整签名 | 我们是否已有(依据 文件:行) | 类别 | 建议工具名 | 价值 | 风险 |
|---|---|---|---|---|---|---|---|
| 启用摄像头 | `FBroLib.wsv:1881` `启用摄像头 注释="命令行enable-media-stream,允许浏览使用摄像头"` | `启用摄像头() → 无返回` | **无**。仅有:伪装 `browser_permission_spoof`(`MCP_Server.wsv:10552`,→`MCP_Server_Core.wsv:3509`)与感知 `browser_collect event_permission_enable`(`MCP_Server.wsv:10342`→`MCP_Server_Core.wsv:3754`)。`media-stream` 全文 0 命中 | **乙** | `browser_startup_args`(统一通道,下同) | 高:getUserMedia/视频通话类站点在无此开关时直接不可用;伪装权限≠打开采集能力 | 中:向页面开放真实摄像头;应默认关、显式开、并提示隐私 |
| 启用录音 | `FBroLib.wsv:1895` `启用录音 注释="命令行：enable-speech-input,允许浏览使用话筒"` | `启用录音() → 无返回` | **无**。`speech-input`/`录音` 全文 0 命中 | **乙** | 同上 | 中:语音输入/WebSpeech 场景 | 中:开放麦克风,隐私敏感 |
| 禁用GPU | `FBroLib.wsv:1924` `禁用GPU 注释="...不兼容的显卡只能禁用GPU否者网页可能渲染失败"` | `禁用GPU() → 无返回` | **无**。`GPU` 仅 2 处非开关命中(见上表) | **乙** | 同上 | **高**:服务器/虚拟机/无显卡或驱动不兼容环境下的白屏兜底,类库注释明说"只能禁用GPU" | 低-中:CPU 占用上升,渲染变慢;属可逆的显式降级 |
| 忽略GPU禁用清单 | `FBroLib.wsv:1938` `忽略GPU禁用清单 注释="内核内置不兼容部分显卡，设置后忽略内核这个设置..."` | `忽略GPU禁用清单() → 无返回` | **无** | **乙** | 同上 | 中:老显卡能被真正启用 | 中:类库自述"忽略了也没用,只有禁用GPU",可能无效果或引入不稳定 |
| 禁用GPU缓存 | `FBroLib.wsv:1931` `禁用GPU缓存 注释="禁止GPU创建缓存文件及文件夹"` | `禁用GPU缓存() → 无返回` | **无** | **乙** | 同上 | 低-中:磁盘占满/多实例缓存冲突场景 | 低 |
| 启用录音/摄像头之外的权限 | — | — | `browser_permission_spoof`(`MCP_Server.wsv:10552`) | **丙** | 不新增 | — | — |
| 通用开关写入 | `FBroLib.wsv:1828` `置值 注释="英语名：AppendSwitch 说明：value默认前面要加\"--\""` / `1835` `置项值 ...AppendSwitchWithValue` | `置值(值:文本型) → 无返回` / `置项值(项目名:文本型, 项目值:文本型) → 无返回` | **无**。`AppendSwitch` 0 命中 | **乙**(必须在 `FBrowser_初始化` 前落到生效命令行) | `browser_startup_args`(白名单+落盘,而非裸开关) | **高**:这是唯一能覆盖"将来任何 Chromium 开关"的通用出口,一处实现永久复用 | **高**:裸透传=让 AI 任意破坏内核(已见 `--single-process` 类注释警告);**必须**做白名单+类型校验,不做自由文本 |
| 读取当前生效开关(自省) | `FBroLib.wsv:1784` `取字符串` / `1849` `取额外参数` / `1811` `是否存在某项` / `1819` `取项值` | `取字符串() → 文本型`;`取额外参数() → 文本型`;`是否存在某项(项目名:文本型) → 逻辑型`;`取项值(项目名:文本型) → 文本型` | **无**。现有仅 `browser_get_process_type`(`MCP_Server.wsv:10449`)、`browser_fbro_version`(`10301`)、`browser_meta`(`10302`),均不涉及命令行 | **甲** | `browser_startup_args action=list`(读回已落盘开关 + 尝试读回实际命令行) | 中:排障刚需——"我设了 `--disable-gpu` 到底进没进内核"目前无法自证 | 低:纯只读 |
| 设置全局代理 | `FBroLib.wsv:1945` `设置全局代理 注释="...不支持带账号密码的S5代理..."` | `设置全局代理(代理地址:文本型, 代理账号:文本型="", 代理密码:文本型="") → 无返回` | **已有**:`browser_set_proxy`(`MCP_Server.wsv:10303`)→`MCP_Server_Core.wsv:1392` `否则 (方法名 == "browser_set_proxy")`→`1420` `browser.设置代理(...)`;类库侧 `FBroLib.wsv:1381` `设置代理`(注释 1383 明说"因为设置代理利用的首选项功能") | **丙** | 不新增 | — | — |
| VIP_高级_设置全局代理 | `FBroLib.wsv:1955` `VIP_高级_设置全局代理 ...带账号密码的S5代理，需赞助会员才可使用` | `VIP_高级_设置全局代理(代理地址, 代理账号="", 代理密码="", 关闭S5错误提示=假) → 无返回` | **已有**:`browser_set_s5_proxy`(`MCP_Server.wsv:10429`)→`MCP_Server_VIP.wsv:60` `vip_ctrl.高级_设置代理(...)` | **丙** | 不新增 | — | — |
| 禁用代理 | `FBroLib.wsv:1968` `禁用代理 注释="命令行：--no-proxy-server，禁止使用代理和系统的自动检测代理功能"` | `禁用代理() → 无返回` | **已有(等价)**:`browser_clear_proxy`(`MCP_Server.wsv:10304`)→`MCP_Server_Core.wsv:1453` `browser.清空代理()`;类库 `FBroLib.wsv:1393` `清空代理` | **丙** | 不新增 | — | — |
| 启用无头模式 | `FBroLib.wsv:1909` `启用无头模式 注释="命令行：--headless，无头模式"` | `启用无头模式() → 无返回` ⚠A4:方法体 `1912` 实为 `EnableAutoplayPoliey` | **已有更优替代**:`browser_create background:true`(`MCP_Server.wsv:10275`)→`main.wsv:217–226` `__BG__` 分支 `FBrowser_创建后台浏览器(...)`,类库注释(`main.wsv:215`)明言"**也不是无头模式(其优于无头模式)**" | **丙** | 不新增 | 低:已被更优方案覆盖 | **高**:类库方法本身是坏的(A4),接线即名实不符 |
| 启用跨框架操作模式 | `FBroLib.wsv:1888` `启用跨框架操作模式 注释="跨框架操作，解除框架和框架直接不能直接操作的限制，存在不安全性"` | `启用跨框架操作模式() → 无返回` | **已有等价路径**:`browser_get_frames`(`MCP_Server.wsv:10314`)、`browser_frame_by_name`(`10316`)、`browser_get_focused_frame`(`10317`)、`browser_dom_query`(`10325`),叠加 `browser_cdp_call`(`10476`)可指定任意 frame 求值 | **丙** | 不新增 | 低 | 类库自述"存在不安全性" |
| 设置远程调试端口 | `FBroLib.wsv:1916` `设置远程调试端口 注释="命令行：--remote-debugging-port"` | `设置远程调试端口(端口号:整数) → 无返回`(参数 1917) | **已有并明确弃用外部端口**:`browser_cdp_call`(`MCP_Server.wsv:10476`)/`browser_cdp`(`10349`)走进程内 CDP;`MCP_Server.wsv:8932` 原文 `cdp_note = "CDP 请使用 MCP 工具 browser_cdp_call, 非 /devtools WebSocket 代理"`。另初始化配置已内建 `远程端口`(`FBroDataType.wsv:28`) | **丙** | 不新增 | 低 | 中:开外部调试端口=放开完整 DevTools 面,与现有安全设计冲突 |
| 启用单进程模式 | `FBroLib.wsv:1874` `启用单进程模式 注释="命令行--single-process，只为了方便多进程模拟调试，仅调试模式下有用，单进程模式存在各种问题，不建议发布软件使用"` | `启用单进程模式() → 无返回` | **无**(0 命中) | **乙** | 不建议单列建议;若做通用通道可纳入白名单 | **低**:类库自述"仅调试模式下有用"、"不建议发布软件使用" | **高**:单进程模式导致 CEF 各类崩溃/异常,注释已警告 |
| 修改执行程序名/额外参数 | `FBroLib.wsv:1800` `置程序` / `1857` `置额外参数` / `1865` `插入值` | `置程序(程序名:文本型)` / `置额外参数(参数文本:文本型)` / `插入值(值:文本型)` | **无** | **乙** | 不新增 | 低 | 高:改 `置程序` 需路径可控;`插入值` 还是坏的(A4) |
| 只读元信息 | `FBroLib.wsv:1758,1763,1770,1778,1792` `是否为空/置空/是否有效/是否只读/取程序` | 见 A2 | **无** | **甲** | 不单列 | 低 | 低 |

---

## ① 真缺口汇总

按优先级(价值/风险比):

1. **`browser_startup_args` 启动参数通道(统一出口)** — 类别**乙**。这是**一个**工具覆盖下列全部开关的最小实现,也是本报告唯一强烈建议做的**基础设施**项。依据:全 `src/` 无任何 `AppendSwitch`/`置值`/`置项值` 调用(`0` 命中),且 `main.wsv:475` 的 `即将处理命令行` 虽已覆写却只记录监控事件、`命令行` 形参未用。
2. **`--disable-gpu`(禁用GPU)** — 类别**乙**。价值最高、风险最低的单点开关。依据:`FBroLib.wsv:1924` 注释"不兼容的显卡只能禁用GPU否者网页可能渲染失败";`src/` 内 0 处开关实现。
3. **`enable-media-stream`(启用摄像头)/ `enable-speech-input`(启用录音)** — 类别**乙**。**注意与 `browser_permission_spoof` 的区别**:后者(`MCP_Server.wsv:10552`)是注入 JS 覆写 `navigator.permissions.query()` 与 `enumerateDevices`,只**伪造权限状态**;前者才是让内核真正允许采集。二者不可互替,故为**真缺口**。
4. **`--disable-gpu-cache`(禁用GPU缓存)/ `DisableGpuBlockList`(忽略GPU禁用清单)** — 类别**乙**。同族,建议随第 1 项一并进白名单。
5. **启动开关只读自省(`action=list` 读回已落盘开关 + 尝试读回实际命令行)** — 类别**甲**。依据:`FBroLib.wsv:1784/1849/1811/1819` 均为无副作用查询;当前排障无法自证开关是否进了内核。
6. **`autoplay-policy`(启用自动播放)** — 类别**乙/丙 边界**,需真机裁决。类库给了开关(`FBroLib.wsv:1902`),但项目另有 `browser_set_preference`(`MCP_Server.wsv:10439`→`MCP_Server_VIP.wsv:1289`,实为**按名写 Chromium 请求环境首选项**)可能以首选项达成同一效果。建议先试首选项,失败再走开关。

**不是缺口(明确排除)**: 代理三件套、无头、跨框架、远程调试端口、单进程 — 依据见 ②。

---

## ② 我主动排除的误报及依据

只按工具名匹配会产生大量误报;以下逐条给出**反证依据**:

1. **代理(设置/清空/S5)** → **误报,已有**。
   - `browser_set_proxy`(`MCP_Server.wsv:10303`)在 `MCP_Server_Core.wsv:1392` 有真实分派 `否则 (方法名 == "browser_set_proxy")`,其内 `1420` 调 `browser.设置代理(address, username, password)`,类库侧 `FBroLib.wsv:1381`。
   - `browser_clear_proxy`(`MCP_Server.wsv:10304`)→ `MCP_Server_Core.wsv:1453` `browser.清空代理()`,`FBroLib.wsv:1393`。
   - `browser_set_s5_proxy`(`MCP_Server.wsv:10429`)→ `MCP_Server_VIP.wsv:60`。
   - 关键旁证: `FBroLib.wsv:1383` 注释原文"**因为设置代理利用的首选项功能**"——运行期设置代理本就等同命令行代理的效果,且有持久化(`MCP_Server.wsv:341–344`)+ 新浏览器自动应用(`MCP_Server.wsv:2031–2062`)。
   - **仍需主代理注意**:命令行代理是**进程全局、创建浏览器前生效**;`browser.设置代理` 是**每浏览器、需刷新生效**(`FBroLib.wsv:1381` 注释"刷新后才会生效")。对有"首个浏览器首帧就要走代理"的严格需求,命令行版本仍有边际价值——但投入产出比远低于第 1 项,故不列真缺口。

2. **无头模式** → **误报,已有更优方案**。
   - `browser_create background:true`(`MCP_Server.wsv:10275` 描述)走 `main.wsv:217–226` 的 `__BG__` 分支调 `FBrowser_创建后台浏览器`,项目注释 `main.wsv:214–216` 原文"**与"先创建再隐藏窗口"不同、也不是无头模式(其优于无头模式), 适合纯后台刷新取数, 占用更低**"。
   - 另有 `browser_set_window_style`(`MCP_Server.wsv:10446`→`MCP_Server_System.wsv:71–93`,Win32 `SetWindowLongPtr` 改 GWL_STYLE/EXSTYLE/ID)与 `browser_show_window`(`10323`)。
   - 叠加 **A4 的类库 bug**(`FBroLib.wsv:1912` 把无头写成了自动播放策略),接线该开关**必然名实不符**。三重理由排除。

3. **远程调试端口** → **误报,属有意设计**。
   - 项目自己的连接信息里写着(`MCP_Server.wsv:8932`):`cdp_note = "CDP 请使用 MCP 工具 browser_cdp_call, 非 /devtools WebSocket 代理"`。
   - 即项目**刻意**用进程内 CDP(`browser_cdp_call` `10476`、`browser_cdp` `10349`)替代对外 `/devtools` 端口。开端口等于额外暴露完整 DevTools 攻击面。

4. **跨框架操作** → **误报,已有等价面**。
   - `browser_get_frames`(`10314`)、`browser_frame_by_name`(`10316`)、`browser_get_focused_frame`(`10317`)、`browser_dom_query`(`10325`)、`browser_frame_names`(`10315`)已给出逐 frame 定位;`browser_cdp_call`(`10476`)可在指定 frame 执行。

5. **单进程模式** → **误报,且不建议做**。
   - `FBroLib.wsv:1874` 注释原文即"**只为了方便多进程模拟调试，仅调试模式下有用，单进程模式存在各种问题，不建议发布软件使用**"。作为面向用户的 MCP 工具,**危害 > 价值**;最多作为第 1 项白名单里的一个禁用项。

6. **摄像头/麦克风"感知"** → **误报,但与缺口不同层**。
   - `MCP_Server.wsv:418` + `10342`(`event_permission_enable`)+ `MCP_Server_Core.wsv:3754` 是**监听"页面正在索要权限"**,`MCP_BrowserEvents.wsv:2950` 亦为告警。**感知 ≠ 启用**,故不构成对 ①.3 的覆盖。

7. **`browser_permission_spoof` 覆盖摄像头/麦克风** → **误报,不可互替**。
   - 其描述(`MCP_Server.wsv:10552`)为"注入 `navigator.permissions.query()` 覆盖(返回指定 state)+ `MediaDevices.enumerateDevices` 覆盖"——这是**JS 层伪造**,让脚本"以为"已授权。它不能让内核真正打开采集设备。若站点真调 `getUserMedia`,仍需 `enable-media-stream`。

8. **`browser_reverse_cache_disable` 覆盖缓存类开关** → **部分误报(仅覆盖运行期缓存)**。
   - `MCP_Server.wsv:10602` 描述为 `Network.setCacheDisabled`(`MCP_Server_Reverse.wsv:1829` 分派),属 **CDP 运行期**缓存开关,能覆盖"禁用缓存"的语义;但它**不覆盖** `禁用GPU缓存`(`FBroLib.wsv:1931`)——后者是禁 GPU 共享缓存文件落盘,与网络缓存不同层。故 `禁用GPU缓存` 仍留 ①.4。

9. **`browser_get_process_type` / `browser_get_run_style` 覆盖"读命令行"** → **误报,但相关**。
   - `10449` 只返回进程类型枚举(浏览器/渲染/GPU);`10447` → `MCP_Server_System.wsv:95–110` 只返回窗口样式与 `is_popup`。二者都不暴露命令行文本,故 ①.5 的自省仍为真缺口。

---

## ③ 关于"启动参数通道"的结论

### 结论: **做**。理由如下

1. **现状是"零通道"且已确认**: `类_FBrowser_命令行` 31 个公开方法在 `src/` 中调用数为 **0**;`main.wsv:475` 的 `即将处理命令行` 早已被覆写,但方法体 `479–487` 只在 `是否监控启动流程` 为真时记录一条 `app_startup_cmdline` 监控事件,形参 `命令行` 未被使用。**插槽现成,未接线。**
2. **命中面大**: ① 中 5 条真缺口(摄像头/录音/GPU 三连/通用通道/自省)全部同一个通道 + 同一处改动即可覆盖,摊薄成本极低。
3. **有明确失败先例,可避坑(关键证据)**: `_audit/verify_startup_args.py`(2026/9/13 03:41)是一份针对 **`browser_startup_args`** 工具的完整验收脚本(action=`set/list/clear`,存储文件 `chromium_args.txt`,用 `--user-agent=McpStartupProbe/9.9` 做**可判别、不可覆盖**的观测)。配套日志 `_audit/_startup_args.log`(03:45:15,GBK)原文含:
   ```
   [AI浏览器] 警告: 取全局命令行对象失败, 启动开关未应用
   [AI浏览器] 已应用启动开关 1 个
   ```
   我已确认这两条字符串**不存在于任何现存源文件**(全项目 `.wsv/.py/.md/.txt/.log` 扫描,含 `*~vbak.wsv`),且**不存在于当前二进制**(对 `_int\...\AI-Fbowser-Mcp.exe` 做 UTF-16LE 扫描:`browser_startup_args`=False、`启动开关`=False,而同批次校验的 `browser_create`/`browser_set_proxy`/`browser_execute_js`/`browser_permission_spoof`/`新建浏览器窗口` 均为 True,方法有效)。该 exe 时间戳 **2026/9/13 08:02** 晚于日志 **03:45**。
   → 即: **上一轮实现过、跑过、失败于"取全局命令行对象失败",随后代码被完全回退,当前构建不含该功能。**
   → **可行动结论: 不要走 `FBrowser_命令行_取全局()` 这条路**(有实测失败先例),应走已存在的事件钩子。

### 最小可行做法(推荐)

**入口复用现成的 `mcp_config.json`,不新增文件**——因为配置在 `FBrowser_初始化` **之前**就已加载:

- 配置加载: `main.wsv:39` `MCP命令服务器.加载MCP配置 ()`
- 初始化: `main.wsv:98` `如果真 (FBrowser_初始化 (设置, 初始化事件) == 假)`
- **加载早于初始化 → 配置值在钩子触发时必然可用,不需要改顺序。**
- 落盘/编辑方式沿用阅读器: `MCP_Server.wsv:538` `方法 加载MCP配置`,现有读取范式见 `576–657`(如 `配置解析.取整数("port")`、`配置解析.取文本("vip_code")`)。新增一个 `chromium_args` 字符串数组读取即可,与本文件既有字段同级。

**建议插入点(按推荐度排序):**

| 位置 | 行号 | 说明 |
|---|---|---|
| **首选** | `main.wsv:475` `方法 即将处理命令行 <公开 @虚拟方法 = 可覆盖>`,在方法体 `479` 之前的守卫之后接线 | 权威依据: `FBroEventControl.wsv:290` 原文"**浏览器进程和渲染进程都会执行，即将处理命令行,在此次可以对命令行参数进行操作**"。形参 `命令行`(`main.wsv:477`)即 `类_FBrowser_命令行`,可直接调 `置值`(`FBroLib.wsv:1828`)。**注意门控**:`FBroEventControl.wsv:291` 原文"The \|process_type\| value will be empty for the browser process,此参数只会在子进程中才会有值" → 应据 `进程类型` 判空,只在浏览器进程应用 |
| 备选 | `main.wsv:489` `方法 浏览器_即将启动子进程`(形参 `命令行` 在 `490`,方法体 `492–496` 目前同样只记监控)——仅用于子进程侧补充开关 | `FBroEventControl.wsv:299` 注释"可在此处获取修改执行子程序命令行" |
| **不要用** | 在 `main.wsv:98` 之前调 `FBrowser_命令行_取全局()`(`FBroLib.wsv:1753`) | 见上文失败先例 `_audit/_startup_args.log:6` |

**必须同时注意的两点(否则白做):**

1. **`禁用命令参数` 未被置位——这是好事,是前提**: `FBrowser_初始化配置` 的 `变量 禁用命令参数 <公开 类型 = 逻辑型>`(`FBroDataType.wsv:16`,映射 `command_line_args_disabled`,见 `FBroDataType.wsv:56`)在 `main.wsv:75–95` 的赋值块中**没有出现**,故取默认假 → 命令行参数**启用**,钩子里加的开关才会生效。若将来有人置其为真,本通道会静默失效。
2. **`远程端口` 已有配置位,不必绕开关**: `FBroDataType.wsv:28` `变量 远程端口 <公开 类型 = 整数>`,映射 `tempdata.remote_debugging_port`(`FBroDataType.wsv:68`)。若最终仍需要外部调试端口,直接在 `main.wsv:75–95` 附近设 `设置.远程端口` 比用 `设置远程调试端口` 更贴合既有初始化配置面。

### 实施风险与纪律提醒

- **安全**: 第 1 项**不要**做成自由文本透传。`FBroLib.wsv:1874` 的注释已经示范了后果("单进程模式存在各种问题，不建议发布软件使用")。建议白名单: `--disable-gpu`、`--disable-gpu-cache`、`--ignore-gpu-blocklist`、`--enable-media-stream`、`--enable-speech-input`、`--autoplay-policy=no-user-gesture-required`。
- **不碰两处坏方法**: `启用无头模式`(`FBroLib.wsv:1909`,体 1912 实为自动播放策略)与 `插入值`(`1865`,体 1870 实为 AppendArgument)是**类库缺陷**,不得接线(接线即功能名实不符,且属对用户失实陈述)。
- **响应必须如实要求重启**: 乙类开关对**已运行**的进程无效,工具响应应明确说明需重启应用;这正是上一轮 `verify_startup_args.py:99` 检查的 `"重启" in t`。
- **本报告未做真机验证**: 钩子是否按预期触发、白名单各开关是否真进内核,均需主代理按 `_audit/verify_startup_args.py` 的探针思路(用 `navigator.userAgent` 之类可判别观测)实测。**不得据本报告声称"已验证可用"。**

---

## 附: 本次审计的失败原文记录(按纪律,如实打印)

- 对 `C:\...\资料\类库\FBrowser浏览器\FBroLib.wsv` 搜索 `类 FBrowser命令行` → **`No matches found`**。原因: 类名实际为 `类 类_FBrowser_命令行`(`FBroLib.wsv:1733`),题面给出的名称与类库原文有差异。
- 对 `_audit\_startup_args.log` 用 read 工具读取 → **报错原文**: `Error: cannot read "..._startup_args.log": invalid UTF-8 text`。改用 GBK(CP936)读取成功,1432 字节 / 29 行,原文已引用于 ③。
- 对当前二进制扫描时,`ASCII`/`GBK` 通道检查 `browser_create` 等已知字符串亦为 False,说明这些字符串以 UTF-16LE 存储;故补做 UTF-16LE 校验并确认方法有效(已知串全 True),再据此判定 `browser_startup_args` 确实缺失。
