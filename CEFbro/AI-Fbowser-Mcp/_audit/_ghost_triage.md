# 幽灵注册分诊表 (只读静态审计)

> 审计对象: `C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\*.wsv`
> 审计方式: 只读静态分析, **未修改任何 .wsv, 未编译, 未调用 MCP 接口**
> 本报告是**分诊表 + 证据**, 不是"已验证/已修复"的结论。

---

## 0. 快照与可复现性声明

审计期间**发现另一进程正在并发改写 src/**（`MCP_Server.wsv` 在我开始读取的 1 分钟内由 609255 → 615334 → 615588 字节; `MCP_Server_Core.wsv` 的 mtime 距我读取仅 8 秒）。因此先把源码冻结成只读快照, 全部结论基于该快照:

- 快照目录: `_audit\_ghost_snapshot\*.wsv.snapshot.txt`（后缀刻意不是 `.wsv`, 防止被 IDE/编译器误当源码）
- 快照清单: `_audit\_ghost_snapshot\_manifest.json`（每个文件的 md5 / 字节数 / mtime）
- 快照时刻: `2026-09-13 02:14:58`; 复核时刻 `02:17:30` 全量哈希一致 → **快照即当前源码**
- 待审计文件最后改动时间区间: `2026-09-13 01:29:06 ~ 02:14:39`

分析脚本（均只读 src、只写 `_audit/`）:

| 脚本 | 作用 |
|---|---|
| `_audit/g0_snapshot.py` | 冻结快照 + 生成 md5 清单 |
| `_audit/g1_ghost_triage.py` | 首轮注册表/分派链提取（产出 `g1_registry.json`） |
| `_audit/g2_ghost_audit.py` | 快照版判定引擎（产出 `g2_ghost_findings.json` / `g2_ghost_evidence.txt`） |
| `_audit/g3_sweep.py` | 全量幽灵扫描 + 复用路径实现状态（产出 `g3_sweep.txt` / `g3_sweep.json`） |

---

## 1. 判定方法（先讲清"注册表"到底有几个面, 这是本次结论与原始名单分歧的根源）

本项目同名概念有**三个彼此独立的面**, 必须分开看:

| 面 | 载体 | 入口 | 规模 | 谁能看到 |
|---|---|---|---|---|
| **A. MCP 工具表** | `工具列表构建缓冲区` | 方法 `添加工具JSON` → `填充工具列表` → `完成构建工具列表` | **301 个工具名** | **唯一的 tools/list 来源**; AI 客户端只能看见这 301 个 |
| **B. 命令注册表(字典)** | `命令注册表 <类_FBrowser_字典值>` | `构建命令注册表` / `注册命令双变体` | **618 个键** | 仅供 `查找命令ID` 做"短名→browser_名"映射, **不是** tools/list |
| **C. 分派链** | 7 个分派器方法 | `执行浏览器命令`(MCP_Server.wsv 快照 L10306) | `方法名 == "..."` 条件字面量 491+42+98+11+9+141+17 | 真正决定"能不能执行" |

分派链结构（快照 `MCP_Server.wsv` L10334~L10437）:

```
前缀直投:  browser_fill_*      → 分类分派_填表操作
          browser_vip_*/browser_fingerprint_*/browser_font_* → 分类分派_VIP操作
          workflow*           → 分类分派_编排操作
          browser_reverse_*   → 分类分派_逆向操作
          browser_kernel_*    → 分类分派_内核操作
          显式名单(browser_create_tab / browser_task_runner_post / ping / ...) → 分类分派_系统操作
          否则                → 分类分派_核心操作
回退链: 若 result == "" 依次再试 核心 → 填表 → VIP → 系统 → 编排 → 内核
兜底: 全部返回 "" ⇒ 返回 命令失败("未知命令: xxx")  ⇒  JSON-RPC 层转成 -32601 "工具不存在: xxx"
           (MCP_Server.wsv 快照 L10437 与 L10086)
