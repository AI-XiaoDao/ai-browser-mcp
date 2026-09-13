# `browser_debugger_flow` / `browser_debugger_evaluate` — 精确修改方案（只读分析产物）

**性质声明**：本文全部结论来自**静态阅读源码**。**未编译、未运行、未调用任何 MCP 工具、未修改除本文件外的任何文件。**
本文提出的代码**均未验证、未测试**，不保证可编译或行为正确；请按自己的判断逐条核对后再改。

工作目录：`C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp`
涉及文件：`src\MCP_Server.wsv`（flow 实现 + 通用 helper）、`src\MCP_Server_Core.wsv`（工具分派）——两文件均为 **UTF-8 无 BOM**（已用字节头确认：`<\xe7\x81\xab...`，无 `EF BB BF`），改回时保持原编码。

---

## 0. 对你给的"已知结论"逐条核验

| # | 你的说法 | 核验结果 |
|---|---|---|
| 1 | flow 的实现是 `MCP_Server.wsv` 里的某个方法 | **确认，但名称要更正**：不是 `DebuggerFlow...`，而是 **`方法 执行Debugger断点流程JSON`（`@输出名 = "ExecuteDebuggerBreakpointWorkflowJSON"`）**，定义在 `src\MCP_Server.wsv:3822`。`DebuggerFlow尝试Resume` / `DebuggerFlow失败返回` 是它用的两个小 helper（`:2632`、`:2650`），不是实现本体 |
| 2 | 工具名从 `MCP_Server_Core.wsv` 分派 | **确认**：`src\MCP_Server_Core.wsv:4968` `否则 (方法名 == "browser_debugger_flow")`，实调用在 `:4979` |
| 3 | `CDP设置断点结果是否成功` 只看成功标志、从不看 `locations` | **确认**（`src\MCP_Server.wsv:3593-3603`，逐字见 §1.0）。**补充**：它还额外接受错误文本含 `"already exists"` 的情形 |
| 4 | flow 有约 45000ms 的默认等待预算，超出客户端耐心（测试客户端 15s 放弃） | **确认**（`src\MCP_Server.wsv:3838-3843`，`maxMs = 45000`）。**补充两点**：① `browser_debugger_wait_paused` 在同一函数里也是 45000（`:5693-5696`）；② flow 的**工具级同步预算**是 60000（`:5685-5688`）——但客户端 15s 就放弃，所以 60000 从未成为约束，真正的沉默源就是 45000 |
| 5 | flow 失败返回带 `ok:false, step:"wait_paused"` | **确认**（`src/MCP_Server.wsv:3925`）。语义本身是诚实的：它是超时后才返回的 |
| 6 | helper `MCP命令服务器.CDP断点是否零命中 (存储JSON)` 已存在 | **确认，且名称/签名与你说的一致**：`src\MCP_Server.wsv:3604-3605`，`类型 = 逻辑型`，单参数 `存储JSON <类型 = 文本型>`，`@输出名 = "CDPBreakpointHasZeroLocations"`。**重要补充**：它的实现是**对结果体做字符串匹配**（找 `"locations":[]` 或 `"locations": []`），不是解析数组（逐字见 §1.0）。全仓库只有 `browser_debugger_auto` 在用它（`src\MCP_Server_Core.wsv:5077`）——**flow 是唯一没用的调试类工具** |
| 7 | evaluate 的帧 ID 只来自 `call_frame_id`、逐字透传、无校验、无活帧回退 | **确认**（`src\MCP_Server_Core.wsv:4845-4852` 取值与校验；`:4871` 透传） |
| 8 | 兄弟工具 `browser_debugger_inspect` 会自动取活帧 | **确认**（`src\MCP_Server_Core.wsv:4919-4946`，逐字见 §2.1）。**补充**：台账第 30 轮（`_audit/_tool_ledger.md:193`）显示 inspect 不传帧 ID 时**实测通过**（0.18s，带 `auto_prepared`），即这条活帧路径是**有运行证据**的 |
| 9 | 坏帧 ID 表现为 CDP `-32000 "Invalid call frame id"` 且被无帮助地透传 | **部分确认，且比你说的更糟**（详见 §2.3）：<br>• 透传**确认**（`:4871` 把 CDP 回包原样交回；台账 `_audit/_tool_ledger.md:231` 逐字就是 `{"code":-32000,"message":"Invalid call frame id"}`，且该行 args 无 `parse` → 走的是 `parse:false` 原始路径）。<br>• **但 `parse:true` 路径有第二个缺陷**：`解析Debugger求值结果`（`src\MCP_Server.wsv:3645-3648`）的失败分支只读包装里的 `"message"`，而框架写失败原因用的是 `"error"`／`"result"`（`src\MCP_Server.wsv:2205-2211`），**`"message"` 这个键在失败包装里根本不存在** → 任何真实失败都被翻译成 `{"ok":false,"error":""}`（**原因被吞掉**）。台账 `_tool_ledger.md:99` 那条 evaluate 的 `{"id":"1","success":true,"data":{"ok":false,"error":""}}` 与这个形状完全吻合（我不能断言就是同一次调用，但代码路径是确定的）。<br>• 另有一种更坏的可能（我无法静态判定，见 §4）：若 CDP 层错误被框架判为"传输成功"，则该函数会在 `:3686-3689` 返回 **`{"ok":true,"raw":<CDP错误对象>}`** —— 即**谎报成功** |

### 0.1 另一条重要发现：`_audit/_triage_debugger.md` 的行号已过期，且它的部分建议**已被实现**

你手里"prior analysis"应是 `_audit/_triage_debugger.md`。它的**行号全部漂移**（例如它说 `CDP设置断点结果是否成功` 在 `MCP_Server.wsv:3571-3581`，实际 3593-3603；说 `maxMs=45000` 在 `:3792-3797`，实际 3838-3843；Core 的 evaluate 取值它说 `:4825-4826`，实际 4845-4846）。漂移量还不一致（+22 / +46 / +20），**不能用它的行号做锚点**，请只用本文 §1/§2 的锚点。

它的 C1/C3/C5 三条**已经落地**（落在 `auto` 上，没有落在 `flow` 上）：
- C1 → helper `CDP断点是否零命中` 已存在（`:3604`）并被 auto 使用（Core `:5077`）；
- C3 → auto 零命中已改为**诚实失败**（Core `:5154-5162`）；
- C5 → auto 默认 `max_ms` 已从 60000 压到 12000（Core `:5037-5044`，注释里写着"实测台账客户端 15s 就放弃"）。

