# 参数层 triage —— 6 个工具的失败归属（只读源码分析）

> 分析方式：**纯静态阅读 + 读取既有审计产物**。本次分析未编译、未调用任何 MCP 工具、未启动/停止进程、未修改任何源码。
> 本文件内所有 `file:line` 均为实际读到的行；引文为逐字摘录。凡属推断（而非引文）均已显式标注 `[推断]`。
> **任何"修复"都只是提议，未经任何验证** —— 验证由主 agent 另行执行。

---

## 0. 结论速览

| 工具 | 台账失败原文 | 判决 | 归属层 |
|---|---|---|---|
| `browser_vip_set_css_version` | `version 必须为正整数 \| 有效范围: 1-65535` | **测试侧假失败（harness artifact）** + 次要产品文案缺陷 | harness（主）/ 常量文案（次） |
| `browser_vip_set_web_version` | 通过 | 通过；与 css 同源同缺陷 | — |
| `browser_vip_set_v8_version` | 通过 | 通过；与 css 同源同缺陷 | — |
| `browser_set_window_style` | `非法窗口属性类型(1) \| 支持: -16(GWL_STYLE) / -20(GWL_EXSTYLE) / -12(GWL_ID)` | **合法拒绝（可行动）** | harness 取值越域，工具行为正确 |
| `browser_cdp_call` | `非法 CDP 方法名: mcp_probe \| 规范格式为 域.方法 ...` | **合法拒绝（可行动）** | harness 取值无意义 |
| `browser_network_body` | `非法 CDP request_id: mcp_probe \| CDP 请求标识为数字串(形如 1000012345.5) ...` | **合法拒绝（可行动，文案最完整）** | harness 取值无意义 |

一句话：**这 4 条失败里没有一条是"schema 声明了实现读不出来的类型"**。三个 VIP 版本工具的 schema 声明（`string`）与读取器（`yyjson取文本`）是**一致**的；css 那条记录是**harness 曾把值写成 JSON 数字 110** 造成的，而且该行台账此后从未重测（陈旧记录）。

---

## 1. `browser_vip_set_css_version` —— 最高价值结论

### 1.1 三个兄弟工具的 schema 声明（逐字，三者完全同构）

`src/MCP_Server.wsv:9713-9715`

```
9713:         添加工具JSON ("browser_vip_set_css_version", "VIP: 设置CSS内核版本", 单参数Schema文本 ("version", "text", "版本号"))
9714:         添加工具JSON ("browser_vip_set_web_version", "VIP: 设置Web内核版本", 单参数Schema文本 ("version", "text", "版本号"))
9715:         添加工具JSON ("browser_vip_set_v8_version", "VIP: 设置V8内核版本", 单参数Schema文本 ("version", "text", "版本号"))
```

`单参数Schema文本` 的 `"text"` → `"string"` 规范化（`src/MCP_Server.wsv:10094-10106`）：

```
10100:         // 标准合规: 历史遗留类型名 "text" 不是 JSON Schema 合法类型, 统一映射为 "string" (Anthropic API 等严格校验会拒绝 type:"text")
10101:         如果 (类型 == "text")
10102:         {
10103:             类型 = "string"
10104:         }
10106:         s = "\"inputSchema\":{\"type\":\"object\",\"properties\":{\"" + ... + "\":{\"type\":\"" + ... + "\",\"description\":\"" + ... + "\"}}"
```

线上 `/tools/list` 快照（`_audit/_tools_list.json`）证实三者**都是 `"type": "string"`**：

```
2932:    "name": "browser_vip_set_css_version"      -> 2937-2938: "version": { "type": "string",  "description": "版本号" }
2948:    "name": "browser_vip_set_web_version"      -> 2953-2954: "version": { "type": "string",  "description": "版本号" }
2964:    "name": "browser_vip_set_v8_version"       -> 2969-2970: "version": { "type": "string",  "description": "版本号" }
```

→ **三者 schema 声明逐字相同**：`version` 都是必填 string。

### 1.2 三个实现的读取与校验（逐字，除变量名/API 名外完全同构）

`src/MCP_Server_VIP.wsv:1155-1183`（CSS）：