```

7 个分派器的尾部均为 `返回 ("")`（核心 L6965 / 逆向 L1709 / VIP L1543 / 系统 L148），**没有任何兜底 `否则` 分支会吞掉未知名字**；全库仅 6 处 `是否以(方法名,...)`（其中 L10338 一行含 2 个），全部位于 `执行浏览器命令` 的**路由**段（是路由不是处理），分派器内部**零**通配/包含判断。⇒ 本次审计中 **"被兜底覆盖" 类判定为 0 例**。

入口归一化（决定了名字等价性）:
- `执行浏览器命令` 做一次 `browser.` → `browser_` 替换 → 所以 `browser.reverse_trace` 与 `browser_reverse_trace` 等价;
- 以 `browser_` 开头的名字**不走**短名映射（`取短名映射` L10486-10489 直接 `返回("")`）;
- `处理_工具调用`(L10020) 把 `params.name` **原样**传给 `执行浏览器命令`, 不校验是否在 tools/list 内 → 严格客户端拒调, 宽松客户端会打到分派链上。

---

## 2. 对任务前提的三处修正（都有证据）

1. **16 个名字没有一个在 tools/list 里**。逐个 grep `添加工具JSON ("<名>"` 结果全为 0。也就是说 AI 客户端在 tools/list 里本来就看不到它们 —— 现象**不是**"调用成功但无实现", 而是"看不见 / 硬调则报错"。
2. **真实运行结果是 `-32601 工具不存在`**（或顶层直接方法路径下的 `未知命令: xxx | 用 mcp_help 查看可用命令`）。因为 11 个真幽灵在 7 个分派器里全部落空 → `执行浏览器命令` 返回"未知命令" → 被 `处理_工具调用` L10084-10086 映射成 `-32601`。**不存在"成功但无实现"的路径**。
3. **16 个里只有 11 个是真幽灵, 5 个其实有实现分支**（`browser_aliases` / `browser_batch` / `browser_create_tab` / `browser_debugger_pause` / `browser_task_runner_post`）。

**原始 16 人名单的来源与误报机理（已定位到行）**: 名单取自 `_audit/_cleanup_report.md` 末尾的 `## 幽灵注册` 段, 该段由 `_audit/cleanup_scan.py` 生成, 其判定只有这一行:

```python
# cleanup_scan.py L95-L102
reg  = {全部 注册命令双变体/"browser_xxx" 置整数值}      # = B 面
tools = {re.findall(r'添加工具JSON \("([a-z0-9_]+)"', all_text)}   # = A 面
ghost = sorted(reg - tools)      # ← 从头到尾没有查过 C 面(分派链)
```

即 `幽灵 = 在命令注册表 且 不在 tools/list` —— **完全没检查分派链**。这正是任务描述里点名要避免的那个错误。5 个误报项之所以被卷进来, 是因为它们的字典键是 `browser_aliases`/`browser_batch`(camel 变体), 而 tools/list 里注册的名字是**不带前缀的** `aliases`/`batch`。

另注: 同一批 5 个名字在 `_audit/_reg_gap.json` 里被归类为 `"unreg"`(未注册), 与 `_cleanup_report.md` 的 `"幽灵注册"` 互相矛盾 —— 项目内对同一事实存在**三套不一致的历史分类**, 建议以本报告的三面模型统一。

---

## 3. 分诊表（16 行, 逐项）

**列说明**: ①=是否在 tools/list(添加工具JSON) 注册; ②=是否在命令注册表(字典)注册; ③=7 个分派器逐个 grep 结果（核心/填表/VIP/系统/编排/逆向/内核）。行号均为快照行号。

| # | 工具名 | ① tools/list | ② 命令注册表 | ③ 分派链（7/7） | 判定 |
|---|---|---|---|---|---|
| 1 | `browser_aliases` | ✗（注册的是 **`aliases`** `MCP_Server.wsv:9573`） | ✓ `MCP_Server.wsv:1087` id=1005 | **核心 L4279 命中** `否则 (方法名 == "aliases" \|\| 方法名 == "browser_aliases")`；其余 6 个无 | **其实有实现（非幽灵）** |
| 2 | `browser_batch` | ✗（注册的是 **`batch`** `MCP_Server.wsv:9537`） | ✓ `:1088` id=1004 | **核心 L5289 命中** `否则 (方法名 == "batch" \|\| 方法名 == "browser_batch")`；其余 6 个无 | **其实有实现（非幽灵）** |
| 3 | `browser_create_tab` | ✗ | ✓ `:1144` id=1141 | **系统 L16 命中** `如果 (方法名 == "browser_create_tab")`；其余 6 个无 | **其实有实现（非幽灵）—— 分支为"有意禁用"的显式拒绝** |
| 4 | `browser_debugger_pause` | ✗ | ✓ `:1040` id=832 | **核心 L4466 命中** `否则 (方法名 == "browser_debugger_pause")`；其余 6 个无 | **其实有实现（非幽灵）—— 分支为"有意禁用"的显式拒绝** |
| 5 | `browser_fingerprint_languages` | ✗ | ✓ `:1285` `注册命令双变体("fingerprint_languages",1348,假)` id=1348 | **全部分派方法均无（7/7 均无）** | **幽灵（需补实现）** |
| 6 | `browser_fingerprint_webgl_vendor` | ✗ | ✓ `:1275` `注册命令双变体("fingerprint_webgl_vendor",1340,假)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 7 | `browser_font_randomize` | ✗ | ✓ `:1259` `注册命令双变体("font_randomize",1327)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 8 | `browser_reverse_cookie_cdp` | ✗ | ✓ `:1276` `注册命令双变体("reverse_cookie_cdp",1341)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 9 | `browser_reverse_css_coverage` | ✗ | ✓ `:1286` `注册命令双变体("reverse_css_coverage",1349)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 10 | `browser_reverse_detect_traps` | ✗ | ✓ `:1249` `命令注册表.置整数值("browser_reverse_detect_traps",1321)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）**（意图若为"应用反检测预设"则改判见 §5.11） |
| 11 | `browser_reverse_emulate_focus` | ✗ | ✓ `:1279` `注册命令双变体("reverse_emulate_focus",1344)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 12 | `browser_reverse_input_cdp` | ✗ | ✓ `:1281` `注册命令双变体("reverse_input_cdp",1345)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 13 | `browser_reverse_layer_tree` | ✗ | ✓ `:1287` `注册命令双变体("reverse_layer_tree",1350)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 14 | `browser_reverse_network_conditions` | ✗ | ✓ `:1277` `注册命令双变体("reverse_network_conditions",1342)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 15 | `browser_reverse_trace` | ✗ | ✓ `:1282` `注册命令双变体("reverse_trace",1346)` | **全部分派方法均无（7/7）** | **幽灵（需补实现）** |
| 16 | `browser_task_runner_post` | ✗ | ✓ `:1163` id=1142 | **系统 L20 命中** `否则 (方法名 == "browser_task_runner_post")`；其余 6 个无 | **其实有实现（非幽灵）—— 分支为"有意禁用"的显式拒绝** |

### 统计

| 分类 | 数量 | 名单 |
|---|---|---|
| **确认幽灵（需补实现）** | **11** | `browser_fingerprint_languages` `browser_fingerprint_webgl_vendor` `browser_font_randomize` `browser_reverse_cookie_cdp` `browser_reverse_css_coverage` `browser_reverse_detect_traps` `browser_reverse_emulate_focus` `browser_reverse_input_cdp` `browser_reverse_layer_tree` `browser_reverse_network_conditions` `browser_reverse_trace` |
| **误报 / 其实有实现（非幽灵）** | **5** | `browser_aliases` `browser_batch` `browser_create_tab` `browser_debugger_pause` `browser_task_runner_post` |
| **被兜底覆盖** | **0** | 7 个分派器均无兜底 `否则` 分支; 全库无 `是否以/包含` 型通配处理分支 |
| **建议删注册项** | **0**（但见 §5 的"可选收敛"） | — |
| 合计 | 16 | — |

---

## 4. 判定为"其实有实现（非幽灵）"的 5 项证据原文

| 工具名 | 分派分支原文 | 行为 |
|---|---|---|
| `browser_aliases` | `MCP_Server_Core.wsv:4279` `否则 (方法名 == "aliases" \|\| 方法名 == "browser_aliases")` | 返回快捷别名清单 JSON（L4291 `构建简单JSON ("aliases", 别名列表)`），**功能完整** |
| `browser_batch` | `MCP_Server_Core.wsv:5289` `否则 (方法名 == "batch" \|\| 方法名 == "browser_batch")` | 转 `处理_批量操作`（`MCP_Server.wsv` 快照 L1373），**功能完整** |
| `browser_create_tab` | `MCP_Server_System.wsv:16-19` | 明确拒绝：`"⛔ 远程创建标签页已禁用 \| 原因: GUI窗口自动管理浏览器实例… \| 替代方案: browser_navigate / browser_create"` |
| `browser_debugger_pause` | `MCP_Server_Core.wsv:4466-4472` | 明确拒绝：`"Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) \| 请用 debugger_flow…"` |
| `browser_task_runner_post` | `MCP_Server_System.wsv:20-23` | 明确拒绝：`"⛔ 远程 task_runner 创建浏览器已禁用…"` |

这 5 项的**共同性质**：不是"漏了实现", 而是 (a) camel 变体别名（第 1、2 项）, 或 (b) 已被产品决策下线的能力, 但**保留了拒绝分支 + 替代方案提示**（第 3、4、5 项）。

**独立佐证**：`备份\仓库精简-20260829\skills\AI浏览器MCP.md` 的 v3.0.0 变更记录原文 ——
> 「移除 `browser_create_tab`/`browser_task_runner_post`」
> 「v2.8.1: 补全路由, batch/aliases/workflow_*/短名(如 get_url) 作为顶层方法调用不再落入 -32601」

⇒ 这 5 项**不应被判为需要补实现**；判"删注册项"也不对（第 3-5 项的字典键是给顶层直接方法路径兜兼容用的, 删掉只会让老调用者收到 `-32601 未知方法` 而不是可读的替代方案提示）。

---

## 5. 11 个确认幽灵：现有可复用实现路径（不重复造轮子）

### 5.0 三个**通用复用底座**（先说这个, 因为多数幽灵只需 4 行）

| 底座 | 位置 | 作用 |
|---|---|---|
| `执行V8CDP命令 (命令ID, CDP方法名, 参数JSON文本, 成功提示)` | `MCP_Server_Reverse.wsv:1714`（分派器内的本地辅助方法） | **逆向分派器内部一行封装的模板**。现存 20+ 个 `browser_reverse_*` 工具都是它的 3~6 行调用（见 L1087 / L1097 / L1121 / L1629 / L1642 / L1656） |
| `执行逆向CDP命令 (命令ID, cdpMethod, paramsJSON)` | `MCP_Server.wsv:7768` | 公开静态统一入口：取安全浏览器 → 注册观察者 → 执行 CDP |
| `执行CDP并同步等待 (命令ID, CDP方法, 参数JSON, 超时ms)` | `MCP_Server.wsv:2977` | 需要**同步拿回结果**时用（`browser_reverse_precise_coverage` L1113 即用法示例） |
| **逃生舱（今天就能用）** | `browser_cdp_call {method, params}` = `MCP_Server_Core.wsv:4294`, tools/list 登记于 `MCP_Server.wsv:9606` | 8 个 CDP 域幽灵（第 6、8~15 项）**今天已经可以**用 `browser_cdp_call` 打到同一个 CDP 方法; 另有 `browser_vip_send_devtools_msg`(`MCP_Server_VIP.wsv:1068`) 可发原始 DevTools 消息 |
| **VIP 指纹底座** | `类_FBrowserVIP_控制器` 的 `指纹_虚拟*` 系列（全库 106 处调用） | 指纹类 3 个幽灵所需的内核 API **都已存在且已被调用** |

### 5.1 `browser_fingerprint_languages` — 需补实现, **一行封装, 内核 API 已存在**
- 意图证据: `MCP_Server.wsv:1284` 注释 `// v2.8 R9: navigator.languages / CSS.startRuleUsageTracking / LayerTree`
- 复用路径（**最强, 因为同一个 VIP API 已在项目里被调用**）: `MCP_Server_Core.wsv:2187-2191`
  ```
  val = MCP命令服务器.yyjson取文本 (配置解析, "languages")
  如果 (val != "") { vip_ctrl.指纹_虚拟Languages (val) }
  ```
  即 `browser_fingerprint` 的 `action=set_batch` + `config.languages` **已经能设 navigator.languages**。
- 分支骨架直接抄同族单值工具 `browser_fingerprint_appname`（`MCP_Server_VIP.wsv:352-368`，参数 `value`），把 `指纹_虚拟AppName` 换成 `指纹_虚拟Languages` 即可。
- 路由已就绪: `执行浏览器命令` L10338 已把 `browser_fingerprint_*` 投给 VIP 分派。

### 5.2 `browser_fingerprint_webgl_vendor` — 需补实现, **一行封装, 内核 API 已存在**
- 意图证据: `MCP_Server.wsv:1274` 注释 `// v2.8 R7: … / WebGL vendor`
- 复用路径: `MCP_Server_Core.wsv:2193-2197`（`config.webgl_vendor` → `vip_ctrl.指纹_虚拟Webglvendor (val)`）
- **注意别误认为已被覆盖**: `browser_vip_fingerprint_webgl`(VIP L763) 与 `browser_vip_fingerprint_webgl_fixed`(VIP L513) 都是**噪点**维度, 均不设置 vendor 字符串 → 该能力在工具层确实缺失。
- 骨架抄 `browser_vip_fingerprint_webgl_fixed`（`MCP_Server_VIP.wsv:513-528`）。

### 5.3 `browser_font_randomize` — 需补实现, **有部分复用**
- 意图证据（**唯一有 schema 与描述的一条**）: `备份\仓库精简-20260829\skills\AI浏览器MCP.md:651`
  > `| browser_font_randomize | action(random/reset),count,seed | **v2.8** 字体枚举随机化(VIP+JS双通道) |`
- 复用路径:
  - VIP 通道 → `browser_vip_fingerprint_font`（`MCP_Server_VIP.wsv:787-794`，调用 `指纹_虚拟CSS字体指纹 (font_list, w_offset, h_offset)`）— 随机化只需把 `font_list`/`w_offset`/`h_offset` 随机生成后复用这条调用；
  - Canvas 字体通道 → `browser_vip_fingerprint_canvas_font`（`MCP_Server_VIP.wsv:798-807`，`指纹_虚拟Canvas字体指纹 (value)`）；
  - JS 通道 → 抄 `browser_canvas_noise`（`MCP_Server_Core.wsv:2994`，纯 JS 注入无需 VIP）的注入骨架；或 `browser_permission_spoof`（`MCP_Server_Core.wsv:3130`）。
- 路由已就绪: `执行浏览器命令` L10338 已把 `browser_font_*` 投给 VIP 分派（**该前缀路由就是为它预留的, 但分派器里没有对应分支**）。
- 判定为 需补实现（不是删注册项）: `browser_vip_fingerprint_font` 是**定值**设字体清单, 无随机化/无 reset, 不等于随机化枚举。

### 5.4 `browser_reverse_cookie_cdp` — 需补实现（CDP 一行封装）
- 意图证据: `MCP_Server.wsv:1274` 注释 `// v2.8 R7: Storage.getCookies / …`
- 复用路径: `执行V8CDP命令 (命令ID, "Storage.getCookies", "{}", "…")`（模板见 `MCP_Server_Reverse.wsv:1656` 的 `browser_reverse_cache_disable`）
- 近邻（避免重复语义）: `browser_reverse_cookie_sources`（`MCP_Server_Core.wsv:5811`）、`browser_get_all_cookies`（`MCP_Server_VIP.wsv:1101`）— 这两者是**其它通道**取向（Cookie来源分析 / 非URL限定全量），与 `Storage.getCookies` 的 CDP 通道**部分重叠但不等价**；若要收敛, 可考虑只留 `browser_get_all_cookies`。

### 5.5 `browser_reverse_network_conditions` — 需补实现（CDP 一行封装, 有同域现成模板）
- 意图证据: `MCP_Server.wsv:1274` `// … Network.emulateNetworkConditions …`
- 复用路径: **直接抄同域兄弟** `browser_reverse_cache_disable`（`MCP_Server_Reverse.wsv:1646-1659`）
  ```
  cdDisable = yyjson取逻辑_默认 (参数JSON, "disable", 真)
  cdParams  = "{\"cacheDisabled\":" + 选择 (cdDisable,"true","false") + "}"
  返回 (执行V8CDP命令 (命令ID, "Network.setCacheDisabled", cdParams, "…"))
  ```
  把方法名换成 `Network.emulateNetworkConditions`、参数换成 `offline/latency/downloadThroughput/uploadThroughput` 即可。

### 5.6 `browser_reverse_emulate_focus` — 需补实现（CDP 一行封装, 有布尔开关模板）
- 意图证据: `MCP_Server.wsv:1274` `// … Emulation.setFocusEmulation …`
- 复用路径: `browser_reverse_bypass_csp`（`MCP_Server_Reverse.wsv:1631-1645`）或 `browser_reverse_skip_pauses`（L1089-1098）——**同构布尔开关**, 换 CDP 方法为 `Emulation.setFocusEmulationEnabled`。
- 另有可参考的 Emulation 域现成用法: `MCP_Server.wsv:3225` `执行CDP并同步等待 ("_tch_emu", "Emulation.setTouchEmulationEnabled", …)`（含"零前置自动开启"的处理思路）。

### 5.7 `browser_reverse_input_cdp` — 需补实现（参数构造已有一半现成代码）
- 意图证据: `MCP_Server.wsv:1280` `// v2.8 R8: Input.dispatchMouseEvent/KeyEvent / …`
- 复用路径（**鼠标部分已完整存在**）: `MCP命令服务器.CDP派发鼠标事件`（`MCP_Server.wsv:3126-3177`，公开静态, 已构造 `type/x/y/button/clickCount/deltaX/deltaY/buttons` 并走 `Input.dispatchMouseEvent`）; 触摸可复用 `CDP派发触摸点一次`(`:3182`) / `CDP派发触摸事件`(`:3206`)。
- 键盘部分: `browser_key_event`（`MCP_Server_Core.wsv:725`）与 VIP 侧 `browser_vip_key_type`(`MCP_Server_VIP.wsv:957`)、`browser_vip_key_input`(`:929`) 覆盖 `Input.insertText` 取向。
- 因此 `browser_reverse_input_cdp` 大概率**只是把已有 CDP 输入原语再包一层**；需先确认它与 `browser_mouse_click`/`browser_key_event` 的差异点（若不打算引入新差异, 则应改判为"建议删注册项"）。

### 5.8 `browser_reverse_trace` — 需补实现（CDP 一行, 有 start/take/stop 模板）
- 意图证据: `MCP_Server.wsv:1280` `// v2.8 R8: … Tracing.start/end …`
- 复用路径: 抄 `browser_reverse_precise_coverage`（`MCP_Server_Reverse.wsv:1099-1132`）——**现成的 `action=start/take/stop` 三段式骨架**, 里面还演示了"先 `执行CDP并同步等待` 开域、再 `执行V8CDP命令` 落命令"的正确顺序。替换为 `Tracing.start`(需 `categories`/`transferMode`) / `Tracing.end`（结果经 `Tracing.dataCollected` 事件取回, 可参考 `取CDP事件数据JSON`）。
- 功能近亲（**注意不重合**）: `browser_kernel_reverse_trace`（`MCP_Kernel.wsv:124` 分支 + `MCP_Kernel.wsv:1310` `分派_调用追踪`，向页面注入包装函数, 数据集 `window.__MCP_TRACE__`）——它是 **JS 包装**通道, `Tracing` 是 **Chrome trace 事件**通道, 二者不等价, 不能据此判"已被覆盖"。

### 5.9 `browser_reverse_css_coverage` — 需补实现（CDP 一行, 有同构模板）
- 意图证据: `MCP_Server.wsv:1284` `// v2.8 R9: … CSS.startRuleUsageTracking …`
- 复用路径: 同为 `browser_reverse_precise_coverage`（`MCP_Server_Reverse.wsv:1099-1132`）的 start/take/stop 骨架 → `CSS.startRuleUsageTracking` / `CSS.stopRuleUsageTracking` / `CSS.takeCoverageDelta`。
- 功能近亲: `browser_reverse_precise_coverage`（JS 覆盖率, `Profiler.*`）—— 域不同（CSS 规则 vs JS 函数）, 不构成覆盖。

### 5.10 `browser_reverse_layer_tree` — 需补实现（CDP 一行, 无直接同域模板）
- 意图证据: `MCP_Server.wsv:1284` `// v2.8 R9: … / LayerTree`
- 复用路径: 抄 `browser_reverse_heap`（`MCP_Server_Reverse.wsv:353`）或 `browser_reverse_runtime`（`:389`）的"域启用/取数据"结构 → `LayerTree.enable` + `LayerTree.compositingReasons`。
- 无现成可复用的 LayerTree 代码, 但**不需要新写底层**（`执行V8CDP命令` 已足够）。

### 5.11 `browser_reverse_detect_traps` — 需补实现（唯一需要新写检测逻辑的一条）
- 意图证据（**唯一有描述的来源**）: `备份\仓库精简-20260829\skills\AI浏览器MCP.md:642`
  > `| browser_reverse_detect_traps | - | **v2.8** 检测7类反调试陷阱(debugger语句/toString重写等) |`
  以及 `MCP_Server.wsv:1244` 注释 `// v2.8 反检测预设 + 逆向增强`（与 `browser_antidetect_presets` id=1320 相邻分配 id=1321）。
- 复用路径: **检测型工具的同族模板** = `browser_reverse_detect_obfuscator`（`MCP_Server_Reverse.wsv:586`，扫脚本判特征给置信度）; 若要检测的具体项是"debugger 语句 / toString 重写 / console 检测 / 时间差检测"等, 可复用 `browser_reverse_scan_crypto`（`MCP_Server_Reverse.wsv:467`）的"扫全部脚本 + 特征清单"实现骨架。
- **重要分叉**: 若最终把它的语义定为"**应用**反检测预设", 那么它被 `browser_antidetect_presets`（`MCP_Server_Core.wsv:6271` 起, 块止于 L6362 前的 `browser_reverse_setup` 分支; stealth/basic/full 三级, 已在 tools/list 注册并实现）**完全覆盖** → 那时应改判 **建议删注册项**, 覆盖者 = `browser_antidetect_presets`。
- 找不到"反调试陷阱检测"的现成实现 → 这部分**需新写**（可复用上述扫描骨架, 但特征规则要新写）。

### 5.12 复用路径小结

| 幽灵 | 工作量估计（基于现有代码） |
|---|---|
| `browser_reverse_network_conditions` `browser_reverse_emulate_focus` `browser_reverse_cache_disable`式 | 抄同域兄弟, 3~6 行 |
| `browser_reverse_cookie_cdp` `browser_reverse_css_coverage` `browser_reverse_trace` `browser_reverse_layer_tree` | 抄 `precise_coverage`/`heap` 骨架 + `执行V8CDP命令`, 5~15 行 |
| `browser_reverse_input_cdp` | 复用 `CDP派发鼠标事件` 等现成原语, 需先确认与 `browser_mouse_click`/`browser_key_event` 的差异点 |
| `browser_fingerprint_languages` `browser_fingerprint_webgl_vendor` | 抄同族单值指纹工具骨架 + VIP API 调用（API 已被调用过）, 6~10 行 |
| `browser_font_randomize` | 复用 `指纹_虚拟CSS字体指纹` + 随机化 + JS 注入骨架（抄 `canvas_noise`） |
| `browser_reverse_detect_traps` | 无现成可复用路径, **需新写**（检测特征规则） |

---

## 6. 附: 全量扫描（本次审计的副产品, 用于证明"16 名单是否完整"）

对**全部 618 个命令注册表键**与**全部 301 个 tools/list 工具名**做了同样的交叉核对（`_audit/g3_sweep.py`）:

| 扫描项 | 结果 |
|---|---|
| tools/list 已登记但分派链无分支 (**AI 可见却不可用**, 最严重一类) | **0 个** |
| 仅在命令注册表、且分派链无分支（含 `browser.` 点号形与短名形的重复计数） | 31 个键 → 去重后**恰好就是这 11 个工具名**（其中 `font_randomize`/`reverse_*` 8 个同时注册了点号形与短名形） |
| 除这 11 个之外的其它死注册项 | **无** |

⇒ 原始 16 人名单在**"真幽灵"这一类上是完整**的（没有漏网之鱼）, 问题只在**多算了 5 个误报**。

---

## 7. 结论（哪些是真的, 哪些不是）

1. **真幽灵 11 个**（tools/list 看不到 + 命令注册表有键 + 7 个分派器全落空）→ 硬调会得到 `-32601 工具不存在: <名>`。
   它们的共同来历很清楚: `MCP_Server.wsv` L1257~L1287 的 **"v2.8 R7/R8/R9 预留号"** 注释块。相邻的 R5/R6 预留号已在 v2.8.2 补齐实现（见 L1288-1296 注释「已在上方预留号, 本次补上实现」）, **R7/R8/R9 这 11 个号被漏了**。
2. **误报 5 个**: `browser_aliases`/`browser_batch` 是 **camel 变体别名**（tools/list 里以 `aliases`/`batch` 注册且工具完整）; `browser_create_tab`/`browser_task_runner_post`/`browser_debugger_pause` 是**有意禁用**的能力, 分派分支**存在且有意返回带替代方案的失败**(不是漏实现)。
3. **被兜底覆盖 0 个**: 7 个分派器均无兜底分支, 全库无 `是否以/包含` 型通配处理。
4. **误报的成因是工具缺陷不是人**: `_audit/cleanup_scan.py` 的 `ghost = reg - tools` 从未检查分派链 —— 正是任务描述里点名要避免的做法。
5. 名单本身还有**另一个方向的不完整**: `_cleanup_report.md` 的"幽灵注册"只覆盖"字典有 / 工具表无"; 本次补上了"**工具表有 / 分派链无**"这一类扫描（结论 0 个, 说明 tools/list 侧是干净的）。

**本报告为静态分诊, 未运行进程、未发任何 MCP 请求, 因此未对"运行时是否真的报 -32601"做实测验证**（那是被禁的动作）; 该结论由 `MCP_Server.wsv` 快照 L10437 → L10084-10086 的代码路径推出。

---

## 8. 证据文件索引

| 文件 | 内容 |
|---|---|
| `_audit\_ghost_triage.md` | 本报告 |
| `_audit\_ghost_snapshot\*.wsv.snapshot.txt` | 冻结的源码快照（审计基线, 后缀非 .wsv） |
| `_audit\_ghost_snapshot\_manifest.json` | 16 个快照文件的 md5 / 字节 / 行数 / mtime |
| `_audit\_ghost_snapshot_manifest.txt` | 同上, 文本形 |
| `_audit\g1_registry.json` | 首轮全量提取（注册表全表 + 7 个分派器分支全表） |
| `_audit\g2_ghost_findings.json` | 16 项判定的结构化结果 |
| `_audit\g2_ghost_evidence.txt` | 16 项判定的人类可读证据（含原文片段） |
| `_audit\g3_sweep.txt` | 全量幽灵扫描 + 47 个复用路径候选的实现状态 |
| `_audit\g3_sweep.json` | 同上, 结构化 |
| `_audit\g0_snapshot.py` `g1_ghost_triage.py` `g2_ghost_audit.py` `g3_sweep.py` | 只读分析脚本（可重跑复现） |
| `_audit\_cleanup_report.md` (既有) | 原始 16 人名单的来源 |
| `_audit\cleanup_scan.py` (既有) | 误报成因所在（L95-102） |
| `备份\仓库精简-20260829\skills\AI浏览器MCP.md` (既有) | `font_randomize` / `detect_traps` 的 schema 与描述、v3.0.0 变更记录（证明 create_tab/task_runner_post 系"移除"而非"漏实现"） |