它的 C4（零命中快速失败）在 auto 上**被有意否决**了，理由写在 Core `:5070-5077`：

> `// 记录"下断当时是否 0 位置"作为**诊断信息**, 但**不据此提前失败**。`
> `// ★ 实测依据(为什么不能提前失败): 本页所有已注册脚本的 url 都是空串(8/8), 于是任何`
> `//   urlRegex 都得到 locations:[]; 而 0 位置**不等于**永远不可能命中 —— 之后若有带真实`
> `//   URL 的脚本加载(真实站点外部脚本/SPA 动态加载), urlRegex 会在那时重新解析并命中。`
> `//   提前失败会把这种合法等待误判成失败, 反而制造"失败 + 反复换方法"。`

**这直接影响 §1 的 F1**：同一个仓库里已经有"零命中不提前失败、只做说明"的既定决策。你要的"fail fast"与那条政策相反。所以 F1 我给了 **主案（快速失败，按你的要求）** 和 **F1'（与 auto 政策一致：不失败、但把默认等待压到 ~3s 并带上零命中说明）** 两个版本，由你裁决。

---

## 1. Tool 1：`browser_debugger_flow`

### 1.0 需要引用的既有代码（逐字）

**(a) `CDP设置断点结果是否成功` — `src\MCP_Server.wsv:3593-3603`（你看的 helper 缺陷在这里）**

```
    方法 CDP设置断点结果是否成功 <公开 静态 类型 = 逻辑型 @输出名 = "CDPSetBreakpointResultIsSuccess" @强制输出 = 真>
    参数 存储JSON <类型 = 文本型 @输出名 = "StoreJSON">
    {
        如果 (CDP同步结果是否成功 (存储JSON))
        {
            返回 (真)
        }
        变量 errText <类型 = 文本型>
        errText = 取CDP同步结果错误 (存储JSON)
        返回 (寻找文本 (errText, "already exists", 0, 假) != -1)
    }
```

**(b) `CDP断点是否零命中` — `src\MCP_Server.wsv:3604-3627`（你要复用的 helper，逐字全引；含它自己的用法说明）**

```
    方法 CDP断点是否零命中 <公开 静态 类型 = 逻辑型 @输出名 = "CDPBreakpointHasZeroLocations" @强制输出 = 真>
    参数 存储JSON <类型 = 文本型 @输出名 = "StoreJSON">
    {
        // 为什么要单独一个 helper: Debugger.setBreakpointByUrl 在 urlRegex/行号匹配到 **0 个**
        // 脚本位置时**仍然返回成功**(带 "locations":[])。所以"断点设置成功"与"永远不可能命中"
        // 是两件事 —— browser_debugger_auto/flow 曾据此把 0 命中判成设置成功, 然后死等到超时。
        // 判据: 同步**成功** 且 结果体里 locations 是空数组。
        // 用法注意: 只有"调用方不会导航"时 0 位置才是终局失败; 若会导航, urlRegex 会在新脚本上重新解析。
        如果 (CDP同步结果是否成功 (存储JSON) == 假)
        {
            返回 (假)
        }
        变量 体文本 <类型 = 文本型>
        体文本 = 取CDP同步结果体文本 (存储JSON)
        如果 (体文本 == "")
        {
            返回 (假)
        }
        如果 (寻找文本 (体文本, "\"locations\":[]", 0, 假) != -1)
        {
            返回 (真)
        }
        返回 (寻找文本 (体文本, "\"locations\": []", 0, 假) != -1)
    }
```

**签名确认**：名称 `CDP断点是否零命中`，`@输出名 = "CDPBreakpointHasZeroLocations"`，`<公开 静态 类型 = 逻辑型 @强制输出 = 真>`，唯一参数 `存储JSON <类型 = 文本型 @输出名 = "StoreJSON">`。**调用方式**：在 `MCP_Server.wsv` 类的内部**裸名调用** `CDP断点是否零命中 (bpRaw)`（同类内互调，与 `:3894` 的 `CDP设置断点结果是否成功 (bpRaw)` 完全同构）；在 `MCP_Server_Core.wsv` 里则要写 `MCP命令服务器.CDP断点是否零命中 (bpRaw)`。

**一个诚实的局限**：它是**字符串匹配**，所以"命中"的条件是结果体里出现 `"locations":[]` 或 `"locations": []` 这两个字面量。若某天 CDP 回包的空数组写成别的间距（如 `"locations" :[]`），helper 会返回**假**（漏检），此时 flow 只会走原来的超时路径——**失败方向是"漏检"而非"误判零命中"，所以拿它做快速失败的门不会误伤可命中的断点**。这一点对 §1 的风险评估很关键。

### 1.1 现状锚点（flow 本体 `执行Debugger断点流程JSON`）

**(A) 默认等待预算 — `src\MCP_Server.wsv:3838-3843`（6 行整块在 `MCP_Server.wsv` 中出现 **1 次**）**

```
        变量 maxMs <类型 = 整数>
        maxMs = yyjson取整数 (参数JSON, "max_ms")
        如果 (maxMs == 0)
        {
            maxMs = 45000
        }
```
（注：裸串 `45000` 在 `MCP_Server.wsv` 出现 2 次 —— 另一处在 `:5695`（`browser_debugger_wait_paused` 的同步预算）。**上面的 6 行整块是唯一的**，可安全做 find/replace。）

**(B) 设断点 + 只判"设置成功" — `src\MCP_Server.wsv:3892-3899`（我给的 4 行锚点在文件中出现 **1 次**）**

```
        变量 bpRaw <类型 = 文本型>
        bpRaw = 执行CDP并同步等待 (命令ID + "_bp", "Debugger.setBreakpointByUrl", bpParams.到可读文本 (YYJSON格式化选项.压缩), 20000)
        如果 (CDP设置断点结果是否成功 (bpRaw) == 假)
        {
            返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",\"error\":\"" + MCP_响应构建.JSON转义文本 (取CDP同步结果错误 (bpRaw)) + "\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\"}"))
        }
        // 须在 navigate 之前清除,否则加载时命中断点的事件会被误删
        清除CDP事件记录 ("Debugger.paused")
        如果 (navUrl != "")
```
关键顺序事实（做 F1 必须知道）：**`navUrl` 在 `:3837` 就已读出**，**设断点在 `:3893`、导航在 `:3918`** —— 所以新增的零命中判断天然落在"导航之前"，语义正确。

**(C) 等待 + 超时返回 — `src\MCP_Server.wsv:3921-3926`（4 行锚点在文件中出现 **1 次**）**