```
1155:         否则 (方法名 == "browser_vip_set_css_version")
1157:             变量 cssVerText <类型 = 文本型>
1158:             cssVerText = MCP命令服务器.yyjson取文本 (参数JSON, "version")
1159:             如果 (cssVerText == "" || 文本到整数 (cssVerText) <= 0)
1160:             {
1161:                 返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_版本必须为正整数))
1162:             }
1171:                     变量 cssVer <类型 = 整数>
1172:                     cssVer = 文本到整数 (cssVerText)
1173:                     如果 (cssVer < MCP_常量.内核版本最小 || cssVer > MCP_常量.内核版本最大 || 到文本 (cssVer) != cssVerText)
1174:                     {
1175:                         返回 (MCP_响应构建.命令失败 (命令ID, "内核版本须为116-135范围内的纯数字(官方API支持值)"))
1176:                     }
1177:                     vip_ctrl.内核开关_设置CSS内核 (cssVer)
1178:                     返回 (MCP_响应构建.响应_需要刷新 (命令ID, "CSS内核已设置"))
```

`src/MCP_Server_VIP.wsv:1184-1212`（Web）与 `1213-1241`（V8）同构，仅 1187/1216 的读取变量名、1202/1231 的校验变量名、1206/1235 的类库调用名不同：

```
1187:             webVerText = MCP命令服务器.yyjson取文本 (参数JSON, "version")
1188:             如果 (webVerText == "" || 文本到整数 (webVerText) <= 0)
1190:                 返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_版本必须为正整数))
1202:                     如果 (webVer < MCP_常量.内核版本最小 || webVer > MCP_常量.内核版本最大 || 到文本 (webVer) != webVerText)
1204:                         返回 (MCP_响应构建.命令失败 (命令ID, "内核版本须为116-135范围内的纯数字(官方API支持值)"))
1206:                     vip_ctrl.内核开关_设置Web内核 (webVer)
1216:             v8VerText = MCP命令服务器.yyjson取文本 (参数JSON, "version")
1217:             如果 (v8VerText == "" || 文本到整数 (v8VerText) <= 0)
1231:                     如果 (v8Ver < MCP_常量.内核版本最小 || v8Ver > MCP_常量.内核版本最大 || 到文本 (v8Ver) != v8VerText)
1235:                     vip_ctrl.内核开关_设置V8内核 (v8Ver)
```

**结论：三个工具的"读取器 + 两道校验"在源码层面没有任何差别**（同一常量、同一文案、同一读取函数）。所以三者行为差异**不可能**来自这三个实现本身。

相关常量：

```
src/MCP_Constants.wsv:51:     常量 内核版本最小 <公开 类型 = 整数 值 = 116 注释 = "CSS/Web/V8 内核开关版本下界" ...>
src/MCP_Constants.wsv:52:     常量 内核版本最大 <公开 类型 = 整数 值 = 135 注释 = "CSS/Web/V8 内核开关版本上界" ...>
src/MCP_Constants.wsv:81:     常量 错误_版本必须为正整数 <公开 类型 = 文本型 值 = "version 必须为正整数 | 有效范围: 1-65535" @输出名 = "ErrorVersionMustBePositiveInt">
```

注意 `错误_版本必须为正整数` **只被这三个工具使用**（全仓 grep `版本必须为正整数` 命中：`MCP_Constants.wsv:81`、`MCP_Server_VIP.wsv:1161/1190/1219`）。

### 1.3 真区间是 116–135（厂商类库文档），`110` 本身就在域外

厂商类库 `FBroVip.wsv` 的现代码声明（该文件**不在本工作区**，逐字引用自审计产物 `_audit/_cg2_data.json`，`file`/`line` 字段标明来源）：

```
_audit/_cg2_data.json:20711:      "<类型 = 整数 注释 = \"支持设置值为135到116\">"        (method = 内核开关_设置CSS内核, file = FBroVip.wsv, line = 1329)
_audit/_cg2_data.json:20725:      "<类型 = 整数 注释 = \"支持设置值为135到116\">"        (内核开关_设置Web内核)
_audit/_cg2_data.json:20739:      "<类型 = 整数 注释 = \"支持设置值为135到116\">"        (内核开关_设置V8内核)
```

