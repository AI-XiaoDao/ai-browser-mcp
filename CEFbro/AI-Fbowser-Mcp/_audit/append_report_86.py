# -*- coding: utf-8 -*-
"""把第 86 节(第 70 轮)追加到 MCP工具可用性检测报告.md。"""
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

## 86. 第 70 轮：`dry_run` 语义验证 + P0 后台浏览器落地 + 一个新暴露的实例退化现象

### 86.1 先补防护：修好读取器反而让某个工具变危险（时序很值钱的一段）

第 69 轮修掉"缺键被当成真"之后, `browser_reverse_patch` 的 `dry_run` 才**真正按文档缺省=false 生效**
(即"真替换脚本源码")。而它当时**还没被测过**, 未来某轮 `--next` 批量探测会给它喂占位源码(`mcp_probe`,
语法上恰好合法) —— 一旦真替换, 页面脚本被改成一个标识符表达式, 实例会被破坏并污染其后所有判定。
**"修好一个缺陷会改变别处的风险面"**, 故本轮第一件事就是把它加入 `mass_probe.MUTATING_SKIP`(附原因)。

### 86.2 `dry_run` 语义双方向验证（`_audit/verify_dryrun_semantics.py`，8/8 PASS）

在一次性页面(about:blank + `document.write` 注入两个小脚本)上, 用**合法极简源码** `var mcpPatchProbe=1;`
做替换, 判定依据是工具自己按 `选择 (ptDry, …)` 生成的提示语:

| 用例 | 期望 | 实测 |
|---|---|---|
| `dry_run:true` | "dryRun 通过(新源码可编译, 未实际替换)" | PASS |
| **省略 `dry_run`** | "脚本已热替换(对后续调用生效)" | PASS(证明缺省值不再被反转) |
| 显式 `dry_run:false` | 同省略 | PASS |
| 事后页面与 CDP 通道 | 仍健康 | PASS(execute_js 0.06s) |

### 86.3 P0 缺口落地：`browser_create {background:true}`（完全无窗口的后台浏览器）

类库签名(来自技能资料 `资料/类库/FBrowser浏览器/FBroLib.wsv`):
`FBrowser_创建后台浏览器 (链接地址, 浏览器设置, 请求环境, 额外信息, 浏览器事件, 禁用事件, 标识) → 逻辑型`,
注释原文:"创建一个完全后台没有窗口的浏览器, 该浏览器没有窗口, 也没有窗口句柄, 只能后台, 不能显示出来,
不同于创建浏览器再隐藏窗口, 也非无头模式其优于无头模式 …… 可用于纯后台刷新取数等相关操作,
比前台浏览器占用更低"。(另有 `_同步` 变体, 但类库注明**只能经 `FBrowser_任务运行器_投递任务` 到 UI 线程**;
本项目该工具位 `browser_task_runner_post` 被有意禁用, 故未采用 `_同步`, 而是复用既有的 UI 时钟握手。)

**实现(沿用既有机制, 不新增状态)**：`browser_create` 用 `__BG__` 前缀把"要建后台浏览器"告诉 UI 线程,
与 `main.wsv` 里既有的 `__SHUTDOWN__` 前缀**同一惯例**。UI 时钟线程识别前缀后调用后台创建 API,
命中后仍按原逻辑置 `待创建完成`。同时把 `background` 注册进工具 schema。

**验收（`_audit/verify_background_browser.py`）**：
创建成功(0.08–0.17s)→ `browser_list` 确实 +1(得到 id=2)→ **该后台浏览器真的能干活**:
`browser_execute_js {browser_id:2}` 读到 `Example Domain`、`browser_get_url` 读到它自己的 URL、
`browser_close {browser_id:2}` 正常关闭; 两个反向对照(省略 / 显式 `false`)都走可见窗口路径且文案不说"后台"。

**顺带修掉一个"创建后立刻用不了"的窗口期**：`browser_list` 已列得出来、但按 `browser_id` 取不到
(实测紧随创建调用会报"没有可用的浏览器", 隔约 1 秒再调又正常)。根因是
`浏览器容器.浏览器数组` 由"浏览器创建完成"事件**异步**回填。已在 `取浏览器ByID` 增加兜底:
数组里找不到时改用**类库自身**的 `FBrowser_浏览器_通过ID取浏览器`(权威来源) ——
`browser_close` 一直直接用类库接口, 所以从来没受这个窗口期影响。修后"无延时重测"通过。

