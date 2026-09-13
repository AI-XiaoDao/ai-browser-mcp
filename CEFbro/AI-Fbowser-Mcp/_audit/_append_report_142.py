# -*- coding: utf-8 -*-
r"""追加报告章节: ## 142. 第124轮 —— "隐藏窗口 ⇒ 输入族 5 秒/不可用"的实测归因与自诊断落地。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 142. 第124轮：隐藏窗口导致的输入族异常 —— 从"偶发 5 秒"追到根因，并把它做成工具的自诊断

### 142.1 起点：一条回归臂开始偶发变红
快检里有一条回归钉：*"mouse_move 后 CDP 仍可用（未打死会话）"*（防的是"内核级鼠标注入把 CDP 通道打死"）。
它要求 `mouse_move` + 紧随的 `dom_query` **合计 < 3 秒**。第123轮末它开始偶发变红：`5.1s 且 dom_query=正常`
—— 内容正常、只有耗时超标。**先怀疑探针、再怀疑产品**：于是按"逐层定位"设计实验，而不是先改阈值。

### 142.2 排除法：不是通道损坏，也不是我们的派发代码
| 观测 | 结果 |
|------|------|
| `execute_js` / `dom_query` / `cdp_call(Runtime.evaluate)` | **0.02~0.03 秒**（全轮稳定） |
| 直发 `browser_cdp_call(Input.dispatchMouseEvent)` | **0.03 秒** |
| 改用 `CDP派发鼠标事件` 封装（`browser_mouse_move`） | **5.06 / 5.09 / 5.11 秒**（同一秒级常数） |
| 重启后再跑：`loop.py --nobuild` + 立刻量 | 一次 **5.07/5.08/5.16 秒**、另一次 **0.03/0.01/0.01 秒** ⇒ 逐**实例**随机 |
⇒ 排除了"内核注入打死通道"（那会让所有 CDP 优先工具 10~30 秒且常返回 null）、也排除了 SQLite 异步结果表与派发封装
（同一封装里 `execute_js` 只要 0.03 秒）。**慢的是 Input 域，且是实例级状态。**

### 142.3 根因：窗口不可见时渲染器被后台化节流（受控 A/B/A/B 复现）
想到"实例级状态"→ 窗口可见性。用 `browser_show_window` 做**可控切换**（`_audit/probe_input_visibility.py`）：

| 阶段 | `browser_mouse_move` | `Runtime.evaluate` |
|------|----------------------|--------------------|
| 基线（可见，GWL_STYLE 含 `WS_VISIBLE`） | 0.02 / 0.01 秒 | 0.03 秒 |
| **隐藏窗口**（`visible:false`，回读确认 `WS_VISIBLE=0`） | **5.12 / 5.11 秒** | 0.03 秒 |
| 显示回来（`visible:true`） | 0.03 / 0.03 秒 | 0.03 秒 |
| 再隐藏 / 再恢复 | 5.12 / 5.08 秒 → 0.03 / 0.03 秒 | 0.03 秒 |

⇒ **根因确定**：窗口不可见时 Chromium 把渲染器后台化（节流），需要渲染器参与的 CDP 命令被拖到 ~5 秒；
`Runtime.evaluate` / `Emulation.*` 不受影响。**不是产品缺陷、不是通道损坏**，快检那条臂的偶发红是**环境性**的。

### 142.4 把"每一类事件"都量清楚（用页面侧计数器当预言机，不靠工具自述）
`_audit/probe_hidden_input_semantics.py` 在页面上注入带 `mousemove/mousedown/mouseup/click` 计数器的按钮，
隐藏窗口后直发 CDP（绕开工具内部预算）：

| 事件 | 可见 | **隐藏（WS_VISIBLE=0）** | 隐藏态是否真实生效 |
|------|------|--------------------------|--------------------|
| `Input.dispatchMouseEvent(mouseMoved)` | 0.03 秒 | **5.08 秒（仍成功）** | **是**：页面 `mousemove` 计数 +1 |
| `…(mousePressed/mouseReleased)`（点击） | 0.03 秒 | **0.03 秒（完全不受影响）** | **是**：页面 `click` 计数 +1 |
| `Input.dispatchMouseEvent(mouseWheel)` | 0.03 秒 | **永不返回**（直发三次 30 秒全部超时） | **否**：`scrollY` 不变 |
| `Input.dispatchTouchEvent` | 0.03 秒 | **永不返回**（直发三次 30 秒全部超时） | 否 |
| `Runtime.evaluate` / `Emulation.setTouchEmulationEnabled` | 0.03 / 0.01 秒 | **0.03 / 0.01 秒** | —（⇒ 通道健康） |

### 142.5 由实测推出的三个真实缺陷（本轮全部修掉）
1. **触摸族的报错把成因指错**：隐藏态 `browser_touch_press` 白等 **8.24 秒**后回
   *"本会话 CDP 通道已不可用（常见诱因是先前调用过内核级注入 kernel:true）"* —— 而同一时刻
   `execute_js` 0.03 秒、直发 `Emulation.setTouchEmulationEnabled` 0.01 秒，**通道明明是健康的**。
   调用方会照这条文案去"换方法试错"，正是本目标要消灭的体验。
2. **滚轮同样永不返回，却连守卫都没有**：隐藏态 `browser_mouse_wheel` 也是白等 8 秒后同一句误导文案。
3. **慢因对调用方不可见**：`mouse_move` 慢 5 秒但成功，调用方没有任何线索知道"这是窗口不可见，不是坏了"。

### 142.6 落地（复用既有机制，不新造轮子）
- `MCP_Server.wsv` 新增三个复用件：
  - `浏览器窗口可见 ()` —— 回读 `GWL_STYLE` 的 `WS_VISIBLE` 位（0x10000000），与 `browser_show_window` 同一判据；
  - `记CDP输入慢因 (起始毫秒, 输入类别)` —— **只在 >2 秒时**才回读一次可见性，并按既有
    `MCP_响应构建.记录自动处理` 机制经 `auto_prepared` 如实上报成因与恢复手段（零常态开销、不静默改状态）；
  - `CDPInput失败原因文本 (动作名)` —— 派发失败时区分"窗口不可见"与"通道真损坏"，并按三类事件给事实。
- 挂载点选择**汇聚点而非各工具分支**：`CDP派发鼠标事件`（鼠标四件套 + `reverse_input_cdp`）与
  `CDP派发触摸点一次`（触摸三件套）各一行计时 + 一行上报；`CDP派发触摸事件` 与 `CDP派发鼠标事件(mouseWheel)`
  各加一条"窗口不可见 ⇒ 立即失败"的守卫（该状态在窗口恢复前**不可能成功**，白等 8 秒毫无价值）。
- `MCP_Server_Core.wsv` 的 6 处失败文案（鼠标 3 + 触摸 3）改为调用上述复用件，尾部替代方案原样保留。
- 8 个工具的描述按**各自**实测分别措辞（点击那条特意写明"隐藏态照样可用"，否则调用方会白做"先显示窗口"一步）。

### 142.7 验收（`_audit/verify_input_occlusion.py`，25/25 通过）
- 可见态：`mouse_move` 0.03 秒、触摸/滚轮成功，且**没有**任何慢因上报（不误报）；
- 隐藏态：`mouse_move` 5.13 秒**成功** + `auto_prepared` 点明"窗口不可见"并给出 `browser_show_window {visible:true}`；
  **页面侧预言机**确认 `mousemove` 计数 +1（事件真实到达）；
- 隐藏态：`execute_js` / `cdp_call` 仍 0.03 秒 ⇒ 与"通道损坏"可区分；
- 隐藏态：`mouse_click` 0.05 秒**成功**且页面 `click` 计数 +1（**隐藏不影响点击**，无需先显示窗口）；
- 隐藏态：`touch_press/move/release` 与 `mouse_wheel` **0.00~0.01 秒快速失败**（原来 8.2 秒），
  报错同时给出"不可见 + 通道本身健康 + 恢复手段"；
- 恢复可见：全部立即回到 0.03 秒级、慢因上报消失（按请求清除，不污染后续回复）。

### 142.8 快检那条臂的修正（把环境性偶发与非环境性回归分开）
臂现在先用**只读**的 `browser_get_window_style` 判 `WS_VISIBLE`，**只在不可见时**才幂等地显示回来，再断言 <3 秒，
并把原始 `style` 写进明细。这样：环境性慢（窗口被遮挡/隐藏）不再假红，而"内核注入打死通道"这一真回归仍会立刻变红
（那种情况即使窗口可见也慢 10~30 秒且常返回 null）。本轮快检稳定 **56/56（4.5~15.6 秒）**。

### 142.8.1 验收脚本自身的两处探针缺陷（先怀疑探针，已修）
- `browser_touch_release {}` 会按设计**拒绝**（必须给 x/y，避免误触左上角）——原先探针按"无参"调用，导致两条触摸断言失败；
  改为显式传 x/y 后通过（这是**探针**的问题，不是产品问题）。
- 滚轮那两条断言最初把 `scrollY` 的"前值"读在滚轮**之后**，于是"前后相同"被误判成"没滚动"；
  修正为**滚轮前读前值**后，实测 `scrollY 60 → 120`，并顺带用独立脚本 `_audit/probe_wheel_after_restore.py`
  复核了"恢复可见后连续三次滚轮每次都真实下滚 60px"（0.01~0.03 秒），排除了"首次滚轮被吞"的猜想。

### 142.9 状态
工具 **321**；台账 **321/321** 已测（315 通过 / 6 未通过 = 2 个刻意确认闸门 + 4 个已记录探针假目标，本轮给 8 个
受影响工具补了实测注记）；快检 **56/56**；`verify_input_occlusion.py` **25/25**；会话健康探针全 0.03 秒级。
已知且有据的边界（本轮实测后**如实写明**，不再让调用方猜）：窗口隐藏时 —— 鼠标**移动**约 5 秒（仍成功）、
鼠标**点击**不受影响、**滚轮与触摸不可用**（立即失败并给出成因）、读类与 `Runtime/Emulation` 完全正常。
'''

# 注: 本字面量内不含三个连续双引号


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 141.' in text, '章节 141 应已存在'
    if '## 142.' in text:
        # 已追加过: 允许用 --replace 覆盖本章(仅本章, 不动其它章节)
        assert '--replace' in sys.argv, '章节 142 已存在(要覆盖请加 --replace)'
        cut = text.index('## 142.')
        text = text[:cut].rstrip('\n') + '\n'
        print('已截去旧的第 142 章')
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已追加/更新: %d -> %d 字符' % (len(raw.decode('utf-8')), len(out)))
    else:
        print('[dry-run] 将写入 %d 字符' % len(SECTION))


main()