（`_audit/_cg2_data.json:20707` 同时给出方法注释原文：`"VIP功能需赞助后才可使用，通过对应的内核版本号，结合谷歌功能关闭对应版本添加或删除的功能..."`。）

→ 厂商支持域 = **116–135**，项目的 `内核版本最小/最大` 与之一致。**110 是域外值**。

### 1.4 机制：为什么 `"110"` 被拒，而 `"120"` 通过

两处读取器**容错性不同**，这是本条的机制核心：

`src/MCP_Server.wsv:6470-6479`（`yyjson取文本`，**无节点类型归一化**）：

```
6470:     方法 yyjson取文本 <公开 静态 类型 = 文本型 @输出名 = "YyjsonGetText" @强制输出 = 真>
6474:         如果 (JSON对象.是否为空 () == 假)
6475:         {
6476:             返回 (JSON对象.取文本 (键名))
6477:         }
6478:         返回 ("")
```

`src/MCP_Server.wsv:6481-6512`（`yyjson取整数`，**已加节点类型归一化**）：

```
6487:             // 修复(参数类型容错): 底层 取整数 只认 JSON 数值节点 —— 文本节点("100")与布尔节点
6488:             // 一律返回 0。而 AI 客户端常把整数写成字符串, 于是工具落进错误分支却照样返回 success。
6496:             如果 (节点类型 == YYJSON值类型.文本值)
6497:             {
6499:                 返回 (文本到整数 (删首尾空 (成员对象.到文本 ())))
6500:              }
```

即：**`取整数` 现在对文本节点容错，`取文本` 仍然只认文本节点**。项目自己也记录了这条经验（`_audit/mass_probe.py:167-169`）：

```
167:     # 注意取值必须**符合 schema 类型**: 该参数在 schema 里是 text, 给整数会让工具侧
168:     # "yyjson取整数"类读取拿到空值(本项目已知: yyjson取文本/整数 对非本类型节点返回空),
169:     # 于是仍报"version 必须为正整数" —— 第一次写成整数 110 时就是这么失败的。
```

于是 css 的失败链条是：

1. 送进去的 `version` 是 **JSON 数字 110**（不是字符串）；
2. `yyjson取文本`（1158）对数值节点返回 `""`；
3. 第一道守卫 `cssVerText == ""`（1159）成立 → 返回 `MCP_常量.错误_版本必须为正整数`；
4. 该常量的值（`MCP_Constants.wsv:81`）逐字就是台账里那句 `version 必须为正整数 | 有效范围: 1-65535`。

**反证（关键）**：字符串**不可能**产生这句文案。理由是同一段代码在**字符串**入参下的失败点必落在第二道守卫、给出**另一句**文案（1175/1204/1233）：`"内核版本须为116-135范围内的纯数字(官方API支持值)"`。台账自己提供了这条自然实验（见 1.6）：

| 轮次(时间) | 工具 | 台账文案 | 推出的入参形态 |
|---|---|---|---|
| 58 (02:58) | web_version | `version 必须为正整数 / 有效范围: 1-65535` | 数值节点（或空） |
| **59 (03:07)** | **web_version** | **`内核版本须为116-135范围内的纯数字(官方API支持值)`** | **字符串，且是第一守卫通过、第二守卫拒绝（即数字串但域外，如 "110"）`[推断]`** |
| 62 (03:08) | web_version | `{"id":"1","success":true,...,"Web内核已设置"}` | 字符串 `"120"`，域内 → 通过 |
| 63 (03:08) | v8_version | 同上（V8内核已设置） | 字符串 `"120"`，域内 → 通过 |

`_audit/_tool_ledger.md:233,234`（轮 58）、`:248,249`（轮 59/60）、`:251,252`（轮 62/63）逐字对应上表。**轮 59 证明"纯数字字符串"会走到第二道守卫**；因此 css 的台账文案（第一道守卫）只可能来自非文本节点。

### 1.5 台账里决定性的一行：args 的类型

`_audit/_tool_ledger.json:2208-2220`（css，轮 50）：

