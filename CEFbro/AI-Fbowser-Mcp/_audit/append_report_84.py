# -*- coding: utf-8 -*-
"""把第 84 节(第 68 轮)追加到 MCP工具可用性检测报告.md。

报告为 UTF-8 无 BOM / LF —— 追加时保持同样编码与行尾。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "MCP工具可用性检测报告.md")

SECTION = """
---

## 84. 第 68 轮：11 个幽灵能力全部补齐 + "前置缺失类失败"清零 + 度量本身的诚实性修复

### 84.1 需要"页面已暂停"的 7 个调试工具改为零前置（A 线核心指标达成）

**病灶**：`browser_debugger_stack / _step_over / _step_into / _step_out / _inspect / _last_paused /
_script_source` 在台账里全是 `fail/PREREQ`，文案统一为"页面未处于暂停状态 | 请先 debugger_flow 或
debugger_enable + 断点 + wait_paused" —— 即**调用方必须先手工编排一串断点流程**，否则工具直接不可用。

**为什么以前不敢让工具自己暂停**：`browser_debugger_pause` 曾被**故意禁用**，注释写明
"无JS执行点的页面上 `Debugger.pause` 永不返回，且冻结渲染器后堵塞后续 CDP 命令（队列 FIFO，
连自动 resume 都排在后面）→ 连锁超时"。根因是**页面上没有可暂停的执行点**，不是 pause 不可用。

**修法**：新增 `MCP命令服务器.确保调试器已暂停 (命令ID)`，两步消除该根因，7 个工具共用：
1. **先显式 `Debugger.enable`，再 `Debugger.pause`**（顺序是关键，见下）；
2. 用 `Runtime.evaluate` 注入 `setTimeout(function(){var _mcpPauseLanding=1;},30)` **安排一个必然
   很快执行的语句**，让 pause 有落点；再发 `Debugger.pause` 并等待 `Debugger.paused`（有界 6s），
   最多重试 2 轮。补过什么经 `auto_prepared` 如实上报。
最坏情况下 `执行CDP并同步等待` 的"卡死自救"会自动 resume，不会把会话留在冻结态。

**顺序为什么是关键（本轮由测量抓出来的真缺陷）**：第一版只靠 `执行CDP并同步等待` 的**反应式**补域，
实测 `browser_debugger_stack` 首次调用报"等待5秒仍未收到 Debugger.paused"，而**下一次**调用却发现
页面其实已经暂停 —— 即那次 pause 白做、下次才生效。原因是启用调试器域会**重置"下一语句暂停"标志**：
先 pause 后 enable == pause 被清掉。改为主动先 enable 后，干净页面首次调用即成功（0.06s）。

**验收（`_audit/verify_debugger_zeroprereq.py`，12/12 PASS）**：
干净页面（无断点、无暂停）直接 `stack` 成功且 `auto_prepared` 含 `Debugger.pause`；
`step_over/inspect/last_paused/script_source` 全部成功（`last_paused` 返回 `reason:"step"`，即**确实进入过
暂停态**，不是空转）；`resume` 后 `execute_js`/`get_text` 仍为 0.02–0.03s（**渲染器未被冻住**，这是
自动暂停最容易留下的坑）；`about:blank` 也能成功（0.2s）。

**顺带暴露出一个更深的老缺陷（已修）**：前置守卫被满足后，`browser_debugger_stack` 立刻暴露出
`-32602 Failed to deserialize params.stackTraceId: mandatory field missing` —— 它把**工具自身的 MCP 参数**
原样当 CDP 参数发给了 `Debugger.getStackTrace`，而该 CDP 方法要的是**错误对象**上的 `stackTraceId`
（来自 `Runtime.exceptionThrown`），与"当前暂停点的调用栈"根本不是一回事；这个缺陷一直被前面的
"未暂停"守卫挡着，从未暴露。现改为：当前暂停栈从 `Debugger.paused` 的 callFrames 取
（复用既有 `解析Debugger暂停摘要`），仅当调用方**显式**传 `stack_trace_id` 时才转发给 CDP（保留原能力），
并把该参数写进工具描述。

