# -*- coding: utf-8 -*-
"""追加报告第 102 节(第86轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 102. 第86轮：覆盖 271->300/312 ＋ 唯一那个「把实例卡死」的工具：先测清、再改承诺、最后加确认闸")

SECTION = """

---

%s

### 102.1 覆盖推进：271 -> **300/312**（通过 234 -> 259）

本轮按"一次一个功能"推了 29 个，其中 6 个原先是**测试侧缺参**造成的假失败（只测到守卫），
已用真实且无害的取值覆盖后打到实现：

| 工具 | 原失败原文 | 覆盖取值 |
|---|---|---|
| `browser_retry` | `重试3次后仍失败 \\| tool=mcp_probe` | `tool="browser_status", max_retries=1`（换成必然成功的只读工具） |
| `browser_highlight` | `selector 参数不能为空` | `selector="h1", action="show", duration_ms=100`（自动清除，不留高亮框） |
| `browser_reverse_search_script` | `query 不能为空` | `action="list"`（只读，不需要 query） |
| `browser_reverse_listeners` | `需提供 object_id 或 selector` | `selector="document"` |
| `browser_reverse_dom_resolve` | 同上报错 | `selector="h1"` —— **注意**：它把 selector 拼成 `document.querySelector(selector)` 取 objectId，
所以给 `"document"` 会得到 `querySelector('document') -> null` 而失败；必须给**页面上真实存在的元素**。第一次给 document 就是这么失败的。 |

### 102.2 唯一一个"把实例卡死"的工具：先测清，再改承诺，最后加闸

台账把 `browser_reverse_instrument_script`（默认 `action=install`）记为 `fail(wedge)` 并冷重启过。
但"台账认为死了"不等于"真死了"——**该工具的设计意图就是"命中后暂停，让调用方去分析"**，
所以必须先分清"硬卡死"还是"只是留下一个可恢复的暂停"。为此写了专门的测量脚本
`_audit/diag_instrument_script_wedge.py`（干净重启后逐步计时）：

| 步骤 | 结果 |
|---|---|
| 基线 | `browser_status` 0.00s / `browser_execute_js` 0.03s |
| `action=install` 之后 | `browser_status` **仍 0.02s**（它走原生、不经 CDP）；`browser_execute_js` **30s 超时**；`browser_debugger_last_paused` 30s 超时 |
| 再 `browser_debugger_resume` | 返回 ok（5.47s），但 `execute_js` **仍 30s 超时** |
| 再 `action=suppress`（工具自称的止血） | 45s 超时；之后 `status` 恢复（5.87s），但 `execute_js` **仍 30s 超时** |

**结论：这是硬卡死，不是可恢复的暂停**——`resume` 与该工具自己的 `suppress` 都救不回来，只有重启进程。
因此既有文案「分析完务必 browser_debugger_resume（否则页面一直卡住）」在**本机 CEF 构建上不成立**：
它会让调用方以为"resume 一下就好了"，然后陷进"每个 JS 类工具都连环超时"的境地 ——
正是用户描述的"连续失败、反复换方法"。

本轮按"**先测清事实 → 再改承诺 → 最后加闸**"三步处理，且**刻意不改它的行为**（在脚本执行前暂停是该工具存在的理由）：

1. **改承诺**：工具描述与源码注释都按实测更正（含"只有重启进程才能恢复"与替代工具建议）。
2. **加确认闸**：`install` 是**默认动作**，于是"顺手空参调一下"就会把整个会话搞死。
   已改为 `install` 必须显式传 `confirm:true`，否则**安全拒绝**并把实测后果与替代方案说清楚
   （与项目既有的危险动作确认惯例一致，如 `browser_vip_enable_js_env`）。`remove`/`suppress` 不需要确认（它们不引入阻塞）。

**效果**：台账「把实例卡死」由 **1 -> 0**；默认调用从"6.31s 后卡死、被迫冷重启"变为
**0.01s 安全拒绝 + 可行动说明**。

### 102.3 本轮我自己引入的一个编译错误（如实记录）

给工具描述加"实测更正"时，我在**火山字符串字面量内部**用了 ASCII 双引号
（`原来的"分析完务必 resume"…`），直接破坏字面量 -> 编译报
`MCP_Server.wsv, 9925: 错误: 发现字符处于无效位置`。已改用全角引号「」修正。
**规则重申：`.wsv` 字符串字面量内部不要用 ASCII 双引号，用全角引号或中文书名号。**

### 102.4 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | **300/312** 已测（本轮 271 -> 300），仅剩 **12** 未测 |
| 通过 | **259**（本轮 234 -> 259） |
| **把实例卡死** | **0**（本轮 1 -> 0） |
| `CAPABILITY` 失败 | 0 |
| 失败性质 | TARGET 26 / OTHER 9 / PARAM 3 / STATE 2 / GUARD 1 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `diag_instrument_script_wedge.py`（硬卡死 vs 软暂停的判别测量） |

### 102.5 仍未做（下一轮）

- 台账剩 **12** 个未测项。
- `browser_reverse_instrument_script` 的**根因修复**（为什么装上就让 JS 通道阻塞，是否可用
  `Debugger.removeBreakpoint`/换 event 类型避免）：本轮只做到"知情选择"，没解决根因。
- 101.4 记录的**陈旧活帧**隐患（`确保调试器已暂停` 只看日志里有没有 paused 事件，日志跨轮次保留）。
- algo / gwatch 的 `push`/`shift`（噪音，非风险）。
""" % HEAD


def main():
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        cur = f.read()
    assert not cur.startswith(u'\ufeff'), "报告带 BOM"
    assert '\r' not in cur, "报告含 CRLF"
    assert HEAD not in cur, "该节已存在, 拒绝重复追加"
    with io.open(REPORT, 'a', encoding='utf-8', newline='') as f:
        f.write(SECTION)
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        new = f.read()
    assert not new.startswith(u'\ufeff') and '\r' not in new, "追加后编码被破坏"
    print("已追加: %s" % HEAD)
    print("行数: %d -> %d" % (cur.count('\n') + 1, new.count('\n') + 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