```
        变量 pausedRaw <类型 = 文本型>
        pausedRaw = 等待CDP事件 ("Debugger.paused", maxMs, 假)
        如果 (pausedRaw == "")
        {
            返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"wait_paused\",\"error\":\"timeout\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\"}"))
        }
```
（`breakpoint` 字段里是 `bpRegex`，即调用方传的 `breakpoint` 正则，不是 URL；超时返回体里**没有** `waited_ms`，也**没有**任何原因说明。）

**(D) 分派层（**本方案不改**，仅说明它如何消费上面的 JSON）— `src/MCP_Server_Core.wsv:4968-4985`**

```
        否则 (方法名 == "browser_debugger_flow")
        {
            变量 flowBp <类型 = 文本型>
            flowBp = MCP命令服务器.yyjson取文本 (参数JSON, "breakpoint")
            如果 (flowBp == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "breakpoint 不能为空 | URL正则, 如: example\\.com/main\\.js | 无参调用不会进入断点流程"))
            }
            // 自愈: 反检测Debugger禁用与断点冲突, 自动恢复防止渲染进程illegal instruction崩溃
            MCP命令服务器.确保Debugger可用 (MCP命令服务器.取主浏览器 ())
            变量 flowJSON <类型 = 文本型>
            flowJSON = MCP命令服务器.执行Debugger断点流程JSON (命令ID, 参数JSON)
            如果 (flowJSON == "" || MCP命令服务器.是否以 (flowJSON, "{\"ok\":false"))
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "debugger_flow 失败: " + flowJSON))
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, flowJSON))
        }
```
→ 分派层**只检查前缀 `{"ok":false`**，其余字段原样吞进 `error` 字符串。所以 §1.3 往失败体里**追加字段是前向兼容的**；但 `"step":"wait_paused","error":"timeout"` 这两个键值**必须保留原样**，免得破坏按它分类的消费方（例如 `_audit/tool_ledger.py` 之类台账/脚本）。

**另一处必须一并改的文案（否则描述与实现不一致）**：`src\MCP_Server.wsv:9664` 的 flow schema —— 其中 `属性项JSON ("max_ms", "integer", "等待暂停毫秒")`。该行整行在文件中出现 1 次。

---

### 1.2 F1（主案）：零命中 + 不会导航 → 立即失败

* **锚点（B）**的 4 行，`src\MCP_Server.wsv:3894-3897`，**唯一**。
* **替换为**（`old_string` = 上面 4 行，`new_string` = 下面整块）：

```
        如果 (CDP设置断点结果是否成功 (bpRaw) == 假)
        {
            返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",\"error\":\"" + MCP_响应构建.JSON转义文本 (取CDP同步结果错误 (bpRaw)) + "\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\"}"))
        }
        // 修(零命中假成功): "断点设置成功" != "断点能命中"。Debugger.setBreakpointByUrl 在 urlRegex
        // 匹配到 0 个脚本位置时仍返回成功(locations 为空), 此时**若本次不导航**就不会再加载新脚本,
        // 等 maxMs 注定白等。复用既有 helper CDP断点是否零命中, 不新增判定逻辑。
        // 只判 navUrl == "" 的场合: 有 url 时新脚本尚未加载, 0 位置是正常中间态。
        变量 flowBp零命中 <类型 = 逻辑型 值 = 假>
        flowBp零命中 = CDP断点是否零命中 (bpRaw)
        如果 (flowBp零命中 && navUrl == "")
        {
            返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",\"error\":\"zero_locations\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\",\"line\":" + 到文本 (flowLine) + ",\"hint\":\"下断时该 URL 正则与当前页面已加载脚本无一匹配(locations 为空), 且本次未传 url 不会导航, 故该断点此刻不可能命中, 不再空等 | 可行动: ①传 url 让本工具导航触发 ②用 browser_reverse_get_possible_breakpoints 或 browser_reverse_search_script 查真实脚本 URL 与可下断行列 ③若确信之后会有匹配脚本被动态注入加载, 改用 browser_debugger_auto (它不提前失败, 只把零命中作为说明返回)\"}"))
        }
```

* **为什么用这个 helper 而不是自己解析**：`CDP断点是否零命中` 的注释里已经写明它就是为 `browser_debugger_auto/flow` 的这个问题写的（"…曾据此把 0 命中判成设置成功, 然后死等到超时"），并且它的"用法注意"一条正是 F1 的门条件（"只有'调用方不会导航'时 0 位置才是终局失败"）。
* **依赖**：本块声明的 `flowBp零命中` 被 F3 使用，所以 **F1 必须先于 F3 落**（或两处一起落），否则 F3 会引用未声明变量。

### 1.3 F1'（备选，与仓库既有政策一致）：不失败，但把这次等待压短

若你认可 Core `:5070-5077` 那条"提前失败会把合法等待误判成失败"的政策，就别做 F1 的硬失败，改成：

```
        变量 flowBp零命中 <类型 = 逻辑型 值 = 假>
        flowBp零命中 = CDP断点是否零命中 (bpRaw)
        // 零命中且不导航: 不做终局失败, 但也不空等 maxMs —— 压到 3s 让调用方在客户端耐心内拿到
        // 带零命中说明的诚实超时(与 browser_debugger_auto 的"只说明不提前失败"政策一致)。
        如果 (flowBp零命中 && navUrl == "" && maxMs > 3000)
        {
            maxMs = 3000
        }
```
（`maxMs` 在 `:3838` 已声明，此处只赋值，不重复声明。）
**取舍**：F1' 绝不会把"其实会命中"的调用判成失败，但也**不会省掉一次 3s 的等待**，且它改的是"静默时长"而不是"成功概率"。台账那条 `mcp_probe` 用例在 F1' 下会得到 `ok:false, step:"wait_paused", error:"timeout", reason:"…零命中…"`（诚实、可行动），而不是 `zero_locations`。

### 1.4 F2：默认等待预算 45000 → 12000

* **锚点（A）**，`src/MCP_Server.wsv:3838-3843`，**唯一**。
* **替换为**：

```
        变量 maxMs <类型 = 整数>
        maxMs = yyjson取整数 (参数JSON, "max_ms")
        如果 (maxMs == 0)
        {
            // 原默认 45000ms: 远超常见客户端耐心(台账实测客户端 15s 就放弃), 结果是
            // "客户端先超时 + 服务端还在等" —— 调用方只看到 timed out, 看不到任何原因。
            // 压到 12000ms(与 browser_debugger_auto 的同类决定一致): 让服务端在客户端放弃之前
            // 给出明确结论。需要更久请显式传 max_ms。
            maxMs = 12000
        }
```
* 同时把 schema 文案对齐 —— `src\MCP_Server.wsv:9664` 中：
  `属性项JSON ("max_ms", "integer", "等待暂停毫秒")` → `属性项JSON ("max_ms", "integer", "等待暂停毫秒(默认12000; 客户端自身超时更短时请调低)")`。