### 84.2 `browser_kernel_reverse_functions` 必失败的真因：**我们自己注入的 JS 有语法错误**

台账里它恒报 `函数提取失败: {"error":"JS异常:Uncaught"} | 页面可能因 CSP 拒绝脚本注入, 或已跨域跳转`。
独立审计（离线 V8 复现 + 逐字证据）定位到真因：注入串是**无任何换行的单行 JS**，而 `[...].forEach(...)`
之后漏写语句终结符，ASI（自动分号插入）因"整行没有行终结符"无法生效：
- `...}})}catch(e){}})['XMLHttpRequest', ...]` → `)` 后直接跟 `[`，被解析成"对 forEach 返回值取下标"
  （`[].forEach()` 返回 undefined → `TypeError: Cannot read properties of undefined`）；
- `...}catch(e){}})return out.slice(0,MAX)` → `)` 后直接跟 `return` → 解析期
  `SyntaxError: Unexpected token 'return'`。

②在**解析期**抛错，页面代码一行都没执行 —— 这就是它 100% 必失败、而同批近亲
`reverse_probe/algo/sources` 全部通过的原因。**两处各补一个分号**后实测 `pass`（0.04s）。

同时纠正**误导性文案**：原文案把原因归为"页面可能因 CSP 拒绝脚本注入，或已跨域跳转"——
CDP 的 `Runtime.evaluate` **不受页面 CSP 约束**，且失败在解析期、与页面无关。已在 3 处改为指向真实
原因（并点明"若为语法/解析类错误则属本工具注入脚本缺陷，重试无意义"），避免把排查方向带偏。

### 84.3 11 个"幽灵能力"全部补齐（本轮补上最后一个）

`browser_reverse_detect_traps`（反调试/风控陷阱检测）已实现并注册：用 `Debugger.searchInContent`
对 **7 类**常见反调试特征逐类检索（`debugger` 语句 / `Function.prototype.toString` 重写 /
`console` 探测 / `performance.now` 时序检测 / `setInterval` 定时自陷 / `navigator.webdriver`
自动化探测 / `devtools` 探测），每类给出命中数与命中行号及结论；`script_id` 可省略（自动选字节最大的
脚本，注册表为空时自动启用调试器等待上报），`classes` 可只测指定类别，`max_hits` 控制每类列出的行号数；
**单类检索失败只在该项标 `error` 原文，不让整次检测失败**。

工具总数 **301 → 312**（+11：7 个 `browser_reverse_*` CDP 工具 + 3 个 VIP 指纹工具 + `detect_traps`）。
台账实测：`browser_reverse_detect_traps` pass(0.13s)、`browser_kernel_reverse_functions` pass(0.04s)。

### 84.4 度量本身的诚实性修复（分类错误会把优化方向带偏）

**问题一：台账里的 `kind` 是"测试当时的分类"，各轮分类器版本不同，混在一起统计会失真。**
台账从第 33 轮累积至今，而分类器在第 56 轮改过（新增 `STATE` 并前置、收紧 `PREREQ` 正则），
旧条目仍保留旧类别。更糟的是 `PREREQ` 曾**误吞**两类失败：
- `browser_fill_*` / `browser_dom_click` 的目标不存在文案尾部有提示"注意 iframe 内元素**需先**切换框架"，
  其中的"需先"被 `PREREQ` 正则命中 → 7 个"目标不存在"失败被记成"缺前置"；
- `browser_dom_*` 的"元素不存在或取不到值"含"不存在"，本应先命中 `TARGET`，却因顺序记成了 `CAPABILITY`
  （错误地暗示"产品缺能力"）。