```
2208:  "browser_vip_set_css_version": {
2212:   "args": {
2213:    "version": 110          <-- JSON 数字（不带引号）
2214:   },
2215:   "note": "version 必须为正整数 | 有效范围: 1-65535",
2216:   "ts": "09-13 02:43",
2217:   "round": 50,
2218:   "kind": "PARAM",
2219:   "why": "必须为正整数",
2220:   "status": "fail"
```

对照同期通过的兄弟（`_audit/_tool_ledger.json:2245-2268`）：

```
2249:   "args": {
2250:    "version": "120"        <-- JSON 字符串
2261:   "args": {
2262:    "version": "120"        <-- JSON 字符串
```

**css 台账记录的是数字 110，web/v8 记录的是字符串 "120"** —— 被送进 `参数JSON` 的节点类型不同，这就是全部差异。

（附带证据：`_audit/mass_probe.py:170` 现在写的是 `{"version": "110"}`，即字符串。）

### 1.6 为什么 css 这条记录至今还是 fail —— 陈旧记录

* 台账**默认不重测已测过的工具**：`_audit/tool_ledger.py:5`（`已测过的默认不再重测`）、`:187-189`（`retest = "--retest" in sys.argv`；`names = [k for k in tools if retest or k not in d]`）。
* css 只在**轮 48/50（02:42/02:43）**测过两次（`_audit/_tool_ledger.md:223,225`）；轮 62/63（03:08）通过 web/v8 时**没有重测 css**。
* 因此台账里的 css 结论停留在"harness 还把值写成数字"的那一版。

`[推断]` 关于"110 为何是数字"的两种可能来源（**我无法从产物中排他性证实**，两者结论相同）：
(a) 当时 `TOOL_ARG_OVERRIDES` 里就写成了整数 `{"version": 110}`，后改成字符串 —— `_audit/mass_probe.py:169` 的作者注（"第一次写成整数 110 时就是这么失败的"）支持这一种；
(b) 当时线上 `/tools/list` 把 `version` 声明为 `integer`，于是 `_audit/tool_ledger.py:78-85` 的"按 schema 类型强转"把字符串转成了整数。
两条都不影响结论：**被读取的节点是数值节点，而读取器只认文本节点**。
当前证据（`src/MCP_Server.wsv` 与 `_audit/_tools_list.json` 的 mtime 分别是 `3:49` / `4:07`，均晚于轮 50 的 `02:43`）表明**现状声明是 string**，但 02:43 那一刻的 schema 没有快照，故 (b) 不能证实也不能证伪。

### 1.7 判决与最小修复（分层）

**判决：`browser_vip_set_css_version` 的台账失败 = 测试侧假失败（harness artifact），不是"schema 声明了实现读不出来的类型"。**
`version` 的 schema 类型（`string`）与实现读取（`yyjson取文本`）**一致**，不存在类型倒挂。

但要把这条从 fail 变成 pass，**必须同时修两处 harness 错误，只修类型不够**：

| # | 层 | 变更 | 依据 |
|---|---|---|---|
| H1 | **harness（正确层）** | `_audit/mass_probe.py:170`：`"browser_vip_set_css_version": {"version": "110"}` → `{"version": "120"}`（**字符串 + 域内 116–135**） | schema 声明 string（`MCP_Server.wsv:9713`、`_tools_list.json:2937-2938`）；域为 116–135（`_cg2_data.json:20711`、`MCP_Constants.wsv:51-52`）。**只改类型不改值仍会失败**：`"110"` 会命中第二道守卫 1173-1175 → `内核版本须为116-135范围内的纯数字(官方API支持值)` |
| H2 | harness（可选） | 改完 H1 后重测该单项以刷新陈旧记录（`tool_ledger.py:187` 的 `--retest`）。**这会发起一次真实 tools/call，须由主 agent 决定**；副作用按 harness 自己的判断是"无害"（`mass_probe.py:170` 注释 `# CSS 版本指纹, 无害`） | `_tool_ledger.md:223,225` vs `:251,252` |

**产品侧确实存在的缺陷（次要、真实，但与本条失败无因果关系）**：