* **不要动** `src\MCP_Server.wsv:5685-5688` 的工具级同步预算 60000：它只是"服务端最多阻塞多久"的上限，默认 12000 < 15000 < 60000，改了没有收益，反而会影响显式传大 `max_ms` 的调用方。

### 1.5 F3：让超时失败说出原因

* **锚点（C）**的 4 行，`src\MCP_Server.wsv:3923-3926`，**唯一**。
* **替换为**：

```
        如果 (pausedRaw == "")
        {
            // 修(失败不给原因): 原返回体只有 error:"timeout", 调用方看不出等了多久、为什么没等到。
            // 保留 step/error 两个既有键值不动(有消费方按键值分类), 只**追加**原因与可行动提示。
            变量 flow等待说明 <类型 = 文本型>
            flow等待说明 = "等待 Debugger.paused 超时(" + 到文本 (maxMs) + "ms): 该窗口内页面未执行到断点位置"
            如果 (flowBp零命中)
            {
                flow等待说明 = flow等待说明 + " | 注: 下断当时该 urlRegex 匹配到 0 个脚本位置(locations 为空) —— 当前页没有可命中该断点的代码; 若之后有带真实 URL 的脚本加载仍可能命中"
            }
            如果 (navUrl == "")
            {
                flow等待说明 = flow等待说明 + " | 本次未传 url, flow 自身不会触发页面加载"
            }
            返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"wait_paused\",\"error\":\"timeout\",\"waited_ms\":" + 到文本 (maxMs) + ",\"reason\":\"" + MCP_响应构建.JSON转义文本 (flow等待说明) + "\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\",\"hint\":\"可行动: ①传 url 让本工具导航触发 ②browser_reverse_get_possible_breakpoints 查可下断行列 ③显式传更大的 max_ms 继续等(注意客户端自身超时更短)\"}"))
        }
```

* 注意：`reason` 里若塞中文引号以外的原样 `"` 会破坏 JSON —— 上面的文案**没有**内嵌双引号；`flow等待说明` 又经 `MCP_响应构建.JSON转义文本` 转义，是安全的。`hint` 是字面量、同样无内嵌双引号。

### 1.6 flow 改动汇总（应用顺序）

1. **F2**（`:3838-3843`）+ schema 文案（`:9664`）—— 独立，可先落。
2. **F1**（`:3894-3897`，或 F1'）—— 引入 `flowBp零命中`。
3. **F3**（`:3923-3926`）—— 依赖 F1/F1' 的变量。
4. 落完后建议自查：`flowBp零命中` 在本文件应恰好出现 5 次（1 次声明 + 1 次赋值 + F1 的 1 次判断 + F3 的 1 次判断… 具体以你最终文案为准）；`CDP断点是否零命中` 在 `MCP_Server.wsv` 里应从 1 次（仅定义）变成 2 次（定义 + 调用）。

---

## 2. Tool 2：`browser_debugger_evaluate`

### 2.1 要复用/对照的既有代码（逐字）

**(a) 现况：evaluate 分派 — `src\MCP_Server_Core.wsv:4843-4872`**

```
        否则 (方法名 == "browser_debugger_evaluate")
        {
            变量 frameId <类型 = 文本型>
            frameId = MCP命令服务器.yyjson取文本 (参数JSON, "call_frame_id")
            变量 expr <类型 = 文本型>
            expr = MCP命令服务器.yyjson取文本 (参数JSON, "expression")
            如果 (frameId == "" || expr == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "call_frame_id和expression " + MCP_常量.错误_缺少参数))
            }
            如果 (MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "parse", 假))
            {
                变量 expandEv <类型 = 逻辑型>
                expandEv = MCP命令服务器.取Debugger求值展开 (参数JSON)
                变量 rbvEv <类型 = 逻辑型>
                rbvEv = MCP命令服务器.取Debugger求值ReturnByValue (参数JSON)
                变量 evRaw <类型 = 文本型>
                evRaw = MCP命令服务器.执行Debugger帧求值并等待 (命令ID, frameId, expr, 12000, rbvEv)
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.解析Debugger求值结果 (evRaw, 命令ID, frameId, expr, expandEv)))
            }
            变量 evParams <类型 = YYJSON对象类>
            evParams.创建自文本 ("{}")
            evParams.加入文本成员 ("callFrameId", frameId)
            evParams.加入文本成员 ("expression", expr)
            如果 (MCP命令服务器.取Debugger求值ReturnByValue (参数JSON))
            {
                evParams.加入逻辑值成员 ("returnByValue", 真)
            }
            返回 (MCP命令服务器.执行CDP命令_带参数 (命令ID, "Debugger.evaluateOnCallFrame", evParams.到可读文本 (YYJSON格式化选项.压缩)))
        }
```
（`:4845-4852` 那 8 行整块在 `MCP_Server_Core.wsv` 中出现 **1 次**；`:4871` 那一行 `返回 (…执行CDP命令_带参数 (命令ID, "Debugger.evaluateOnCallFrame", …))` 也出现 **1 次**。）

**(b) `browser_debugger_inspect` 的活帧获取逻辑 — `src\MCP_Server_Core.wsv:4919-4946`（这就是你要复用的东西）**

```
        否则 (方法名 == "browser_debugger_inspect")
        {
            变量 frameId2 <类型 = 文本型>
            frameId2 = MCP命令服务器.yyjson取文本 (参数JSON, "call_frame_id")
            如果 (frameId2 == "")
            {
                // 零前置: 未给帧ID 且页面未暂停时, 先自动制造暂停点(已暂停则立即返回真)
                如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "无法自动制造暂停点(已安排执行点 + Debugger.pause 并等待5秒仍未收到 Debugger.paused) | 可能原因: 页面没有可执行的JS(纯静态页/about:blank) 或 CDP 通道不可用 | 替代: browser_debugger_flow 一键断点流程"))
                }
                变量 rawInspect <类型 = 文本型>
                rawInspect = MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")
                如果 (rawInspect != "")
                {
                    变量 暂停摘要 <类型 = 文本型>
                    暂停摘要 = MCP命令服务器.解析Debugger暂停摘要 (rawInspect)
                    变量 暂停解析 <类型 = YYJSON只读对象类>
                    如果 (暂停解析.创建自文本 (暂停摘要))
                    {
                        frameId2 = MCP命令服务器.yyjson取文本 (暂停解析, "call_frame_id")
                    }
                }
            }
            如果 (frameId2 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "缺少 call_frame_id | 请先 browser_debugger_wait_paused 或 browser_debugger_last_paused"))
            }
```
（锚点 `frameId2 = …"call_frame_id"` + `如果 (frameId2 == "")` + `{` 这 4 行，在 `MCP_Server_Core.wsv` 中出现 **1 次**。）

