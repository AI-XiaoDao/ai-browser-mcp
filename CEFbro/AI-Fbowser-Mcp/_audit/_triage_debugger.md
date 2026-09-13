# 三个调试器工具失败分诊 (browser_debugger_auto / flow / evaluate)

> 只读源码分析。**未编译、未运行、未调用任何 MCP 工具、未改动任何其它文件。**
> 所有结论均带 `file:line` + 原文引用。**本文件提出的补丁均为"未验证的候选改法"**，验证由主代理另行进行。

---

## 0. 原始失败证据（逐字）

`_audit/_tool_ledger.json` 中三条记录（用 `ConvertFrom-Json` 读出，未改写）：

```
=== browser_debugger_auto ===
cls=TIMEOUT elapsed=15.02 status=fail ts=09-13 02:08 round=11
args={"breakpoint":"mcp_probe"}
note=timed out
=== browser_debugger_flow ===
cls=TIMEOUT elapsed=15.01 status=fail ts=09-13 02:07 round=10
args={"breakpoint":"mcp_probe"}
note=timed out
=== browser_debugger_evaluate ===
cls=ERR_GOOD elapsed=0.04 status=fail ts=09-13 02:57 round=56
args={"call_frame_id":"mcp_probe","expression":"1"}
note={"code":-32000,"message":"Invalid call frame id"}
```

驱动脚本 `_audit/tool_ledger.py:46` 的客户端超时是**硬编码 15 秒**：

```
TOOL_TIMEOUT = 15
```

同文件 `:43-45` 的注释已预见这一点：

```
# 每工具超时上限: 有些工具自带长超时(browser_debugger_wait_paused 会等满自身 30s,
# browser_debugger_flow 40s+), 逐功能测时会把整轮预算吃光(实测那批 76s, 其他批次仅 1–12s)。
```

**这一条决定了本任务能得出的最强事实**：`auto`/`flow` 两条记录里 `elapsed≈15.0`，即客户端在读超时处主动放弃，
服务端此刻**仍在工具内部的等待循环里**（预算 45s / 60s，见下文）。所以台账的 `timed out` 本身
**无法区分**"没建立状态 / 事件投递不到 / 预算不合理"这三者 —— 必须回源码定因。
另外注意 `browser_debugger_evaluate` 的 `elapsed=0.04`、`cls=ERR_GOOD`：它是**快速返回了一个明确错误**，
不是超时。三个工具里只有它和 `flow/auto` 的性质不同。

---

## 1. 三个工具的实现分支锚点

全部三个都在 `src/MCP_Server_Core.wsv` 的 `分类分派_核心操作` 里按名字分派：

| 工具 | 分支锚点 | 后续调用链 |
|---|---|---|
| `browser_debugger_evaluate` | `src/MCP_Server_Core.wsv:4823` | 帧 ID 直接用参数 → `执行Debugger帧求值并等待` / 原始 `Debugger.evaluateOnCallFrame` |
| `browser_debugger_flow` | `src/MCP_Server_Core.wsv:4948` | `MCP_Server.wsv:3776 执行Debugger断点流程JSON` |
| `browser_debugger_auto` | `src/MCP_Server_Core.wsv:4991` | 内联 enable → setBreakpointByUrl → 可选导航 → 循环等暂停 |

`src/MCP_Server_Core.wsv:4823`：

```
否则 (方法名 == "browser_debugger_evaluate")
```