**修法（两道）**：① `prereq_of` 在分类前先 `strip_hints` 剥掉尾部"建议/注意/提示/替代"段 ——
它们是**行动建议**，不是失败原因；② `TARGET_RE` 补上"匹配到 0 个元素 / element not found"。
随后 `_audit/reclassify_ledger.py` 重算并**逐条打印变化**(旧类别→新类别+命中依据)，共 23 条，
全部为纠错（6 条调试工具 `PREREQ→STATE`、8 条 `CAPABILITY→TARGET`、7 条 `PREREQ→TARGET`、
3 条 `OTHER→GUARD`、1 条 `OTHER→PARAM`）。**PREREQ 由 14 降到 0。**

**问题二：探针给的值不适用于某些工具 → 测到的是"缺参守卫"而不是实现。**
新增 `mass_probe.TOOL_ARG_OVERRIDES`（按工具名覆盖入参），并修掉一个自己写错的语义：
第一版写成"仅在该参数缺失时补"，而那三个工具的入参恰好都是 **required**（通用取值已填），
覆盖被**静默跳过** —— 实测才发现 `base64_decode`/`kernel_events_all`/`set_zoom` 仍在测守卫。
改成"**替换**通用取值"后三者立刻 pass（`decoded:"hello"` / `全事件流已关闭` / `缩放(持久): 1.0`）。
另补 `mouse_wheel`(delta_y)、`kernel_download`(action=list)、`delete_cookies`(confirm) 的取值。

### 84.5 又一次踩到"voldev_awp 不带 @compile 会打开 IDE"

本轮开工时又发现一个滞留的 `voldev_awp.exe` IDE 进程（持有工程打开状态、可阻塞编译）。
查命令行确认**是我自己**在上一轮误用 `voldev_awp.exe /c <vprj>` 启动的（正确形式是
`voldev_awp.exe @compile <vsln> /c`）；该进程存活了 20 多分钟。已结束，并把这条写成硬规则。
**教训**：`voldev_awp.exe` 只传路径=打开 IDE，不编译；这也解释了上一轮"命令 120s 无输出且超时"。

### 84.6 新工具 `_audit/brace_check.py` 的自带 bug（记录以免后人再踩）

首版花括号收支自检把 `MCP_Server.wsv` 误报成"末深度 = -2"，而它编译 0 错 0 警。
原因是扫描器没有剥掉**行尾 `//` 注释**：注释里出现的引号被当成字符串起点，于是该行真正的 `{}` 被漏计。
修好后 8 个文件全部配平。**结论：拿不准时先怀疑度量工具，而不是源码。**

### 84.7 本轮台账进度与指标

| 指标 | 本轮开始 | 本轮结束 |
|---|---|---|
| 工具总数 | 311 | **312** |
| 已测 | 175 | **176** |
| 通过 | 120 | **139** |
| 失败 | 55 | **37** |
| **前置缺失类失败(PREREQ)** | 14 | **0** ✅ |
| **把实例卡死** | 0 | **0** ✅ |

剩余 37 条失败的性质分布（**全部落在"可接受"范围**）：
`TARGET` 27（参数指向的目标不存在，如探针用的 `#mcp-probe-nonexistent`）、
`OTHER` 5（3 个 `debugger_wait_paused/flow/auto` 因探针未编排断点而等满自身超时；
`file_dialog` 属有意不弹原生对话框；`browser_forward` 无前进历史）、
`CAPABILITY` 2（`move_window`/`set_auto_resize` 如实返回"嵌入式GUI浏览器不支持"）、
`PARAM` 1（`network_body` 需有效 CDP request_id，属需编排）、
`STATE` 1（未暂停时 `debugger_resume` 的诚实 no-op）、
`GUARD` 1（`vip_mouse_wheel` 的内核注入工具守卫）。
`auto_prepared 生效` 开始有记录（2 条），证明"零前置自动补"这条链路是活的。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf", "报告意外带 BOM, 中止以免改编码"
assert b.count(b"\r\n") == 0, "报告意外含 CRLF, 中止以免改行尾"
txt = b.decode("utf-8")
assert "## 84." not in txt, "第 84 节已存在, 中止(避免重复追加)"
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d, BOM=%s CRLF=%d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1,
         nb[:3] == b"\xef\xbb\xbf", nb.count(b"\r\n")))