**它依赖的 3 个既有 helper（都已在用、无需新增）**：
- `MCP命令服务器.确保调试器已暂停 (命令ID)` — `src\MCP_Server.wsv:1658`，语义："已暂停则立即返回真；否则先 `Debugger.enable` → 用 `setTimeout(...,30)` 安排执行点 → `Debugger.pause` → 等 `Debugger.paused`（每轮 6000ms，最多 2 轮）"，成功时还会 `MCP_响应构建.记录自动处理 ("Debugger.pause(…)")`，这就是台账里 inspect 响应中 `auto_prepared` 字段的来源（`_audit/_tool_ledger.md:193`）。
- `MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")` — 读最近一次暂停事件。
- `MCP命令服务器.解析Debugger暂停摘要 (rawInspect)` — `src\MCP_Server.wsv:2736`，返回体含 `"call_frame_id"`（`frames[0].callFrameId`）以及 `"frames"`（最多 8 条，`:2812`）。

**(c) 你在问的"翻译调试器求值错误"的 helper —— 存在，但是有缺陷的**

`执行Debugger帧求值并等待` — `src\MCP_Server.wsv:2822-2845`：

```
    方法 执行Debugger帧求值并等待 <公开 静态 类型 = 文本型 @输出名 = "ExecuteDebuggerFrameEvaluateAndWait" @强制输出 = 真>
    参数 命令ID <类型 = 文本型 @输出名 = "CommandID">
    参数 callFrameId <类型 = 文本型 @输出名 = "CallFrameID">
    参数 expression <类型 = 文本型 @输出名 = "Expression">
    参数 最大毫秒 <类型 = 整数 @默认值 = 8000 @输出名 = "MaxMs">
    参数 returnByValue <类型 = 逻辑型 @默认值 = 真 @输出名 = "ReturnByValue">
    {
        如果 (callFrameId == "" || expression == "")
        {
            返回 ("")
        }
        变量 evParams <类型 = YYJSON对象类>
        evParams.创建自文本 ("{}")
        evParams.加入文本成员 ("callFrameId", callFrameId)
        evParams.加入文本成员 ("expression", expression)
        如果 (returnByValue)
        {
            evParams.加入逻辑值成员 ("returnByValue", 真)
        }
        变量 子ID <类型 = 文本型>
        子ID = 命令ID + "_ev"
        执行CDP命令_带参数 (子ID, "Debugger.evaluateOnCallFrame", evParams.到可读文本 (YYJSON格式化选项.压缩))
        返回 (同步等待异步任务 (子ID, 最大毫秒))
    }
```
→ 它是"发命令 + 同步等取回**异步结果包装 JSON**"，**不做任何错误翻译**。

`解析Debugger求值结果` — `src/MCP_Server.wsv:3629-3648`（只引前 20 行，失败分支就是问题所在）：

```
    方法 解析Debugger求值结果 <公开 静态 类型 = 文本型 @输出名 = "ParseDebuggerEvaluateResult" @强制输出 = 真>
    参数 异步结果JSON <类型 = 文本型 @输出名 = "AsyncResultJSON">
    参数 命令ID前缀 <类型 = 文本型 @默认值 = "" @输出名 = "CommandIDPrefix">
    参数 callFrameId <类型 = 文本型 @默认值 = "" @输出名 = "CallFrameID">
    参数 expression <类型 = 文本型 @默认值 = "" @输出名 = "Expression">
    参数 展开对象 <类型 = 逻辑型 @默认值 = 假 @输出名 = "ExpandObject">
    {
        如果 (异步结果JSON == "")
        {
            返回 ("{\"ok\":false,\"error\":\"empty\"}")
        }
        变量 包装 <类型 = YYJSON只读对象类>
        如果 (包装.创建自文本 (异步结果JSON) == 假)
        {
            返回 ("{\"ok\":false,\"error\":\"invalid_json\"}")
        }
        如果 (yyjson取逻辑 (包装, "success") == 假)
        {
            返回 ("{\"ok\":false,\"error\":\"" + MCP_响应构建.JSON转义文本 (yyjson取文本 (包装, "message")) + "\"}")
        }
```
**复用判定**：
- `执行Debugger帧求值并等待` —— **适合复用**（它就是为 `Debugger.evaluateOnCallFrame` 写的那一条路径，parse 分支已在用）。
- `解析Debugger求值结果` —— **是唯一存在的"调试器求值错误翻译器"，应当复用，但它当前的失败分支有确定缺陷**：只读包装里的 `"message"`。而失败包装是由 `处理CDP响应` 写的（`src\MCP_Server.wsv:2205-2211`）：`{"success":false,…,"error":<CDP回包文本>}`（成功时写 `"result"`）；`同步等待异步任务` 超时返回**空串**（`:5961`，随后被 `:3636` 的 `AsyncResultJSON == ""` 分支接住 → `"empty"`）。所以 `"message"` 这个键在这条链路上**不存在** → **任何 CDP 层失败的原因都会丢成 `""`**。台账 `_tool_ledger.md:99` 的 `{"ok":false,"error":""}` 正是这个形状。
- 全仓库**没有**任何一处把 `-32000` / `Invalid call frame id` 翻译成人话（我 grep 过 `src\*.wsv`：`-32000` 只在 `src\MCP_Server.wsv:8972` 出现一次，是 JSON-RPC 关闭码，与调试器无关）。**结论：须新增"可行动文案"，不能指望"复用现成的翻译"**。

### 2.2 E1：`call_frame_id` 为空时自动取活帧（复用 inspect 的逻辑）

* **锚点**：`src\MCP_Server_Core.wsv:4845-4852` 的 8 行整块（**唯一**，逐字见 §2.1(a) 的前 10 行中的 4845-4852）。
* **替换为**：