`src/MCP_Server_Core.wsv:4948`：

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
```

`src/MCP_Server_Core.wsv:4991`：

```
否则 (方法名 == "browser_debugger_auto")
```

命令注册表映射（`src/MCP_Server.wsv:1054/1062/1066`）：

```
命令注册表.置整数值 ("browser_debugger_evaluate", 839)
命令注册表.置整数值 ("browser_debugger_flow", 844)
命令注册表.置整数值 ("browser_debugger_auto", 846)
```

**分发是同步的**：`src/MCP_Server.wsv:10495` 在请求处理路径上直接调用
`result = MCP_核心分派.分类分派_核心操作 (命令ID, 方法名, 参数JSON)`，随后 `:10527 MCP执行锁.解锁 ()`。
两者都不返回 `_async` 包装（`命令成功_原始JSON` → `构建带数据字段JSON`，不写 `_async`；
对照 `MCP_ResponseBuilders.wsv:140-147 构建异步提交JSON` 才写 `_async`）。
所以 `将异步响应转为同步` 那条外挂等待路径（`MCP_Server.wsv:6240` 要求 `_async` 为真）**对这两个工具不生效**，
它们的耗时完全由自身内部等待决定。

---

## 2. `browser_debugger_flow` 为什么会超时

### 2.1 内部预算：默认 45000ms，远超客户端 15s

`src/MCP_Server.wsv:3776` 起的流程，`:3792-3797`：

```
变量 maxMs <类型 = 整数>
maxMs = yyjson取整数 (参数JSON, "max_ms")
如果 (maxMs == 0)
{
    maxMs = 45000
}
```

唯一的等待在 `src/MCP_Server.wsv:3875-3880`：

```
变量 pausedRaw <类型 = 文本型>
pausedRaw = 等待CDP事件 ("Debugger.paused", maxMs, 假)
如果 (pausedRaw == "")
{
    返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"wait_paused\",\"error\":\"timeout\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\"}"))
}
```

`等待CDP事件` 的语义（`src/MCP_Server.wsv:2557-2597`）是**有界轮询**，不是事件回调：

```
变量 截止 <类型 = 长整数>
截止 = 取启动时间 () + 最大毫秒
判断循环 (取启动时间 () < 截止)
{
    ...
    data = 取CDP事件数据JSON (事件名)
    ...
    延时 (100)
    ...
}
返回 ("")
```

要它提前返回，**必须**有 `Debugger.paused` 落进 `cdp_event:Debugger.paused` 这个键。

### 2.2 台账那一次的参数根本不可能产生暂停 → 主因是 (a)+(c)，不是 (b)

台账参数是 `{"breakpoint":"mcp_probe"}`，`url` 未传。于是：

- `src/MCP_Server.wsv:3790-3791` 读出 `navUrl = ""`；
- `src/MCP_Server.wsv:3854` 的导航分支 `如果 (navUrl != "")` **不进入** ——
  没有任何动作去让页面执行与 `mcp_probe` 匹配的脚本；
- 断点只是"挂上去"，命中与否取决于当前已加载页面里有没有 URL 含 `mcp_probe` 的脚本。

而且**断点没匹配到任何位置时，代码仍当成成功**。`src/MCP_Server.wsv:3846-3851`：

```
变量 bpRaw <类型 = 文本型>
bpRaw = 执行CDP并同步等待 (命令ID + "_bp", "Debugger.setBreakpointByUrl", bpParams.到可读文本 (YYJSON格式化选项.压缩), 20000)
如果 (CDP设置断点结果是否成功 (bpRaw) == 假)
{
    返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",\"error\":\"" + ... + "\"}"))
}
```

`CDP设置断点结果是否成功`（`src/MCP_Server.wsv:3571-3581`）**只看 success 标志和 "already exists"，完全不看 `locations`**：

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

全仓库对 `locations` 的引用只有三处，且都在别处（`src/MCP_Server_Core.wsv:4715` 只是注释，`src/MCP_Server_Reverse.wsv:1467/1469` 属 `getPossibleBreakpoints`）：
我 grep `locations|actualLocation` 得到的命中里**没有任何一处用它判定 `setBreakpointByUrl` 是否真的挂到了位置**。

✅ 结论：**`Debugger.setBreakpointByUrl` 在 `locations: []` 时返回成功，代码当成"断点已就绪"，
然后死等 45000ms 等一个不可能发生的 `Debugger.paused`。** 这就是 (a) 未建立它所要等的状态，
再叠加 (c) 预算（45s）远超客户端耐心（15s）。

### 2.3 (b) 可以被代码证据排除

观察者通道是完整的（见 §5）：事件确实会被写进 `cdp_event:Debugger.paused`。
并且仓库里**同一个 `等待CDP事件` 原语在别处是被当成可用手段使用的** ——
`src/MCP_Server.wsv:1701-1707`（`确保调试器已暂停` 内部）：

```
变量 已暂停 <类型 = 文本型>
已暂停 = 等待CDP事件 ("Debugger.paused", 6000, 假)
如果 (已暂停 != "")
{
    MCP_响应构建.记录自动处理 ("Debugger.pause(页面原本未暂停, 已自动启用调试器域并安排执行点制造暂停点; 用完请 browser_debugger_resume 恢复页面)")
    返回 (真)
}
```

`确保调试器已暂停` 被 6 个工具当"零前置"入口用（`src/MCP_Server_Core.wsv:4797/4889/4906/4977/4629/4637/4645`）。
若 `等待CDP事件` 收不到 `Debugger.paused`，这条链会全线崩塌并留下"页面未处于暂停状态"的连锁失败 ——
而台账里 `browser_debugger_resume` 的失败文本恰恰是
`页面未处于暂停状态, 无需恢复 | 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused`
（`_audit/_ledger_status.txt`），说明它看到的确实**不是**暂停态，与"断点从未命中"一致，
而不是"命中了但事件投递不到"。

⚠️ 我**只**能说"投递通道在源码上完整"，**不能**断言运行时一定投递成功（见 §9）。

### 2.4 一处**次要**竞态：把刚到的命中自己删掉

`src/MCP_Server.wsv:3852-3853`：

```
// 须在 navigate 之前清除,否则加载时命中断点的事件会被误删
清除CDP事件记录 ("Debugger.paused")
```

注释只考虑了"有导航"的情形。当 `navUrl == ""` 且页面**本就在跑匹配脚本**时，
`setBreakpointByUrl` 之后、`:3853` 清除之前，命中可能已经落地 → 被这行删掉；
而渲染进程此刻**是真的暂停了**，同一个暂停不会再触发第二次 → `等待CDP事件` 依然死等到 45s，
最后报 `step=wait_paused, error=timeout`（**假阴性**：断点其实命中了）。

`清除CDP事件记录`（`src/MCP_Server.wsv:3012-3031`）是**显式清除**，不是 TTL：

```
删除异步结果 ("cdp_event:" + 事件名)
```

而 TTL 层面并不会在单次调用内让事件消失 —— `src/MCP_Constants.wsv:47`：

```
常量 异步结果非等待保留毫秒 <公开 类型 = 整数 值 = 86400000 注释 = "24小时" @输出名 = "AsyncResultNotWaitRetainMs">
```

`src/MCP_Constants.wsv:13`：

```
常量 缓存最大条目 <公开 类型 = 整数 值 = 50000 @输出名 = "CacheMaxEntry">
```

即：单次调用窗口内**只有显式清除**会删事件（`Debugger.resumed` 到达时的清除见 `src/MCP_Server.wsv:2421-2425`）。
所以这个竞态是真实存在且可由代码定位的，但它是**次要**成因（窗口很小），不是台账那次超时的解释。

### 2.5 失败时**没有**调用解卡自救

已修的那个自救只在 `执行CDP并同步等待` 里（`src/MCP_Server.wsv:3096-3118`）：

```
否则 (cdp错误 == "timeout")
{
    // ── 卡死自救: 页面停在断点上而无人 resume, 会让**之后每一个**工具都超时 ──
    ...
    如果 (取CDP事件数据JSON ("Debugger.paused") != "")
    {
        执行CDP命令_带参数 (命令ID + "_rsq", "Debugger.resume", "{}")
        ...
    }
}
```

`browser_debugger_flow` 的主等待 `:3876` 用的是 `等待CDP事件`，**不经过**这个自救。
flow 自己的兜底是失败返回里的 `DebuggerFlow失败返回`（`src/MCP_Server.wsv:2650-2656` → `:2632-2648 DebuggerFlow尝试Resume`）——
**这条兜底存在**，所以"渲染进程永久冻结"的风险已被覆盖，但**延迟**（dead wait）没被覆盖。

---

## 3. `browser_debugger_auto` 为什么会超时

### 3.1 预算更糟：默认 60000ms **每一次命中**，最多 5 次 → 最长 300000ms

`src/MCP_Server_Core.wsv:5015-5020`：

```
变量 autoMaxMs <类型 = 整数>
autoMaxMs = MCP命令服务器.yyjson取整数 (参数JSON, "max_ms")
如果 (autoMaxMs == 0)
{
    autoMaxMs = 60000
}
```

循环里唯一的等待，`src/MCP_Server_Core.wsv:5069-5081`：

```
判断循环 (autoHits < autoMaxHits)
{
    如果 (MCP命令服务器.MCP正在关闭 || MCP_编排分派.工作流应停止)
    {
        跳出循环
    }
    MCP命令服务器.清除CDP事件记录 ("Debugger.paused")
    变量 autoPausedRaw <类型 = 文本型>
    autoPausedRaw = MCP命令服务器.等待CDP事件 ("Debugger.paused", autoMaxMs, 假)
    如果 (autoPausedRaw == "")
    {
        跳出循环
    }
```

以及 schema 自己声明的默认（`src/MCP_Server.wsv:9620`）：

```
添加工具JSON ("browser_debugger_auto", "自动断点求值(VIP): 断点命中→自动执行JS→resume→循环, max_hits次后自动停止", 多属性Schema文本 (... 属性项JSON ("max_hits", "integer", "最大命中次数(默认5,最大100)") + "," + 属性项JSON ("max_ms", "integer", "每次等待超时ms(默认60000)"), "\"breakpoint\""))
```

台账参数 `{"breakpoint":"mcp_probe"}` 未传 `max_ms`/`max_hits` → 生效值就是 60000ms 单次等待、5 次上限。
**第 15 秒客户端就放弃了**，而服务端还在第一次 `等待CDP事件` 里。

### 3.2 与 flow 同一个 (a)：断点可以匹配 0 个位置却是"成功"

`src/MCP_Server_Core.wsv:5040-5045`：

```
变量 autoBpRaw <类型 = 文本型>
autoBpRaw = MCP命令服务器.执行CDP并同步等待 (命令ID + "_bp", "Debugger.setBreakpointByUrl", autoBpParams.到可读文本 (YYJSON格式化选项.压缩), 15000)
如果 (MCP命令服务器.CDP设置断点结果是否成功 (autoBpRaw) == 假)
{
    返回 (MCP_响应构建.命令失败 (命令ID, "断点设置失败: " + MCP命令服务器.取CDP同步结果错误 (autoBpRaw)))
}
```

同样走 §2.2 那个只看 success 的判定。
并且 `url` 也是可选的（`:5047 如果 (autoNavUrl != "")`），台账没传 → 没有任何触发动作。

### 3.3 关键差异：auto 在**零命中**时返回的是 `success:true`

`src/MCP_Server_Core.wsv:5111-5118`：

```
MCP命令服务器.确保Debugger已恢复 (命令ID + "_done")
变量 auto汇总 <类型 = YYJSON对象类>
auto汇总.创建自文本 ("{}")
auto汇总.加入逻辑值成员 ("success", 真)
auto汇总.加入整数成员 ("hits", autoHits)
auto汇总.加入文本成员 ("breakpoint", autoBpUrl)
auto汇总.加入文本成员 ("results", MCP_编排分派.步骤JSON片段列表到数组文本 (autoResults))
返回 (MCP_响应构建.命令成功_原始JSON (命令ID, auto汇总.到可读文本 (YYJSON格式化选项.压缩)))
```

超时路径是 `:5078-5081` 的 `跳出循环`（**不是** `返回 失败`），然后落到上面这段无条件 `success=真`。
于是：

- 客户端等到 15s → 台账记 `timed out`；
- 客户端若肯等满 60s → 拿到 **`success:true, hits:0`** —— 一个**假成功**。

对比 flow：flow 在同样情形下返回 `ok:false, step:"wait_paused", error:"timeout"`（`src/MCP_Server.wsv:3879`）——
**flow 是诚实的，auto 不是**。这是两个工具最本质的区别，也是 auto 的补丁重点。

### 3.4 auto 也有一处**次要**竞态，且窗口比 flow 更常出现

`:5075 清除CDP事件记录 ("Debugger.paused")` 紧贴 `:5077 等待CDP事件(..., 假)`；
上一轮迭代在 `:5102 MCP命令服务器.DebuggerFlow尝试Resume (...)` 之后立刻回到 `:5075`。
若热行断点在 resume 后**立刻**再次命中，事件可能落在"resume → 清除"之间被删掉 → 白等 60s。

同时 `:5096-5109` 的顺序值得注意：

```
变量 autoEvalOut <类型 = 文本型>
autoEvalOut = "[]"
如果 (autoFrameId != "")
{
    autoEvalOut = MCP命令服务器.Debugger帧内批量求值JSON (命令ID + "_ah" + 到文本 (autoHits), autoFrameId, autoExprRaw, 真, 真)
}
MCP命令服务器.DebuggerFlow尝试Resume (命令ID + "_ar" + 到文本 (autoHits))
...
autoHitResult.加入文本成员 ("frame_id", autoFrameId)
```

**先 resume（:5102）再记录 `frame_id`（:5106）** —— 详见 §4.3，这直接制造了给 `browser_debugger_evaluate` 用的**已失效帧 ID**。

---

## 4. `browser_debugger_evaluate`：帧 ID 从哪来、为什么无效

### 4.1 完整调用路径（`src/MCP_Server_Core.wsv:4823-4852`）

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
        ...
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

**帧 ID 的唯一来源是调用方参数 `call_frame_id`（`:4825-4826`）**，
非空即被逐字塞进 `callFrameId`（`:4845`），没有任何合法性校验，
也没有像同族工具那样回落到"当前暂停点"。

### 4.2 台账那一次：不是"stale"，也不是"empty"，是**调用方给的占位串**

台账 args 逐字是 `{"call_frame_id":"mcp_probe","expression":"1"}` —— 探针填的占位值。
`frameId != ""` 通过了 `:4829` 的守卫，`parse` 未传（默认假）→ 走 `:4843-4851` 原始路径 →
CDP 返回 `{"code":-32000,"message":"Invalid call frame id"}`，被 `处理CDP响应`（`src/MCP_Server.wsv:2205-2211`）
原样放进 `error` 字段：

```
否则
{
    如果 (结果文本 != "")
    {
        结果对象.加入文本成员 ("error", 结果文本)
    }
}
```

`_audit/MCP工具可用性检测报告.md:6270` 也早已把这条判为"需编排"：

```
其中 `browser_debugger_evaluate` 的 `-32000 Invalid call frame id` 属"需编排"(探针给的是占位帧ID),
```

所以**台账这条的直接成因是测试侧占位值**；但工具侧"照抄不校验、错误不翻译"使这条失败**不可行动**。

### 4.3 但确实存在真实的"stale 帧"来源 —— 而且都是本仓库自己造出来的

**(1) `browser_debugger_flow` 默认 `resume:true`，返回的 `paused.call_frame_id` 在 resume 后即失效。**

`src/MCP_Server.wsv:2994-2995`：

```
// 统一走 yyjson取逻辑_默认: 布尔/数值/文本三种表示都能正确识别, 缺键回默认真。
返回 (yyjson取逻辑_默认 (参数JSON, "resume", 真))
```

`src/MCP_Server.wsv:3905-3915`：

```
evalOut = Debugger帧内批量求值JSON (命令ID, frameId, exprRaw, flowExpand, flowRbV)
变量 resumed <类型 = 逻辑型 值 = 假>
如果 (应Resume)
{
    resumed = DebuggerFlow尝试Resume (命令ID + "_done")
}
...
返回 ("{\"ok\":true,\"breakpoint\":\"" + ... + "\",\"url\":\"" + ... + "\",\"paused\":" + pausedSummary + ",\"evaluations\":" + evalOut + ",\"resumed\":" + 选择 (resumed, "true", "false") + "}")
```

`pausedSummary` 里含 `call_frame_id`（`src/MCP_Server.wsv:2554` 的返回体有
`\"call_frame_id\":\"...\"`）。调用方拿它去 `evaluate` → 页面已 resume → **必然 `Invalid call frame id`**。
即：**"先 flow 再 evaluate"这个最自然的两步用法，在默认参数下就是一条注定失败的路。**

**(2) `browser_debugger_auto` 输出的 `frame_id` 是"构造上已失效"的**（见 §3.4）：先 resume 后记录。

**(3) `执行CDP并同步等待` 的卡死自救会在调用方不知情的情况下 resume 并抹掉暂停事件**：

`src/MCP_Server.wsv:3105-3107`：

```
执行CDP命令_带参数 (命令ID + "_rsq", "Debugger.resume", "{}")
同步等待异步任务 (命令ID + "_rsq", 5000)
清除CDP事件记录 ("Debugger.paused")
```

没有任何机制回溯性地作废此前已经交出去的帧 ID（本来也不可能），
所以**没有任何工具能在事后判断"我拿到的这个帧 ID 是哪一次暂停的"**。

**(4) 同族工具都做了"从当前暂停点自动取帧"，只有 evaluate 没做。**
`src/MCP_Server_Core.wsv:4902-4926`（`browser_debugger_inspect`）：

```
变量 frameId2 <类型 = 文本型>
frameId2 = MCP命令服务器.yyjson取文本 (参数JSON, "call_frame_id")
如果 (frameId2 == "")
{
    // 零前置: 未给帧ID 且页面未暂停时, 先自动制造暂停点(已暂停则立即返回真)
    如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)
    {
        返回 (MCP_响应构建.命令失败 (命令ID, "无法自动制造暂停点(已安排执行点 + Debugger.pause 并等待5秒仍未收到 Debugger.paused) | ..."))
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
```

结论：`evaluate` 的帧 ID 问题**不是**"空"，而是三件事叠在一起 ——
**(i) 调用方给的占位/猜测值被照抄（台账情形）；(ii) 框架自己交出去的帧 ID 在 resume 后即失效（flow/auto/自救）；**
**(iii) 工具既不自取活帧，也不把 `-32000` 翻译成可行动的说明。**

---

## 5. 观察者通道能否投递 `Debugger.paused`？(用于排除 (b))

写侧 —— `src/MCP_Callbacks.wsv:524-543`（`类_MCP_DevTools观察者` = `类_FBrowser_开发者消息事件`，`:495`）：

```
方法 开发者消息_VIP_收到事件 <公开 @虚拟方法 = 可覆盖>
参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
参数 方法名 <类型 = 文本型 @输出名 = "MethodName">
参数 参数指针 <类型 = 变整数 @输出名 = "ParamPtr">
参数 参数大小 <类型 = 整数 @输出名 = "ParamSize">
{
    // CDP事件(如Debugger.paused, Network.requestWillBeSent)也存入缓存
    // 事件键名为 \"cdp_event:方法名\"
    ...
    MCP命令服务器.存储CDPDevTools事件 (方法名, 事件文本)
}
```

落库 —— `src/MCP_Server.wsv:2231-2232`：

```
// 缓存存裸 params,避免 wrapper.message 二次解析失败
存储异步结果 ("cdp_event:" + 事件方法名, 参数字段)
```

读侧 —— `src/MCP_Server.wsv:2434-2439`：

```
变量 cache <类型 = 文本型>
cache = 查询任务结果 ("cdp_event:" + 事件名)
如果 (cache != "")
{
    返回 (解包CDPDevTools事件JSON (cache))
}
```

`resume` 会清缓存 —— `src/MCP_Server.wsv:2421-2425`：

```
// resume后立即清除paused事件缓存: 防 debugger 快速失败检查误判"仍在暂停"
如果 (事件Method == "Debugger.resumed")
{
    清除CDP事件记录 ("Debugger.paused")
}
```

观察者是**懒注册**的，且在申请失败时会明确失败而不是静默 —— `src/MCP_Server.wsv:1593-1612`（节选）：

```
如果 (CDP观察者已注册 == 假)
{
    持久CDP观察者.创建 (类_MCP_DevTools观察者)
    变量 重注册结果 <类型 = 逻辑型>
    重注册结果 = vip_ctrl.开发者消息_启用监管者事件 (持久CDP观察者)
    ...
```

并且未在册时会**快速失败**（`src/MCP_Server.wsv:1619-1622`）：

```
如果 (CDP观察者已注册 == 假)
{
    返回 (MCP_响应构建.命令失败 (命令ID, "CDP 通道不可用: DevTools观察者未在册 | 该类 CDP 工具(debugger_*/cdp_*/reverse CDP类)将全部失效 | ..."))
}
```

→ 若观察者没在册，失败文本会是上面这句，而台账里 flow/auto **不是**这句。
所以 §2.3 的判据成立：**通道层面看不出"投递不到"的证据，主因不在 (b)。**

---

## 6. 变更清单（候选补丁；**未验证**）

约定：行号是**当前**文件状态；补丁会使后续行号平移，故同时给出可搜锚点。
所有 `after` 都尽量**复用既有 helper**（`取CDP同步结果体文本` / `确保调试器已暂停` / `解析Debugger暂停摘要` / `执行Debugger帧求值并等待` / `解析Debugger求值结果`）。

### C1 — `flow`：断点匹配 0 位置且无导航时，立即失败而不是死等 45s

- 锚点：`src/MCP_Server.wsv:3846-3851`（在 `CDP设置断点结果是否成功` 判定**之后**插入）
- 依据：§2.2（`CDP设置断点结果是否成功` 不看 `locations`；台账无 `url`、`breakpoint="mcp_probe"` 不可能命中；`maxMs` 默认 45000）
- 复用：`取CDP同步结果体文本`（`src/MCP_Server.wsv:3918-3931`）已能取出 CDP `result` 体，无需新解析器

**before**
```
bpRaw = 执行CDP并同步等待 (命令ID + "_bp", "Debugger.setBreakpointByUrl", bpParams.到可读文本 (YYJSON格式化选项.压缩), 20000)
如果 (CDP设置断点结果是否成功 (bpRaw) == 假)
{
    返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",...}"))
}
```

**after**
```
bpRaw = 执行CDP并同步等待 (命令ID + "_bp", "Debugger.setBreakpointByUrl", bpParams.到可读文本 (YYJSON格式化选项.压缩), 20000)
如果 (CDP设置断点结果是否成功 (bpRaw) == 假)
{
    返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",...}"))
}
// 新增: 断点是否真的落在了某个位置? locations 为空 == 该 URL 正则与"当前已加载脚本"无一匹配。
// 没有 url 参数时不导航 => 不会再加载新脚本 => 这次等待注定白等到 maxMs(默认45s)。
变量 bpBody <类型 = YYJSON只读对象类>
变量 bpLocN <类型 = 整数 值 = 0>
如果 (bpBody.创建自文本 (取CDP同步结果体文本 (bpRaw)))
{
    变量 bpLocs <类型 = YYJSON只读数组类>
    bpLocs = bpBody.取数组 ("locations")
    如果 (bpLocs.是否为空对象 () == 假)
    {
        bpLocN = (整数)bpLocs.取成员数 ()
    }
}
如果 (bpLocN == 0 && navUrl == "")
{
    返回 (DebuggerFlow失败返回 (命令ID, "{\"ok\":false,\"step\":\"set_breakpoint\",\"error\":\"no_location_matched\",\"breakpoint\":\"" + MCP_响应构建.JSON转义文本 (bpRegex) + "\",\"hint\":\"该 URL 正则与当前页面已加载脚本无一匹配, 且未传 url 触发导航, 故不会再产生断点命中 | 传 url 触发加载, 或先用 browser_reverse_search_script 定位真实脚本 URL\"}"))
}
```

- 取舍：`navUrl != ""` 时**不**拦截（新脚本尚未加载，0 位置是正常中间态）。
  `navUrl == ""` 理论上仍可能靠后续动态脚本命中，所以严格说是"极可能无效"而非"必然无效"——
  把它做成**快速失败 + 可行动提示**，比让它白等 45s 更诚实；若主代理偏好保守，
  降级版本是：不失败，但把 `bpLocN` 放进 `ok:true` 的返回体里，并在 `bpLocN==0 && navUrl==""` 时把 `maxMs` 压到 ~3000。

### C2 — `flow`：默认等待预算压到客户端耐心之内

- 锚点：`src/MCP_Server.wsv:3792-3797`
- 依据：§0（台账 15s 放弃）+ §2.1（内部 45000）

**before**
```
如果 (maxMs == 0)
{
    maxMs = 45000
}
```
**after**
```
如果 (maxMs == 0)
{
    maxMs = 12000   // 默认必须 < 常见 MCP 客户端超时; 需要更久请显式传 max_ms
}
```

- 取舍：**这不让命中变可能**，只是把"客户端超时（看不到任何原因）"换成"服务端诚实超时（`ok:false step=wait_paused error=timeout`）"。
  它是 C1 的补充，不是替代品 —— 只做 C2 会把 45s 的沉默变成 12s 的沉默。

### C3 — `auto`：零命中不允许返回 `success:true`

- 锚点：`src/MCP_Server_Core.wsv:5076-5081` 与 `:5111-5118`
- 依据：§3.3（超时只 `跳出循环`，随后无条件 `success=真`）

**before**
```
autoPausedRaw = MCP命令服务器.等待CDP事件 ("Debugger.paused", autoMaxMs, 假)
如果 (autoPausedRaw == "")
{
    跳出循环
}
```
**after**（只改"一次都没命中"这一情形）
```
autoPausedRaw = MCP命令服务器.等待CDP事件 ("Debugger.paused", autoMaxMs, 假)
如果 (autoPausedRaw == "")
{
    如果 (autoHits == 0)
    {
        返回 (MCP_响应构建.命令失败 (命令ID, "断点从未命中(" + 到文本 (autoMaxMs) + "ms) | breakpoint=" + autoBpUrl + " | 可能原因: ①该 URL 正则与当前已加载脚本不匹配 ②未传 url 且页面不会再执行该脚本 ③Debugger 域未生效 | 建议: 传 url 触发导航, 或先用 browser_reverse_search_script / browser_debugger_set_breakpoint 确认断点位置能落地"))
    }
    跳出循环
}
```

- 取舍：`autoHits > 0` 之后的中途超时应保持"正常结束"语义（已拿到 N 次结果），故不改成失败。

### C4 — `auto`：断点 0 位置且无导航时快速失败

- 锚点：`src/MCP_Server_Core.wsv:5040-5045`
- 依据：§3.2（与 flow 同一个 `CDP设置断点结果是否成功` 缺陷）
- 写法与 C1 同构（用 `执行CDP并同步等待` 的返回值 + `取CDP同步结果体文本` + `取数组("locations")`）。
- 与 C3 的关系：C4 解决"连断点都没挂上"，C3 解决"挂上了但不会命中"；两者都只针对 `autoNavUrl == ""`，互不覆盖。

### C5 — `auto`：默认 `max_ms` 压到客户端耐心之内

- 锚点：`src/MCP_Server_Core.wsv:5015-5020`（默认 60000）+ schema 描述 `src/MCP_Server.wsv:9620`
- 依据：§3.1

**before** → **after**
```
如果 (autoMaxMs == 0)          |   如果 (autoMaxMs == 0)
{                              |   {
    autoMaxMs = 60000          |       autoMaxMs = 12000
}                              |   }
```
并同步把 `src/MCP_Server.wsv:9620` 的 `"每次等待超时ms(默认60000)"` 改成新值（描述与实现必须一致）。

- 取舍：同 C2 —— 降低的是"沉默时长"，不是"失败概率"。`max_hits=5` 的最坏总时长随之从 300s 降到 60s，仍可能超过 15s，故 C3 才是关键。

### C6 — `evaluate`：缺帧 ID 时复用 `inspect` 的自取帧逻辑

- 锚点：`src/MCP_Server_Core.wsv:4829-4832`
- 依据：§4.3(4)
- 复用：把 `src/MCP_Server_Core.wsv:4903-4922` 那段整块搬过来（`确保调试器已暂停` → `取CDP事件数据JSON("Debugger.paused")` → `解析Debugger暂停摘要` → 读 `call_frame_id`）

**before**
```
如果 (frameId == "" || expr == "")
{
    返回 (MCP_响应构建.命令失败 (命令ID, "call_frame_id和expression " + MCP_常量.错误_缺少参数))
}
```
**after**
```
如果 (expr == "")
{
    返回 (MCP_响应构建.命令失败 (命令ID, "expression " + MCP_常量.错误_缺少参数))
}
如果 (frameId == "")
{
    // 与 browser_debugger_inspect 同源: 未给帧ID 时从当前暂停点自动取帧(已暂停则直接复用)
    如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)
    {
        返回 (MCP_响应构建.命令失败 (命令ID, "未给 call_frame_id 且无法自动制造暂停点 | 请先 browser_debugger_wait_paused / browser_debugger_last_paused 取帧, 或用 browser_debugger_inspect"))
    }
    变量 evPauseRaw <类型 = 文本型>
    evPauseRaw = MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")
    如果 (evPauseRaw != "")
    {
        变量 evPauseSum <类型 = 文本型>
        evPauseSum = MCP命令服务器.解析Debugger暂停摘要 (evPauseRaw)
        变量 evPauseObj <类型 = YYJSON只读对象类>
        如果 (evPauseObj.创建自文本 (evPauseSum))
        {
            frameId = MCP命令服务器.yyjson取文本 (evPauseObj, "call_frame_id")
        }
    }
}
如果 (frameId == "")
{
    返回 (MCP_响应构建.命令失败 (命令ID, "缺少 call_frame_id | 请先 browser_debugger_wait_paused 或 browser_debugger_last_paused"))
}
```

- 说明：**这不会**修好台账那条 `call_frame_id:"mcp_probe"`（非空垃圾值仍会照抄），但它是零风险的一步，
  且让 `evaluate` 与 `inspect/stack` 的"零前置"承诺对齐。

### C7 — `evaluate`：把 `-32000 Invalid call frame id` 变成可行动错误（而不是硬修）

- 锚点：`src/MCP_Server_Core.wsv:4843-4851`（`parse` 为假时的原始路径）
- 依据：§4.2（错误被原样透传，调用方无从得知"帧 ID 从哪来、为什么会失效"）
- **我倾向这一条就是"把失败做得可行动"而非"让它成功"的典型**（见 §7）。
  最小做法：非 parse 路径改走既有 `执行Debugger帧求值并等待` + `解析Debugger求值结果`，
  失败时把 `error` 文本翻译成带出处的说明；**保留** `returnByValue` 语义，`展开对象` 传假以贴近原原始路径的行为。

**before**
```
返回 (MCP命令服务器.执行CDP命令_带参数 (命令ID, "Debugger.evaluateOnCallFrame", evParams.到可读文本 (YYJSON格式化选项.压缩)))
```
**after（示意；沿用 parse 分支已有的两个 helper，文案待主代理定）**
```
// 与 :4839-4841 的 parse 分支同源: 用 执行Debugger帧求值并等待 拿回可判读的结果
变量 evRbV <类型 = 逻辑型>
evRbV = MCP命令服务器.取Debugger求值ReturnByValue (参数JSON)
变量 evRaw <类型 = 文本型>
evRaw = MCP命令服务器.执行Debugger帧求值并等待 (命令ID, frameId, expr, 12000, evRbV)
// 展开传假, 以贴近原原始路径(不做属性展开)的语义
变量 evParsed <类型 = 文本型>
evParsed = MCP命令服务器.解析Debugger求值结果 (evRaw, 命令ID, frameId, expr, 假)
变量 evObj <类型 = YYJSON只读对象类>
如果 (evObj.创建自文本 (evParsed) && evObj.取逻辑值 ("ok") == 假)
{
    变量 evErr <类型 = 文本型>
    evErr = MCP命令服务器.yyjson取文本 (evObj, "error")
    返回 (MCP_响应构建.命令失败 (命令ID, "帧内求值失败(原始错误: " + evErr + ") | call_frame_id 与暂停点绑定, 页面 resume 后立即失效 —— flow/auto 默认 resume:true, 其返回的 paused.call_frame_id / results[].frame_id 在返回时已失效 | 取活帧: browser_debugger_wait_paused 或 browser_debugger_last_paused, 拿到后立即 evaluate"))
}
返回 (MCP_响应构建.命令成功_原始JSON (命令ID, evParsed))
```
（`取逻辑值`/`yyjson取文本` 的可用性见 `src/MCP_Server.wsv:4489-4501`、`:3170` 等既有用法；
`解析Debugger求值结果` 的 `ok:false` 分支见 `src/MCP_Server.wsv:3590-3613`。）

- ⚠️ 风险：这会改变该路径的**响应形状**（原本是 `执行CDP命令_带参数` 的异步包装）。
  但这只影响 `parse:false` 的调用方，且 `_audit/检测报告-第二轮.md:63-65` 已记录该路径本身就"忽略 parse/expand"，
  形状并不稳定可靠。**如果主代理想零形状改动**，替代方案是在 `evParams` 组装前加一道**校验**：
  拒绝不含 `{` 的 `call_frame_id`（下发给调用方"如何取得"的说明），但这依赖帧 ID 的实际格式，
  我无法静态确证（见 §9 与 §10 的开放问题），故**不推荐**。

### C8 — 文档层：把"帧 ID 会失效"写进 schema 描述（纯文案，零逻辑风险）

- 锚点：`src/MCP_Server.wsv:9614`（`browser_debugger_evaluate` 的 `call_frame_id` 描述"帧ID"）
- 依据：§4.3(1)(2)

**before**
```
属性项JSON ("call_frame_id", "text", "帧ID")
```
**after**
```
属性项JSON ("call_frame_id", "text", "帧ID(形如 wait_paused/last_paused 返回的 paused.call_frame_id); 与暂停点绑定, 页面 resume 后即失效 —— flow/auto 默认 resume:true, 其返回的帧在返回时已失效")
```

### C9（可选，不建议与上面捆绑）— 去掉 `auto` 循环内的"删除刚到的命中"

- 锚点：`src/MCP_Server_Core.wsv:5075`
- 依据：§3.4
- 改动：只在 `autoHits == 0` 时清除，或改为依赖 `Debugger.resumed` 触发的清除（`src/MCP_Server.wsv:2421-2425`）。
- **风险**：若 `Debugger.resumed` 丢失，会重复读到同一个暂停事件、重复计数、并用旧帧 ID 求值（正好触发 `-32000`）。
  **它不是根因**，修它需要"等 `Debugger.resumed`"的新逻辑 —— 与"最小改动 + 复用既有 helper"的要求冲突，故列而不推。

---

## 7. 哪些地方"诚实的修法是让失败可行动，而不是让它成功"

1. **`auto` 零命中返回 `success:true, hits:0`（§3.3）** —— 这不是超时问题，是**谎报**。
   正确修法是 C3（诚实失败），不是"想办法让它命中"。
2. **`evaluate` 的 `-32000`（§4.2）** —— 帧 ID 是 CDP 的不透明句柄，工具**无法**"修好"一个调用方编造的帧 ID。
   正确修法是 C7（说明帧 ID 从哪来、何时失效）+ C8（把失效条件写进 schema），而不是猜格式做校验。
3. **C1/C4 的 0 位置断点** —— 无可命中的断点不可能"等出来"（`url` 缺失时尤其）。
   正确修法是立刻把事实（`locations: []` + 没传 `url`）作为错误返回，而不是延长或缩短等待。
4. **C2/C5 的预算** —— 承认 45s/60s 的默认值本身就是缺陷：工具无法保证在客户端耐心内返回，
   就不该承诺那么长的等待。**但压低预算只提升可诊断性，不提升成功率** —— 不要把它当成"修好了"。

---

## 8. 三条根因结论（含置信度）

| 工具 | 根因分类 | 一句话结论 | 置信度 |
|---|---|---|---|
| `browser_debugger_flow` | **(a) 主 + (c) 叠加**；(b) 已由代码证据排除 | 断点可以匹配 0 个位置却判为"设置成功"（`CDP设置断点结果是否成功` 不看 `locations`），未传 `url` 时又无任何触发动作，于是死等默认 45000ms（`MCP_Server.wsv:3792-3797`、`:3875-3880`），客户端 15s 就放弃 → `timed out`。失败语义本身是诚实的（`ok:false, step:"wait_paused"`）。 | 高（对台账那组参数：断点不可能命中——证据是参数+无 url 分支） |
| `browser_debugger_auto` | **(a) + (c)，另加"假成功"** | 与 flow 同一 0 位置问题，且默认单次等待 60000ms×最多 5 次；更严重的是零命中时只 `跳出循环`，最终无条件返回 `success:true, hits:0` —— 客户端等满就会拿到**假成功**。 | 高（假成功路径 `:5078-5081` + `:5111-5118` 是逐行可读的） |
| `browser_debugger_evaluate` | **(调用方占位值）→ 无校验 + 无自动取活帧 + 错误不可行动** | 帧 ID 只来自参数（`:4825-4826`），非空即透传（`:4845`）。台账传的是占位串 `"mcp_probe"`，故 CDP 回 `-32000`。且框架自身会交出**已失效帧**：flow 默认 `resume:true` 却在返回体里带 `paused.call_frame_id`（`MCP_Server.wsv:2995`、`:3909-3915`），auto 先 resume 再记录 `frame_id`（`MCP_Server_Core.wsv:5102` vs `:5106`）。 | 高（帧 ID 来源唯一、无校验，代码只有一条路径）；对"台账那条属测试侧占位值"为**高**（args 逐字可见），对"其它调用方遇到的是 stale"为**中**（机制存在，但本次台账未复现） |

补充：**已修的那个卡死自救（`src/MCP_Server.wsv:3096-3118`）只覆盖 `执行CDP并同步等待`，
不覆盖 flow 的主等待 `等待CDP事件`（`:3876`）、`wait_paused`（`MCP_Server_Core.wsv:4868`）、
以及 `确保调试器已暂停` 的内层等待（`MCP_Server.wsv:1702`）。** 这条不对称值得记录，
但 flow/auto 各自的失败路径**确实**调用了 `DebuggerFlow尝试Resume`（`MCP_Server.wsv:3879`→`:2650-2656` / `MCP_Server_Core.wsv:5111`），
所以"渲染进程永久冻结"这一最坏情形已被兜住；未被兜住的是**沉默延迟**。

---

## 9. 静态阅读**无法**确定的（明确列出，不含猜测）

1. **`Debugger.paused` 在运行时是否真的会被投递到 `cdp_event:Debugger.paused`。**
   我只证明了写侧（`MCP_Callbacks.wsv:543`）与读侧（`MCP_Server.wsv:2435`）在源码上闭合，
   且观察者未在册时会有**另一句**不同的失败文本（`MCP_Server.wsv:1619-1622`）而台账里没有这句。
   我没有、也不能验证某一次真实暂停是否触发了 `开发者消息_VIP_收到事件`。
2. **台账那两轮（round 10/11）运行时页面上到底加载了什么。**
   `_audit/_cold_matrix.json` 的 `build_args` 只补必填项，`url` 未被传入；
   当前页面是上一轮留下的什么，静态读不出来。因此我只能说"`mcp_probe` 这个正则**几乎不可能**匹配任何真实脚本 URL"，
   而**不能**断言"该轮页面上确实没有匹配脚本"。
3. **`setBreakpointByUrl` 在本 CEF/V8 构建上返回的 `locations` 字段名与结构**（我是按 CDP 规范推断 `locations` 数组）。
   `src/MCP_Server_Core.wsv:4715` 的注释提到"含breakpointId/locations"，与我的推断一致，但这只是注释，不是运行证据。
4. **CDP `callFrameId` 的实际字符串格式。** 这直接决定了 C7 的替代方案（格式校验）是否可行；
   我因此**不建议**做格式校验。
5. **服务端在客户端 15s 断开后是否继续执行完了 `等待CDP事件`。**
   台账 `tool_ledger.py:126-129` 的注释说"客户端超时后不做探针"，因为服务端自身超时更长、
   仍持协议锁；这**暗示**（但不证明）服务端还在等。
6. **`flow`/`auto` 在真实断点命中时是否端到端可用。**
   仓库里已有 `_audit/verify_debugger_realflow.py`（用 `data:` URL 造带脚本的页面、`breakpoint:".*"`），
   但我在 `_audit/` 下**找不到它的输出记录**（grep `verify_debugger_realflow|用例 B` 只命中脚本自身），
   所以它的结论我无法引用。

## 10. 活体实验需要测什么（给主代理的测量清单）

> 均为**测量项**，不是结论。以 `_audit/tool_ledger.py` 的 15s 为对照，建议同时用 ≥90s 的超时跑一组，
> 才能把"沉默"与"失败"分开。

1. **0 位置断点的返回值**：`browser_debugger_set_breakpoint {url:"mcp_probe_never_matches", line:0}` →
   读回原始 CDP 结果体，确认 `locations` 是否为 `[]` 且 `success:true`。这直接验证 §2.2/C1 的前提。
2. **`flow` 的失败必须多快返回**：`browser_debugger_flow {breakpoint:"mcp_probe"}`（不传 url），
   客户端超时设 90s → 记录是否在 ~45s 返回 `ok:false, step:"wait_paused", error:"timeout"`。
   这验证"沉默 45s 后诚实报错"（现状）而不是"挂死"。
3. **命中路径是否真能通**：按 `verify_debugger_realflow.py` 的用例 B
   （`data:text/html,...` 带 `<script>` + `breakpoint:".*"` + `line:0`）跑 `flow`，
   测耗时与 `ok`。这决定 C1/C2 之外是否还有隐藏缺陷。**同一页面同时确认 `paused` 是否非空。**
4. **`auto` 的假成功**：`browser_debugger_auto {breakpoint:"mcp_probe", max_ms:3000}`（超时 ≥20s）→
   记录是否返回 `success:true, hits:0`。若如此，§3.3 被运行时确认。
5. **帧 ID 失效链**：`flow {url:PAGE, breakpoint:".*", line:0}`（**不传 resume**，默认 true）→
   取返回体 `paused.call_frame_id` → 立刻 `browser_debugger_evaluate {call_frame_id: <该值>, expression:"1"}` →
   记录是否 `-32000 Invalid call frame id`。这验证 §4.3(1)（我预期的最强 stale 证据）。
6. **活帧求值是否可用**：`browser_debugger_wait_paused {max_ms:8000, fresh:true}` → 取 `call_frame_id` →
   立刻 `evaluate`。若成功，说明问题是"帧的生命周期"而非"`evaluate` 本身坏"。
7. **观察者是否在册**：任一调试器命令的响应里是否出现 `auto_prepared`/自动处理说明
   （`MCP_Server.wsv:1705`、`:3133`），以及日志里有无 `[MCP] CDP观察者已自动注册到浏览器 ID:`（`MCP_Server.wsv:1602`）。
   这验证 §5/(b) 的排除是否成立。
8. **一次暂停后是否真的会冻结后续工具**（验证自救覆盖面）：
   制造暂停后**不** resume，直接 `browser_execute_js` 并观察是否出现
   `自动处理` 文案（`MCP_Server.wsv:3113`「Debugger.resume(页面原卡在断点, 已自动恢复并重试成功)」）。
   这验证 §8 补充里的"自救不覆盖 `等待CDP事件`"是否有实际后果。
9. **`parse:true` 与 `parse:false` 两条 evaluate 路径的响应形状**（为 C7 的形状变更评估影响面）。

---

## 11. 开放问题（需要主代理/用户裁决）

1. **C1/C4 在 `navUrl == ""` 时该"快速失败"还是"降级警告 + 短等待"？**
   动态注入脚本（`eval`/XHR 后 `appendChild`）确实可能在 `locations==[]` 之后加载并命中，
   故严格意义上不是"必然无效"。我倾向快速失败（诚实、可行动），但这是**产品语义**取舍。
2. **C2/C5 的默认值定多少？** 12s 是我按"15s 客户端 × 余量"选的，不是实测值。
   若目标客户端超时未知，更稳的做法可能是"默认短、由调用方显式传长"。
3. **C7 是否允许改变 `parse:false` 路径的响应形状？**
   `_audit/检测报告-第二轮.md:63-65` 显示该路径本就吞掉了 `parse`/`expand`，
   但我不知道是否有外部脚本依赖它的现有形状。
4. **是否需要给帧 ID 加"代次"（generation）标记**，让 `evaluate` 能判断"这个帧是否已失效"？
   这需要跨工具的状态传递（现有 `pausedSummary` 里只有 `call_frame_id`），**不是最小改动**，
   但如果 C7/C8 之后仍频繁出现 `-32000`，它可能是唯一真正治本的方向。
5. **`auto` 中途超时（已命中若干次）该算成功还是部分成功？** 我按"正常结束"处理（C3 只改零命中的情形），
   但 `hits:N < max_hits:M` 时是否应该显式标注"未达预期命中数"，属于语义问题。

---

### 附：本次分析读过的主要文件

`src/MCP_Server_Core.wsv`（分派与 auto 实现）、`src/MCP_Server.wsv`（flow 实现 / 等待与事件 helper / 同步等待预算）、
`src/MCP_Callbacks.wsv`（DevTools 观察者）、`src/MCP_ResponseBuilders.wsv`（响应形状）、`src/MCP_Constants.wsv`（TTL/上限）、
`_audit/tool_ledger.py`、`_audit/_tool_ledger.json`、`_audit/_ledger_status.txt`、`_audit/verify_debugger_realflow.py`、
`_audit/MCP工具可用性检测报告.md`、`_audit/检测报告-第二轮.md`（仅引用其既有结论）。

**本文件未验证任何补丁；未编译；未运行程序；未调用 MCP 工具；除本文件外未创建或修改任何文件。**