### 86.4 ★ 新暴露的现象：用过第二个浏览器之后，主浏览器的同步执行路径持续退化

`_audit/diag_background_sideeffect.py` 的时序(每步都实测):

| 步骤 | 操作 | 耗时 |
|---|---|---|
| T1 | 主浏览器 `execute_js` / `get_text` | 1.18s / **0.02s**(CDP 健康) |
| T2a | `create background:true` | 0.40s(PASS) |
| T2b | 后台浏览器 `execute_js {browser_id:2}` | **30.23s** |
| T2c | 关闭后台浏览器 | 0.02s |
| T3a/T3b | 主浏览器 `execute_js` ×2 | **30.28s / 30.18s** |
| T3c | 主浏览器 `get_text` | **10.20s 且返回 null** |

`get_text` 返回 null + 10 秒级白等, 正是本项目既有的"**CDP 优先工具退化为原生路径**"特征。

**但本轮不下"后台特有"的结论**: 同一轮的可见窗口对照实验(创建/关闭第二个**可见**浏览器)之后,
主浏览器同样出现 35s 级变慢(原验证脚本因此把最后的健康检查判为 FAIL)。两种情形都变慢,
说明更可能是"**创建并使用第二个浏览器(+ 关闭)**"这件事本身在扰动, 而非后台模式独有 ——
未做同配置对照前不宣称归因。

**当前处置(诚实披露, 而不是留坑)**：本功能对"纯后台取数"这一目标可用且已验证, 但副作用已写进
`browser_create` 的 **参数描述与后台创建的成功文案**: 用 `browser_id` 操作第二个浏览器后若还要用
CDP 类工具, 建议重启 `AI-Fbowser-Mcp.exe`。**根因定位列为下一轮首要项**(候选方向: 第二个浏览器
未附着 CDP 观察者 → 落到原生 JS 回调路径 → URL 请求槽/同步等待被占住; 项目内已有"粘滞 URL 请求槽"
检测的相关字段可用于验证)。

### 86.5 另修 4 个工具的描述谎报（以本轮台账实测为依据）

台账里 `browser_vip_mouse_press` / `_release` / `browser_vip_key_input` / `_key_type`
**每一项之后都紧跟"实例不活, 先冷重启"** —— 即它们与其余 VIP 内核输入工具一样, 每次调用都会让
CDP 通道在本会话内失效。但它们的描述写的是"CDP鼠标按下"/"CDP输入字符", **看起来走 CDP**。
上一轮我**故意没给它们加警告**(当时没有实测证据, 不臆断); 本轮有了证据, 故按同一措辞补上警告
并指出 CDP 版替代工具。**至此"会打断 CDP 的 VIP 内核输入族"共 10 个工具的描述都已如实标注。**

### 86.6 台账进度

| 指标 | 本轮开始 | 本轮结束 |
|---|---|---|
| 工具总数 | 312 | 312 |
| 已测 | 191 | **206** |
| 通过 | 152 | **165** |
| 失败 | 39 | **41** |
| **前置缺失类失败(PREREQ)** | 0 | **0** ✅ |
| **把实例卡死** | 0 | **0** ✅ |

剩余 41 项性质: `TARGET` 27 / `OTHER` 6 / `PARAM` 4 / `CAPABILITY` 2 / `STATE` 1 / `GUARD` 1。
其中 `browser_debugger_evaluate` 的 `-32000 Invalid call frame id` 属"需编排"(探针给的是占位帧ID),
已记录为可用"先自动暂停 → 取真实帧ID"的专门用例覆盖, 不再用通用探针硬测。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf", "报告意外带 BOM"
assert b.count(b"\r\n") == 0, "报告意外含 CRLF"
txt = b.decode("utf-8")
assert "## 86." not in txt, "第 86 节已存在"
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d, BOM=%s CRLF=%d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1,
         nb[:3] == b"\xef\xbb\xbf", nb.count(b"\r\n")))