| # | 层 | 变更 | 依据 |
|---|---|---|---|
| P1 | **产品（文案自相矛盾）** | `MCP_Constants.wsv:81` 的 `"version 必须为正整数 | 有效范围: 1-65535"` 与本工具**实际接受域 116–135** 矛盾：1–115 与 136–65535 全部会被拒。该常量仅这三个工具使用，改成"须为 116–135 的数字字符串"是安全的最小改法 `[未验证]` | 常量值 `MCP_Constants.wsv:81`；真实域 `MCP_Constants.wsv:51-52` + `MCP_Server_VIP.wsv:1173` |
| P2 | **产品（文档缺失）** | 三个 schema 的描述只有 `"版本号"`（`MCP_Server.wsv:9713-9715`），未写 116–135 域；其他工具（如 `browser_kernel_cdp_monitor`，`MCP_Server.wsv:9681`）都会把取值域写进描述。建议补成 `"内核版本号 116-135 (官方API支持值)"` `[未验证]` | 同上 |
| P3 | **产品（健壮性，可选且影响面大）** | `yyjson取文本`（`MCP_Server.wsv:6470-6479`）未做数值节点归一化，而 `yyjson取整数`（`6481-6512`）已做。AI 客户端把 `version` 写成 `120`（数字）是很自然的事，结果会收到自相矛盾的 `version 必须为正整数`。最小面改法是在这三个工具内改用容错读取，而不是全局改 `取文本`（`取文本` 被数百处使用，全局改语义影响面大）`[未验证][影响面未评估]` | `6481-6512` 的修复注释即先例 |

**不要动 schema 的 `text`/`string`、也不要把读取器改成 `取整数`**：声明为 string 是"标准合规"的有意选择（`MCP_Server.wsv:10100`），而若改成 `取整数`，按 schema 正确传 `"120"` 的调用方反而会因"纯数字字符串"被 `to-text` 规范化差异坑到（`到文本 (cssVer) != cssVerText` 这条纯数字校验会失效/出现前后不一致）。**当前 reader 与 schema 是匹配的，错在 harness 的值。**

---

## 2. `browser_set_window_style` —— 合法拒绝

### 2.1 schema（声明 integer）与读取器（取整数）**互相一致**

```
src/MCP_Server.wsv:9702:         添加工具JSON ("browser_set_window_style", "设置窗口风格", 多属性Schema文本 (属性项JSON ("type", "integer", "风格类型") + "," + 属性项JSON ("style", "integer", "风格值"), "\"type\",\"style\""))
_audit/_tools_list.json:2771-2778:   "type": {"type": "integer", "description": "风格类型"}, "style": {"type": "integer", "description": "风格值"}
```

```
src/MCP_Server_System.wsv:77:                 // type(GWL索引)白名单校验, 任意值透传SetWindowLongPtr静默失败无反馈
src/MCP_Server_System.wsv:79:                 窗口类型 = MCP命令服务器.yyjson取整数 (参数JSON, "type")
src/MCP_Server_System.wsv:80:                 如果 (窗口类型 != MCP_常量.窗口样式_GWL_STYLE && 窗口类型 != MCP_常量.窗口样式_GWL_EXSTYLE && 窗口类型 != MCP_常量.窗口样式_GWL_ID)
src/MCP_Server_System.wsv:82:                     返回 (MCP_响应构建.命令失败 (命令ID, "非法窗口属性类型(" + 到文本 (窗口类型) + ") | 支持: " + ... ))
src/MCP_Server_System.wsv:89:                 browser.置窗口属性 (窗口类型, MCP命令服务器.yyjson取整数 (参数JSON, "style"))
```

白名单常量值（`src/MCP_Constants.wsv:53-55`）：`窗口样式_GWL_STYLE = -16`、`窗口样式_GWL_EXSTYLE = -20`、`窗口样式_GWL_ID = -12`。

### 2.2 台账入参

`_audit/_tool_ledger.json:2119-2132`：`"args": {"type": 1, "style": 1}`、`"note": "非法窗口属性类型(1) | 支持: -16(GWL_STYLE) / -20(GWL_EXSTYLE) / -12(GWL_ID)"`。

### 2.3 判决