```
            变量 frameId <类型 = 文本型>
            frameId = MCP命令服务器.yyjson取文本 (参数JSON, "call_frame_id")
            变量 expr <类型 = 文本型>
            expr = MCP命令服务器.yyjson取文本 (参数JSON, "expression")
            如果 (expr == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "expression " + MCP_常量.错误_缺少参数))
            }
            如果 (frameId == "")
            {
                // 零前置(与 browser_debugger_inspect 同源逻辑, 见本文件 :4919-4946 的 inspect 分支):
                // 未给帧ID 时自动取"当前活帧" —— 已暂停则直接复用, 未暂停则先制造暂停点
                // (会经 auto_prepared 如实上报), 再从最近一次 Debugger.paused 读 call_frame_id。
                如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "未给 call_frame_id 且无法自动制造暂停点(已安排执行点 + Debugger.pause 并等待5秒仍未收到 Debugger.paused) | 可能原因: 页面没有可执行的JS(纯静态页/about:blank) 或 CDP 通道不可用 | 可行动: browser_debugger_wait_paused / browser_debugger_last_paused 取帧后立即重试, 或用 browser_debugger_inspect"))
                }
                变量 rawEvPaused <类型 = 文本型>
                rawEvPaused = MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")
                如果 (rawEvPaused != "")
                {
                    变量 evPauseSummary <类型 = 文本型>
                    evPauseSummary = MCP命令服务器.解析Debugger暂停摘要 (rawEvPaused)
                    变量 evPauseObj <类型 = YYJSON只读对象类>
                    如果 (evPauseObj.创建自文本 (evPauseSummary))
                    {
                        frameId = MCP命令服务器.yyjson取文本 (evPauseObj, "call_frame_id")
                    }
                }
            }
            如果 (frameId == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "无法取得活帧 call_frame_id | 可行动: browser_debugger_wait_paused 或 browser_debugger_last_paused 取帧后立即重试"))
            }
```

**关于"复用方式"的取舍（请裁决）**：
- **主案（上面这版）= 把 inspect 的那 20 行原样搬进 evaluate**。优点：只改 1 个文件、不新增任何方法/输出名（`MCP_Server.wsv` 里 255 个 `方法` 定义中 254 个带 `<公开>`、**255 个全部带 `@输出名`**（已统计），所以"新增一个 helper"必然要新增一个导出符号，会牵动 `输出名对照表.md`（由 `_audit/b8_doc.py` 生成）与符号审计脚本）；inspect 一行不动（零回归面）。缺点：同一逻辑出现两份，与仓库里"同一逻辑只留一份实现"的既有注释习惯相悖（如 `src\MCP_Server.wsv:2348`、`src\MCP_Server_Core.wsv:4883-4885`）。
- **备选 = 抽一个新 helper**（例如 `方法 取Debugger活帧ID <公开 静态 类型 = 文本型 @输出名 = "GetDebuggerLiveFrameID" @强制输出 = 真>`，参数 `命令ID`），把 inspect 与 evaluate 都改成调它。优点：一份实现；缺点：新增公开符号要同步 `输出名对照表.md`，且要动 inspect（虽然只是等价替换），**回归面比主案大**。
- 我按你"最小改动 + 别写新逻辑"的要求推荐**主案**；若你要的是"一次到位、不留两份实现"，再走备选。

### 2.3 E2：schema 必须同步（否则客户端会把"不传帧 ID"挡在门外）

* **锚点**：`src\MCP_Server.wsv:9660` 的 evaluate 工具声明行（整行在文件中出现 **1 次**）。其中两处需要改：
  - `属性项JSON ("call_frame_id", "text", "帧ID")` —— 该片段在 `MCP_Server.wsv` 出现 **1 次**（inspect/script_source 的文案是 `"帧ID(空=最近paused)"`，不冲突）。
  - 必填列表 `"\"call_frame_id\",\"expression\""` —— 在 `MCP_Server.wsv` 出现 **1 次**。
* **改为**：
  - `属性项JSON ("call_frame_id", "text", "帧ID(空=自动取最近暂停的活帧, 会自动制造暂停点)")`
  - 必填列表 → `"\"expression\""`
* **理由**：inspect 的 schema 就是 `"帧ID(空=最近paused)"` 且必填列表只有 `"\"expressions\""`（`src\MCP_Server.wsv:9663`），evaluate 要与兄弟工具一致；不改必填列表的话，严格按 schema 校验的客户端根本不会发出"不带 call_frame_id"的调用，E1 就永远不会被走到。
* **这是契约变更**，不是纯增量：显式依赖"call_frame_id 必填"的客户端/文档会看到变化（功能上更宽松，但属于接口行为改变）。同时建议在描述里点明帧的生命周期（原 triage 的 C8）："…与暂停点绑定, 页面 resume 后即失效 —— flow/auto 默认 resume:true"。

### 2.4 E3：把 `-32000` / `Invalid call frame id` 变成可行动错误

**(a) 零形状改动的一步（推荐先做）：修 `解析Debugger求值结果` 的失败分支并加提示**

* **锚点**：`src\MCP_Server.wsv:3645-3648` 的 4 行（**唯一**，逐字）：

```
        如果 (yyjson取逻辑 (包装, "success") == 假)
        {
            返回 ("{\"ok\":false,\"error\":\"" + MCP_响应构建.JSON转义文本 (yyjson取文本 (包装, "message")) + "\"}")
        }
```
* **替换为**：

```
        如果 (yyjson取逻辑 (包装, "success") == 假)
        {
            // 修(失败原因被吞): 原来只读包装里的 "message" —— 但写入失败原因的是处理CDP响应
            // (src\MCP_Server.wsv:2205-2211), 它写的键是 "error"(失败) / "result"(成功), 从来没有
            // "message"; 于是任何真实失败都被翻译成 {"ok":false,"error":""}, 调用方看不到原因。
            变量 求值失败原因 <类型 = 文本型>
            求值失败原因 = yyjson取文本 (包装, "message")
            如果 (求值失败原因 == "")
            {
                求值失败原因 = yyjson取文本 (包装, "error")
            }
            如果 (求值失败原因 == "")
            {
                求值失败原因 = yyjson取文本 (包装, "result")
            }
            // 把"帧 ID 失效"翻译成可行动提示(帧 ID 是 CDP 的不透明句柄, 工具无法修复调用方给的旧帧,
            // 只能说明它从哪来、为什么会失效 —— 这是"让失败可行动", 不是"让它成功")。
            如果 (寻找文本 (求值失败原因, "Invalid call frame id", 0, 假) != -1)
            {
                求值失败原因 = 求值失败原因 + " | call_frame_id 与当前暂停点绑定: 页面 resume 之后立即失效 —— 而 browser_debugger_flow / browser_debugger_auto 默认 resume:true, 它们返回体里的 paused.call_frame_id 在返回时通常已失效 | 取活帧: browser_debugger_wait_paused 或 browser_debugger_last_paused, 拿到后立即 evaluate; 也可以不传 call_frame_id(本工具会自动取活帧)"
            }
            如果 (求值失败原因 == "")
            {
                求值失败原因 = "cdp_failed"
            }
            返回 ("{\"ok\":false,\"error\":\"" + MCP_响应构建.JSON转义文本 (求值失败原因) + "\"}")
        }
```
* **覆盖面**：`解析Debugger求值结果` 被 `evaluate(parse:true)`、`Debugger帧内批量求值JSON`（→ `flow`、`inspect`、`auto` 全走这条）共同使用 —— 所以这一处修好，**所有"同步解析"路径的失败原因都不再是空串**，并且都会带上帧失效的行动指引。
* **风险**：只改 `success == 假` 分支，**成功路径一个字符都不动**（严格增量）；唯一行为变化是失败时的 `error` 文案从 `""` 变成真实原因 + 提示。

