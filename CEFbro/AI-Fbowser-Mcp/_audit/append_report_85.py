# -*- coding: utf-8 -*-
"""把第 85 节(第 69 轮)追加到 MCP工具可用性检测报告.md。"""
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

## 85. 第 69 轮：一个**系统性**读取缺陷（缺键被当成"真"）+ 类库缺口审计收敛到 46 条

### 85.1 ★★ 系统性缺陷：`yyjson取逻辑_默认` 对**缺失键**不回落到默认值，一律返回"真"

**这是本会话影响面最广的一个缺陷：所有真实默认值为"假"的逻辑参数都会被静默反转成"真"。**

**发现路径（从"一个工具行为怪"追到"公共读取器坏了"）**：
台账里 `browser_debugger_wait_paused` 总是报"等待 Debugger.paused 超时"，而我第 68 轮加的自动暂停
明明成功了。于是做**判别实验**（`_audit/diag_pause_discriminate.py`）：
- **A 组**：造出暂停后**不碰** wait_paused —— 暂停稳定存活，`last_paused` 在 0s/1s/3s/6s/**11s** 都能读到，
  且不带 `auto_prepared`（说明是同一个暂停，不是被重新造出来的）；
- **B 组**：唯一差别是中间调了一次 wait_paused —— **之后暂停就没了**。
⇒ 结论钉死：`wait_paused` 把"它正要等的那个暂停事件"当场清掉了。

该分支里唯一会清事件的是 `等待CDP事件 (…, 清除旧)`，而 `清除旧 = yyjson取逻辑_默认 (参数JSON, "fresh", 假)`。
**交叉验证**（`_audit/crosscheck_logic_default.py`，用另一个语义完全不同的调用点）：
`browser_reverse_network_conditions {}`（`offline` 默认假）的响应里赫然写着 **`offline=true`** ——
两处独立证据同时指向同一个读取器。

读码找到了"早就写下、却只修了一半"的线索：`参数键存在` 的注释里已经写明
"取对象(键名)：缺失键返回假节点，是否为空() 为假、**取类型() 也不是 未知/空值**" ——
上一轮据此把**存在性判定**改成了序列化文本查找，**但没有改 `yyjson取逻辑_默认`**，
于是那里"缺失键类型=未知→回默认值"的分支**永远不会成立**。

**修法（修在根上，一处胜九处）**：在 `yyjson取逻辑_默认` 顶部先判 `参数键存在`，不存在即返回默认值。
随后把 `wait_paused` 里为绕过该缺陷而临时写的判断**改回直接调用**——同一逻辑只留一份实现。

**验收**：
| 判据 | 修复前 | 修复后 |
|---|---|---|
| `wait_paused`（暂停已存在） | ERR 2.10s"等超时" | **OK 0.01–0.03s**，且之后暂停仍在 |
| `browser_reverse_network_conditions {}` 的 `offline` | `offline=true` | **`offline=false`** |
| 构建 / 快检 | — | 0 警告 0 错误；41/41 |

**影响面清单（静态候选，供后续逐个真机复核）**：`yyjson取逻辑_默认 (参数JSON, 键, 假)` 共 **9 处**：
Core 的 `parse` / `fresh` / `capture_stack`，Reverse 的 `dry_run` / `restrict_to_function` /
`persist` / `offline` / `await_promise`，VIP 的 `reset`。
其中 **`dry_run` 反转最危险**（本该"干跑"却会真的执行），`offline` 会把浏览器置为断网，
`reset` 会静默复位指纹 —— 都属于"用户没要求却真的做了"的静默副作用。
另有 24 处默认值为"真"，方向安全（缺键返回真与默认一致），但仍属同一读取器的行为。

**副产品（正面）**：修好后 `browser_fingerprint_languages` 的空参调用从"通过"变成**正确地要求入参** ——
说明它此前的"通过"其实是 `reset` 被误判为真、静默复位指纹的**假成功**。补上真实入参后 pass。

### 85.2 两个被"证伪"的怀疑（记录了排除过程，避免下次重走）

1. **`data:` URL 被拒 ≠ 缺陷**：实测 `data:text/plain`、`data:text/html` 三种写法都被拒。
   读码发现这是**有意的安全策略**（`验证URL安全`）：拒 `javascript:`/`vbscript:`/`file:`，
   `data:` **只放行图片 MIME**（png/jpeg/gif/webp/bmp/x-icon），注释明确写着"防 text/html XSS / script 注入"。
   **但错误文案与 3 处工具描述都在说"仅允许 http/https/about/data/ftp"**，与实际策略矛盾、
   且不提示"data: 只支持图片"，撞墙后无从下手。已把常量文案 + 3 处描述 + 1 处注释改为
   "允许 http/https/about/ftp；data: 仅图片类型，为防脚本注入 data:text/html 被拒"。
2. **`set_breakpoint` 不命中 ≠ 缺陷**：先前在 `/about:blank` 上用 `document.write` 注入内联脚本，
   断点回 `"locations":[]` 且不命中。查明两点：① 那个内联脚本的 **URL 是空串**，URL 正则匹配不到；
   ② 更重要 —— 我填的 `line:0` **落在脚本范围之外**（欢迎页内联脚本实际是 `startLine=437, endLine=887`），
   第 0 行本就没有可断位置。**换成脚本真实行范围后 `locations` 立刻非空**：
   `[{"scriptId":"5","lineNumber":443,"columnNumber":15}]` —— 断点**绑定成功**，工具实现正确。
   教训与前几轮一致：**先用对照实验排除"测试场景特殊"，再判定产品缺陷**。

### 85.3 类库缺口审计第三轮收敛（B 线基准）

独立只读审计把 363 条候选逐条核对（工具名 / action 枚举 / `browser_cdp_call` 直通 / 非能力项四路）：
**确认缺口 46**（P0 2 / P1 9 / P2 35）、**误报 313**、**存疑 4**。报告 `_audit/_classlib_gap_confirmed2.md`。
- **P0**：`browser_create_background`（创建**完全无窗口**的后台浏览器；类库注释称优于无头模式、占用更低），
  复用路径 `main.wsv` 已有的 UI 线程创建路径，把 `FBrowser_创建浏览器` 换成 `FBrowser_创建后台浏览器`。
- **P1**：`类_FBrowser_命令行` 一族（无头模式/远程调试端口/自动播放/插入值）**只能在 CEF 初始化前生效**，
  应做成**启动通道**而非运行期工具；落点 `main.wsv` 的 `即将处理命令行` override 体**现成且为空**。
  注意 `--headless` 已被 MCP 服务端占用，新开关须换名。
- **误报的主要来源非常有价值**：覆盖藏在**批量工具**与**参数开关**里 —— 例如
  `内核开关_禁用ConsoleLog/Warn/Error…` 15 条只被 1 个 `browser_vip_disable_console` 覆盖；
  `高级鼠标_单击/移动/滚轮` 被鼠标工具的 **`kernel:true` 参数分支**覆盖（按工具名永远看不见）。
- **诚实折扣**：`类_FBrowser_应用事件` 判"无缺口"，但其中 `渲染_*` 一族属**名义覆盖** ——
  项目自己在代码里声明渲染进程事件不会派发、`app_render_*` 不产生记录。这类"名义覆盖"需与真覆盖分开看。

### 85.4 台账进度

| 指标 | 本轮开始 | 本轮结束 |
|---|---|---|
| 工具总数 | 312 | 312 |
| 已测 | 176 | **191** |
| 通过 | 139 | **152** |
| 失败 | 37 | **39**（含新测项） |
| **前置缺失类失败(PREREQ)** | 0 | **0** ✅ |
| **把实例卡死** | 0 | **0** ✅ |

剩余失败性质：`TARGET` 27 / `OTHER` 5 / `PARAM` 3 / `CAPABILITY` 2 / `STATE` 1 / `GUARD` 1，
全部落在"参数非法、目标不存在、本机不支持、需编排"这些可接受范围内。
另新增两个测试基建能力：**工具级前置调用**（`mass_probe.TOOL_PRE_CALLS`，为语义上依赖某状态的工具
声明最小前置序列并把结果写进备注）与**工具级入参覆盖的替换语义修正**（第一版写成"仅在缺失时补"，
而那几个参数恰好都是 required，导致覆盖被静默跳过 —— 实测才发现）。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf", "报告意外带 BOM, 中止以免改编码"
assert b.count(b"\r\n") == 0, "报告意外含 CRLF, 中止以免改行尾"
txt = b.decode("utf-8")
assert "## 85." not in txt, "第 85 节已存在, 中止"
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d, BOM=%s CRLF=%d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1,
         nb[:3] == b"\xef\xbb\xbf", nb.count(b"\r\n")))