**合法拒绝（actionable 的 PARAM 失败），不是产品缺陷；schema 与 reader 无分歧。**
- 通用整数取值 `1` **就是**在该工具合法域 `{-16, -20, -12}` 之外；
- harness 本身是**有意**不覆盖的：`_audit/mass_probe.py:165-166` 逐字写着 `# 通用整数取值 1 不在该工具的合法域内(它只认 -16/-20/-12); 这里**不覆盖** —— 改窗口样式是对宿主窗口的真实副作用(可能把 GUI 窗口样式改坏), 宁可让它记 PARAM 失败。`；`_audit/mass_probe.py:160-166` 的注释块也说明这类"测到的是守卫不是实现"的情况才补覆盖；
- 工具在**任何副作用发生之前**就拒绝了（80-83 早于 89 的 `置窗口属性`），即拒绝本身是设计良好的守卫；
- 文案同时给出"被拒的值(1)"、"全部三个合法值及其含义"，**可行动**。

可选改进（均 `[未验证]`，非必需）：
| # | 层 | 变更 |
|---|---|---|
| S1 | 产品文档 | `属性项JSON ("type", "integer", "风格类型")`（`MCP_Server.wsv:9702`）→ 描述里写明 `-16(GWL_STYLE)/-20(GWL_EXSTYLE)/-12(GWL_ID)`，让 schema 自带域信息（现在只有错误文案里有） |
| S2 | harness（风险自负） | 若要让探针真正打到实现，可做**幂等**前置：先 `browser_get_window_style`（`MCP_Server_System.wsv:61-69`，只读）取当前值，再以 `type=-16` + 原值回写（等同 no-op）。**写回窗口样式是真实副作用，且项目已明确因风险拒绝覆盖，是否采用须由主 agent 决断** |

---

## 3. `browser_cdp_call` —— 合法拒绝（文案可行动）

### 3.1 有效值是什么、从哪来、文案是否说清

```
src/MCP_Server_Core.wsv:4441:             变量 cdpMethod <类型 = 文本型>
src/MCP_Server_Core.wsv:4442:             cdpMethod = MCP命令服务器.yyjson取文本 (参数JSON, "method")
src/MCP_Server_Core.wsv:4445:                 // CDP 方法名规范为 "域.方法" (Network.getResponseBody 等), 无点号必为非法 -> 快速失败(否则会持协议锁挂满 30s+ 拖住其它请求)
src/MCP_Server_Core.wsv:4446:                 如果 (寻找文本 (cdpMethod, ".", 0, 假) == -1)
src/MCP_Server_Core.wsv:4448:                     返回 (MCP_响应构建.命令失败 (命令ID, "非法 CDP 方法名: " + cdpMethod + " | 规范格式为 域.方法, 例: Network.getResponseBody / Runtime.evaluate / Page.navigate / Debugger.enable | 无点号的方法名不会得到内核响应, 会长时间挂起并阻塞其它请求, 故直接拒绝"))
src/MCP_Server_Core.wsv:4450:                 // 观察者由 浏览器_创建完毕 事件自动注册, 此处仅检查不注册(避免阻塞)
src/MCP_Server_Core.wsv:4451:                 返回 (MCP命令服务器.执行CDP命令 (命令ID, cdpMethod, 参数JSON))
```

- **有效值**：真实的 CDP 方法名，必须是 `域.方法` 形式（例：`Network.getResponseBody`、`Runtime.evaluate`、`Page.navigate`、`Debugger.enable`）。
- **调用方从哪获得**：工具**不自带方法清单**；来源是 Chrome DevTools Protocol 的域/方法定义（本仓未内置清单，`4446` 只检查"含点号"这一个必要条件）。`[推断]` 该工具不对域做白名单校验，因此"含点号但不存在的方法"会进入 `执行CDP命令` 直到超时。
- **文案是否可行动**：**是**。它同时给出：被拒值（`mcp_probe`）、规范格式、4 个具体示例、以及"为什么拒绝"（无点号会挂起并阻塞其它请求）。台账原文见 `_audit/_tool_ledger.md:243` / `_audit/_tool_ledger.json:2365` 起。
- schema（`MCP_Server.wsv:9732`、`_tools_list.json:3105` 起）声明 `method` = text → 实现用 `取文本`，**一致**。