**(b) 覆盖 `parse:false` 原始路径 —— 需要形状变更（可选，请你裁决）**

台账那条 `-32000` 走的是 `parse:false`（`:4871`，原样透传），**它不经过上面的翻译器**。要让它也可行动，只能把这一行改成走同步 helper：

* **锚点**：`src\MCP_Server_Core.wsv:4871` 一行（**唯一**）：

```
            返回 (MCP命令服务器.执行CDP命令_带参数 (命令ID, "Debugger.evaluateOnCallFrame", evParams.到可读文本 (YYJSON格式化选项.压缩)))
```
* **可行的替换（示意）**：用 `执行Debugger帧求值并等待 (命令ID, frameId, expr, 12000, evRbV)` 同步取回结果 → 交给 `解析Debugger求值结果 (…, 展开对象:假)` → 若 `ok:false` 则 `命令失败` 带上面那段行动指引；否则 `命令成功_原始JSON`。
  （`取Debugger求值ReturnByValue` 已在 `:4867` 用过，语义可保留；`展开对象` 传假以贴近原路径"不做属性展开"的行为。）
* **为什么我**不推荐**默认做这一步**：
  1. 它把 `parse:false` 从"**异步占位 + task_id**"（`执行CDP命令_带参数` 返回 `{"success":true,"_async":true,"task_id":…}`，见 `src\MCP_Server.wsv:1648`）改成"同步阻塞返回 data 形状"——**响应契约变了**，外部脚本若依赖 task_id 轮询会被打断；
  2. 延迟从"立即返回"变成"最多 12000ms"（工具级同步预算是 20000，见 `src\MCP_Server.wsv:5697-5700`，放得下，但终究是行为变化）；
  3. `parse` 这个开关的**设计意图**就是"true=同步解析 / false=异步原始"（分派 `:4853`），改掉它等于取消这个区分。
* 折中建议：先做 (a) + E2 的 schema 文案（把"帧 ID 与暂停点绑定、resume 即失效、不传则自动取活帧"写进描述），让 `parse:false` 的调用方**在文档层**拿到行动指引；如果之后台账里 `parse:false` 的 `-32000` 仍反复出现，再单独评估 (b)。

**(c) 已考虑但不建议的做法**
- **按格式校验帧 ID**（例如"不含 `{`/小数点就拒绝"）：帧 ID 的真实格式我无法静态确证（见 §4），误拒合法帧的风险高于收益，**不建议**。
- **拿"当前活帧 ID"做硬校验**（当前暂停摘要里的 `frames` 只有最多 8 条，`src\MCP_Server.wsv:2812`）：帧序号 >8 的合法帧会被误判为失效，**不建议做阻断式校验**（最多只能当"提示"用）。

### 2.5 evaluate 改动汇总

| 步骤 | 锚点 | 是否推荐 |
|---|---|---|
| E1 自动取活帧 | `MCP_Server_Core.wsv:4845-4852`（唯一） | 推荐（你要的核心修复） |
| E2 schema 文案 + 必填列表 | `MCP_Server.wsv:9660`（两处片段各唯一） | 推荐（E1 的必要配套） |
| E3(a) 失败原因 + 帧失效提示 | `MCP_Server.wsv:3645-3648`（唯一） | 推荐（零形状改动、失败路径增量） |
| E3(b) parse:false 改走同步 helper | `MCP_Server_Core.wsv:4871`（唯一） | 可选，需你确认接受契约变更 |

---

## 3. 风险与行为影响（第 4 条要求：是否"严格增量"）

| 改动 | 对"传了合法帧 ID / 断点真能命中"的调用方 | 是否严格增量 | 说明 |
|---|---|---|---|
| **F1** 零命中+不导航 → 立即失败 | **无影响**：`CDP断点是否零命中` 只有结果体里出现字面量 `"locations":[]` 才返真，能命中的断点会返回假 | **否** | 受影响的是"下断时 0 位置、靠**之后动态加载的脚本**命中"的合法场景（Core `:5070-5077` 有实测记录：本页 8/8 脚本 url 都是空串）。这类调用会从"等 maxMs 后可能命中"变成"立即失败"。**这是产品语义取舍，不是纯增量** |
| **F1'** 零命中+不导航 → 只把 `maxMs` 压到 3s | **无影响** | **是**（除"等待变短"外不改语义）：它仍返回 `ok:false, step:"wait_paused", error:"timeout"` | 与仓库既有政策一致；代价是仍有一次 3s 沉默 |
| **F2** 默认 45000 → 12000 | **近乎无影响**：默认路径下"能命中"的断点通常在导航后 1-2s 内就暂停 | **否** | 受影响的是"客户端超时 >45s 且脚本命中耗时 12-45s"的调用方：以前会成功，现在会诚实超时（可显式传 `max_ms` 恢复）。**必须明确：F2 不提高成功率，只把"客户端超时（看不到原因）"换成"服务端诚实失败"** |
| **F3** 超时附带原因 | **无影响**（真命中的调用永远走不到这一支） | **是** | 只在既有失败体上**追加** `waited_ms`/`reason`/`hint`；`step`/`error` 原值保留；分派层只检查 `{"ok":false` 前缀（Core `:4980`） |
| **E1** 帧 ID 为空时自动取活帧 | **无影响**（非空帧 ID 走原路径，一行不改） | **是**（对合法调用） | 行为变化只发生在"帧 ID 为空"这一支：以前**立即失败**（`call_frame_id和expression 参数不能为空`），现在会先尝试制造暂停点（**会改变页面暂停状态**，并通过 `auto_prepared` 如实上报——与 inspect/stack 的既定零前置行为一致） |
| **E2** schema 文案 + 必填列表 | 无功能影响 | **否（接口契约变更）** | 必填项减少是放宽，但依赖"必填"做校验/文档的消费方会看到变化 |
| **E3(a)** 失败原因 + 帧失效提示 | **无影响**（成功路径不动） | **是**（失败路径） | 顺带修掉一个确定缺陷：失败原因此前恒为空串 |
| **E3(b)** parse:false 改同步 | **无影响** | **否** | 响应形状从 async(task_id) 变 data，外部依赖 task_id 的脚本会断 |

