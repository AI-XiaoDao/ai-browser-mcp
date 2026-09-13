# -*- coding: utf-8 -*-
"""把第 90 节(第 73 轮)追加到 MCP工具可用性检测报告.md。"""
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

## 90. 第 73 轮：读取链修好（第二个浏览器能读了）+ 一个**与浏览器无关**的"空文本被当成读不到"

### 90.1 现象与判别式诊断
接第 72 轮留下的"已知局限": `browser_get_text` 对**非主浏览器**返回字面 `null`。先用判别式场景定位
(`_audit/diag_gettext_second_browser.py`: 主浏览器 example.com、第二个浏览器 about:blank, 两者可区分):

| 探针 | 实测 |
|---|---|
| `execute_js {browser_id:2}` 读 `location.href` | **about:blank**(确实是第二个浏览器) |
| `get_text {selector:'h1', browser_id:2}`(第二个浏览器也在 example.com) | **null** |
| `fill_exists {selector:'body', browser_id:2}` | `1`(填表框架能看见 DOM) |
| `fill_attr_get {selector:'body', attr:'tagName', browser_id:2}` | **null** |
| `get_text {selector:'h1'}`(主浏览器, 对照) | Example Domain |

⇒ "在第二个浏览器上执行 JS"没问题, 断在**读取链的第二、三跳**。

### 90.2 顺带发现一个**与浏览器无关**的缺陷: 元素存在但文本为空 → 返回 null
`get_text` 原来拼的 JS 是 `return e?e.textContent:'__MCP_NO_ELEM__'`。当元素**存在但文本本来就是空**
(例如空的 `<div>`、空的输入框)时, `textContent` 就是 `""`, 而调用侧的判据是
`js取文值 != ""` —— **空串被当成"读不到"**, 于是退到原生路径, 最终给出字面 `null`。
**这在主浏览器上同样会发生**, 与多浏览器无关, 只是此前没人测"空元素"这一种输入。

**修法**: 给这段 JS 加前缀哨兵 —— 读到就返回 `__MCP_TEXT__` + 文本, 元素不存在才返回 `__MCP_NO_ELEM__`,
从根上把"读到了空串"与"没读到"分开; 返回给客户端前再去掉前缀。

### 90.3 第二处: 第二跳的"内联等待"拿不到回调结果
`原生执行JS并等待` 内部是**内联等待**(`等待异步任务完成`), 在第二个浏览器上它返回空串;
而 `browser_execute_js` 的原生回退是"**提交回调 + 把异步回执交回外层**, 由 尝试同步跟随异步响应 去等",
同一条路径实测 0.06s 就能取回内容。差别不在"能不能执行", 而在**谁来等**。
故把 `get_text` 的最后手段从"填表框架 取元素内容"(对第二个浏览器立刻以 null 结束)换成
**与 execute_js 完全相同的"提交原生 JS + 异步回执"机制**(复用已验证路径, 不另造轮子)。

**递归修掉的两个自身错误(都是实测抓出来的)**:
1. 占位对象漏写 `max_ms` → 外层"同步跟随"按占位里的 `max_ms` 决定等多久, 于是只等 **0ms** 就报
   `等待超时(0ms)`。与 `browser_execute_js` 的占位**逐字对齐**后才正常。
2. 异步这条路会把回调结果**原样**交给客户端, 工具侧没机会去前缀 → 第一版把内部哨兵漏给了用户:
   实测返回 `__MCP_TEXT__Example Domain`。故异步路径改用**不带哨兵**的片段(走到这一跳时前面的同步
   路径已判定过元素是否存在, 无需哨兵)。

### 90.4 验收（`_audit/verify_gettext_fixes.py`，5/5 PASS）

| 用例 | 修复前 | 修复后 |
|---|---|---|
| 主浏览器正常元素(回归) | Example Domain | **Example Domain**(0.03s) |
| **元素存在但文本为空** | 字面 `null` | **成功且内容为空串** |
| 元素不存在 | 明确失败 | **明确失败**(仍带"先用 snapshot 确认"的建议) |
| **第二个浏览器 `browser_get_text`** | 字面 `null` | **`Example Domain`(0.05s)** |
| 第二个浏览器读不到时 | 静默 `null` | 改为**如实报超时**, 不再有假成功 |

另: 构建 0 警告 0 错误; `fastcheck` **41/41**; 台账复测 `browser_get_text`/`browser_get_source` 通过。

### 90.5 第三次同步更正披露文案
第 70 轮我写下"用第二个浏览器后主浏览器会持续变慢"(第 71 轮修掉并更正),
第 72 轮又写下"get_text 对非主浏览器返回 null"(本轮修掉)。**同一处描述三轮改了三次** ——
这本身是个提示: **凡"当前限制"的表述都必须绑定测量时间, 修好就得同步改**,
否则描述会从"诚实披露"退化成"新的误导"。本轮已把两处(工具参数描述 + 创建成功文案)改为
"实测目标隔离正确、不影响主浏览器 CDP 工具, 读取亦正常", 不再保留任何已失效的限制说明。

### 90.6 台账进度
**218/312**; **前置缺失类失败维持 0、把实例卡死维持 0**; 剩余失败仍全部落在
目标不存在 / 参数非法 / 本机不支持 / 需编排这些可接受类别。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf" and b.count(b"\r\n") == 0
txt = b.decode("utf-8")
assert "## 90." not in txt
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1))