**判决：合法拒绝（探针值无意义），无可归因的产品缺陷。** 探针若要有意义，需要传真实方法名（如只读的 `Runtime.evaluate` + `params`）；具体取值需真实调用验证，本次未做 `[未验证]`。

---

## 4. `browser_network_body` —— 合法拒绝（文案最完整）

```
src/MCP_Server_Core.wsv:4592:             变量 requestId <类型 = 文本型>
src/MCP_Server_Core.wsv:4593:             requestId = MCP命令服务器.yyjson取文本 (参数JSON, "request_id")
src/MCP_Server_Core.wsv:4594:             如果 (requestId == "")
src/MCP_Server_Core.wsv:4596:                 返回 (MCP_响应构建.命令失败 (命令ID, "request_id " + MCP_常量.错误_缺少参数))
src/MCP_Server_Core.wsv:4598:             // CDP 的 RequestId 为数字串(形如 1000012345.5), 按格式快速失败(非法 id 不会得到内核响应, 会持协议锁挂满 30s+ 拖累其它请求)
src/MCP_Server_Core.wsv:4600:             首字符 = 取文本左边 (requestId, 1)
src/MCP_Server_Core.wsv:4601:             如果 (寻找文本 ("0123456789", 首字符, 0, 假) == -1)
src/MCP_Server_Core.wsv:4603:                 返回 (MCP_响应构建.命令失败 (命令ID, "非法 CDP request_id: " + requestId + " | CDP 请求标识为数字串(形如 1000012345.5) | 如何取得有效值: ① browser_kernel_cdp_monitor action=add methods=Network.* 订阅 ② browser_cdp_event event_name=Network.requestWillBeSent 取其中的 requestId ③ 再调用本工具 | 注意: browser_network list 的日志里没有 CDP request_id, 取不到"))
src/MCP_Server_Core.wsv:4607:             bodyParams.加入文本成员 ("requestId", requestId)
src/MCP_Server_Core.wsv:4608:             返回 (MCP命令服务器.执行CDP命令_带参数 (命令ID, "Network.getResponseBody", bodyParams.到可读文本 (YYJSON格式化选项.压缩)))
```

- **有效值**：`requestId`，是**以数字字符开头**的字符串（形如 `1000012345.5`）；`4601` 只检查首字符是 `0-9`。
- **从哪获得**：文案**已经逐字给出三步获取路径**（① `browser_kernel_cdp_monitor action=add methods=Network.*` 订阅 ② `browser_cdp_event event_name=Network.requestWillBeSent` 取其中 `requestId` ③ 再调用本工具），并额外给了反例警告"`browser_network list` 的日志里没有 CDP request_id, 取不到"。该引导是**真实存在**的工具与参数：`browser_kernel_cdp_monitor` 注册见 `src/MCP_Server.wsv:9681`（`action=add {methods,max}`、`methods` 例 `Network.*`），实现见 `src/MCP_Kernel.wsv:92-96`。
- **文案是否可行动**：**是**，而且是六个工具里最完整的（值 + 格式 + 三步获得法 + 一条否定性提示）。

**判决：合法拒绝（探针值无意义），无可归因的产品缺陷。**
附带观察（**与本条失败无因果**，仅记录）：`request_id` 的 schema 是 text、读取用 `取文本`（`4593`，非归一化，见 `MCP_Server.wsv:6470-6479`）；由于 CDP requestId 天然是"数字串"，AI 客户端若把它当数字（JSON number）发来，会被读成 `""` 并报 `request_id 参数不能为空`（`4596`）。这与 1.7 的 P3 是同一类问题，`[未验证]`，且按 schema 正确传字符串的调用方不受影响。

---

## 5. 变更清单（提议，全部未验证）