**必须诚实标注的"这是让失败可行动、不是让它成功"的三处**：
1. **F2** —— 12s 只是把沉默缩短、把结论提前到客户端耐心内，**不提高命中率**。
2. **F1** 的零命中判定 —— 无可命中的断点**等不出来**；正确修法是把事实（`locations:[]` 且未传 `url`）作为错误/说明交出去，而不是延长等待。F1 与 F1' 的差别只是"交出去的方式"。
3. **E3** 的 `-32000` —— 帧 ID 是 CDP 的不透明句柄，工具**无法**修复调用方给的旧帧/编造的帧，只能说明"它从哪来、何时失效、怎么取活帧"。**不要**试图靠格式校验或猜测让它"成功"。

---

## 4. 我**无法**通过阅读确定的事项（未做任何运行验证）

1. **CDP 层错误（`-32000`）到底被框架判为"传输成功"还是"传输失败"。** `成功` 标志由闭源 VIP 类 `类_FBrowserVIP_控制器` / `类_FBrowser_开发者消息事件` 的 `开发者消息_VIP_执行完成` 回传（`src\MCP_Callbacks.wsv:513-522`），源码不在本仓库。这决定了两个后果之一：
   - 若为"传输失败" → 包装写 `"error"` → `parse:true` 得到 `{"ok":false,"error":""(现状)}`（E3(a) 会把它变成有原因）；
   - 若为"传输成功" → CDP 回包被放进 `"result"` → `解析Debugger求值结果` 会走到 `src\MCP_Server.wsv:3686-3689` 返回 **`{"ok":true,"raw":{…error…}}`**，即 `parse:true` **谎报成功**（这是我按代码读出的第三条缺陷，但**未能证实是否可达**）。
2. **台账 `_tool_ledger.md:231` 那条 `{"code":-32000,"message":"Invalid call frame id"}` 的准确出处**：它所在的 args（`_audit/_triage_debugger.md:23`：`{"call_frame_id":"mcp_probe","expression":"1"}`，无 `parse`）指向 `parse:false` 原始路径，但我无法确定探针/桥接层是如何把这个字符串从异步结果里解出来的（该字符串没有 `"id"` 外壳，与 `处理CDP响应` 存的原文不完全一致）。
3. **`Debugger.setBreakpointByUrl` 在本 CEF/V8 构建上的空匹配回包是否真是字面量 `"locations":[]`（或 `"locations": []`）。** 这正是 `CDP断点是否零命中` 的判据所假设的；我没有运行验证（`_audit/_triage_debugger.md:866` 也把它列为未知）。若实际格式不同，helper 会**漏检**（返回假）→ F1 不触发、只退化回 F3 的超时路径。
4. **生产客户端的真实超时。** 我只有审计探针的硬编码 15s（`_audit/tool_ledger.py`，被 triage 引作 `:46`）。12000 / 3000 都是我（与 triage）按"15s − 余量"选的**启发式**，不是实测值。
5. **是否有仓库外的调用方依赖** evaluate `parse:false` 的异步形状（`task_id`）、或依赖 flow 失败体里的键集合。仓库内的 `workflows\debugger_full.json` **不调用** `browser_debugger_flow`（它手工编排 enable→bp→navigate→wait_paused→inspect，且 `browser_debugger_inspect` **不传** `call_frame_id`——这条恰好支持 E1 的方向），但仓库外无从得知。
6. **`src\MCP_Server.wsv:5685-5688` 那个"工具级同步预算"函数（flow=60000）的全部调用点与真实作用**：我只读到它是一个按工具名返回预算的查询函数，没有穷尽它的调用方，因此不能断言改不改它有无副作用（我的建议是**不改**）。
7. **帧 ID 的真实字符串格式**（`paused.call_frame_id` 形如 `-5823230465752015470.1.0`，见 `_audit/_tool_ledger.md:195`，但这是单一样本）→ 因此我不建议任何格式校验。
8. **`解析Debugger暂停摘要` 的 `frames` 是否覆盖全部调用帧**（当前截断为 8 条，`src\MCP_Server.wsv:2812`）→ 因此我不建议用"帧 ID 是否在 frames 里"做阻断式校验。
9. **未做的验证**：没有编译、没有运行 `voldev`、没有调用任何 MCP 工具、没有用任何一个 helper 做过真值测试。本文所有"确认"仅指**源码逐字核对**，不含运行时确认。

---

## 5. 一句话交付摘要

- **flow**：`执行Debugger断点流程JSON`（`src\MCP_Server.wsv:3822`）里三处最小改动 —— ① 在 `:3894-3897` 之后用**既有 helper** `CDP断点是否零命中 (bpRaw)` 判"零命中且未传 url"（F1 快速失败 / F1' 压到 3s）；② `:3838-3843` 默认 `45000` → `12000`（+ schema 文案 `:9664`）；③ `:3923-3926` 的超时体追加 `waited_ms`/`reason`/`hint`。三处锚点均**逐字唯一**。
- **evaluate**：`src\MCP_Server_Core.wsv:4845-4852` 换成"表达式必填 + 帧 ID 为空时复用 inspect 那段活帧逻辑"（E1），并把 `src\MCP_Server.wsv:9660` 的必填列表收敛为 `"expression"`（E2）；`-32000` 走 `src\MCP_Server.wsv:3645-3648` 修好被吞掉的失败原因并追加"帧已失效/怎么取活帧"的行动指引（E3a，零形状改动）；`parse:false` 原始路径（`:4871`）要可行动只能改形状（E3b，可选，需你裁决）。
- **不要动**：`browser_debugger_inspect`（它是可复用的样板，且台账有实测通过记录）、`browser_debugger_auto`（它的零命中策略是**有意的**，见 Core `:5070-5077`，与 F1 的取舍直接冲突，须你先裁决）。