| ID | 层 | 文件:行 | 现状 → 提议 | 依据 | 必要性 |
|---|---|---|---|---|---|
| **H1** | harness | `_audit/mass_probe.py:170` | `{"version": "110"}` → `{"version": "120"}` | schema=string；域 116–135（`MCP_Constants.wsv:51-52`）；`"110"` 会命中第二守卫 `MCP_Server_VIP.wsv:1173-1175` | **必需**（否则 css 永远 fail，只是换一句文案） |
| H2 | harness | 重测单项（`tool_ledger.py:187` `--retest`） | 刷新陈旧行 | `_tool_ledger.md:223,225` 早于 `:251,252` 的 harness 修复 | 建议（会发起真实调用，需主 agent 决定） |
| **H3** | harness | `_audit/mass_probe.py:298` | `args, notes = build_args(schema, desc)` → 传入 `name` | 函数签名 `:203` 有 `tool_name=None`，`:220` 用它取覆盖；**当前 mass_probe 从不传 → 整张 `TOOL_ARG_OVERRIDES` 表（`147-187`）在该脚本中全部失效**。证据：`_audit/_probe_result.json:2464-2468` 记录 css 实收 `"version": "mcp_probe"`（覆盖值未生效） | 建议（影响面广：`_probe_result.json` 里所有被覆盖的工具都在测守卫而非实现） |
| H4 | harness | `_audit/cold_matrix.py:130` `PARAM_RE` | 增加 `须为|范围内的纯数字` 之类分支 | 第二守卫文案不含 `非法/无效的/必须为正整数`，现被归为 `OTHER`（`_tool_ledger.md:248,249` 即 `ERR_GOOD / OTHER`），重测后会像"未分类缺陷" | 可选（改 H1 后更明显） |
| **P1** | 产品（文案） | `src/MCP_Constants.wsv:81` | `"version 必须为正整数 \| 有效范围: 1-65535"` → 与真实域 116–135 一致 | 该常量只被这三个工具用；真实域见 `51-52` + `MCP_Server_VIP.wsv:1173` | 建议（真实缺陷，但低危） |
| P2 | 产品（文档） | `src/MCP_Server.wsv:9713-9715` | 描述 `"版本号"` → 写明 `116-135` | 域未进 schema，其他工具会写（如 `:9681`） | 建议 |
| P3 | 产品（健壮性） | `src/MCP_Server.wsv:6470-6479` / 三个 VIP 分支 | 让 `version` 的读取对数值节点容错（**最小面：只在这三个工具内**，勿全局改 `取文本`） | `取整数` 已有同类先例 `6481-6512` | 可选，影响面未评估 |
| S1 | 产品（文档） | `src/MCP_Server.wsv:9702` | `"风格类型"` → 写明 `-16/-20/-12` | 域现仅存在于错误文案 `MCP_Server_System.wsv:82` | 可选 |
| S2 | harness | — | 幂等前置（读回当前 style 再回写） | 项目已明确因风险拒绝（`mass_probe.py:165-166`） | **不建议**，除非主 agent 明确接受窗口样式风险 |

**不应做的改动**：不要把 `version` 的 schema 从 `string` 改成 `integer`（`MCP_Server.wsv:10100` 是有意的标准合规映射），也不要把读取器换成 `取整数`（会与 `到文本 (ver) != verText` 纯数字校验（`MCP_Server_VIP.wsv:1173`）的语义打架）。**读取器与 schema 是匹配的；错的是 harness 送的值。**

---

## 6. 未能证实 / 明确缺口

1. **无法证实轮 50（02:43）线上 `/tools/list` 对 `version` 声明的是 `string` 还是 `integer`**：`_audit/_tools_list.json`（4:07）与 `src/MCP_Server.wsv`（3:49 修改）都晚于该轮；那一版的 schema 无快照。故 1.6 的 (a)/(b) 两来源不能排他（结论不受影响：送进去的是数值节点）。
2. **无法证实轮 59 时 web_version 收到的具体字符串**（表 1.4 中标 `[推断]`）：只能证明它是"纯数字且域外"的字符串。
3. **厂商类库文件 `FBroVip.wsv` 不在本工作区**（`glob **/FBroVip.wsv` 无结果）；116–135 的依据是审计产物 `_audit/_cg2_data.json:20711/20725/20739` 记录的类库声明，而非原件。
4. **本报告未做任何真机验证**：没有调用任何工具、没有重跑 harness、没有编译。H1–H4/P1–P3/S1–S2 全部是提议。
5. 本次未审计其他工具的同类"`取文本` 遇数值节点"风险（仅在第 1.7 P3 与第 4 节各记录一例）。
