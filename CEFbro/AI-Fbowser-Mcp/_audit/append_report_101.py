# -*- coding: utf-8 -*-
"""追加报告第 101 节(第85轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = "## 101. 第85轮：flow/evaluate 改动清单落地（拖了两轮，本轮做完）＋ 失败原因被吞的横切缺陷"

SECTION = """

---

%s

### 101.1 终于落地：`flow` / `evaluate` 五项改动

这份清单来自只读复核（`_audit/_flow_evaluate_fix_plan.md`，逐字锚点），我连续两轮推迟，本轮一次做完。

| 项 | 改动 | 为什么 |
|---|---|---|
| **E1** | `evaluate` 在 `call_frame_id` 为空时**复用 `inspect` 的活帧获取**（已暂停则直接复用；未暂停则先制造暂停点并经 `auto_prepared` 上报，再从最近一次 `Debugger.paused` 读帧） | 原来缺帧 ID 直接失败，而 AI 最自然的用法就是"给个表达式让我看看" -> **第一次调用必失败** |
| **E2** | `evaluate` 的 schema：`call_frame_id` 不再必填 + 文案同步 | 不改必填列表的话，严格按 schema 校验的客户端**永远不会**发出"不带帧 ID"的调用，E1 等于白改（这是契约变更，功能变宽松） |
| **E3a** | `解析Debugger求值结果` 的失败分支：原因取值从只读 `"message"` 改为回退链 `message` -> `error` -> `result`，并给帧失效加行动指引 | 写入失败原因的是 `处理CDP响应`，它写的键是 `"error"`/`"result"`，**从来没有 `"message"`** -> 任何失败都被吞成 `{"ok":false,"error":""}`。**覆盖面**：evaluate(parse:true)、flow、inspect、auto 全走这个翻译器 |
| **F2** | `flow` 默认等待 45000 -> **12000ms**（+ schema 文案） | 45000 远超客户端耐心（台账客户端 15s 就放弃）-> "客户端先超时 + 服务端还在等"，调用方只看到 timed out |
| **F3** | `flow` 超时失败体：**保留** `step`/`error`，**追加** `waited_ms`/`reason`/`hint` | 原来只有 `error:"timeout"`，看不出等了多久、为什么没等到 |

### 101.2 实测效果（三个都是"从失败变可用"）

| 工具/场景 | 修复前 | 修复后（实测原文） |
|---|---|---|
| `browser_debugger_evaluate {expression:"document.title"}`（**不给帧 ID**） | 必失败：`call_frame_id和expression 参数不能为空` | **成功 0.18s**：`{"result":{"type":"string","value":"Example Domain"}}` |
| `evaluate` 传**非法帧 ID**（`parse:true`） | `{"ok":false,"error":""}` —— 原因被吞光 | `{"ok":false,"error":"{\\"code\\":-32000,\\"message\\":\\"Invalid call frame id\\"} | call_frame_id 与当前暂停点绑定: 页面 resume 之后立即失效 —— 而 browser_debugger_flow / browser_debugger_auto 默认 resume:true … 取活帧: browser_debugger_wait_paused 或 browser_debugger_last_paused …"}` |
| `browser_debugger_flow {breakpoint:"不存在的脚本"}` | 死等 45000ms，只报 `timed out` | **12.42s** 有界失败：`{"ok":false,"step":"wait_paused","error":"timeout","breakpoint":"…","waited_ms":12000,"reason":"等待 Debugger.paused 超时(12000ms) | 未传 url: 本工具不会导航…","hint":"可行动: ①用 browser_reverse_get_possible_breakpoints 确认该脚本真正可下断的行列…③需要更久请显式传 max_ms"}` |

台账随之变化：`browser_debugger_evaluate` **fail -> pass**（0.17s）。

### 101.3 顺手修的一个"清场工具却会失败"

`browser_debugger_resume` 在页面本就未暂停时报**失败**（`页面未处于暂停状态, 无需恢复`）。
但 resume 是**清场/收尾**类工具——"本来就没暂停"说明目标状态已达成，不是错误；
报失败会让 AI 以为需要"先制造暂停再恢复"，去做无意义的多步调用（正是本目标要消灭的"反复换方法"）。
已改为**幂等成功**，且如实说明"未执行任何动作"（不谎报做过事）：台账 `fail -> pass`。

### 101.4 验收 10/11，唯一的 FAIL 是**我的断言写错**

`_audit/verify_flow_evaluate.py` 11 条里 10 条通过。唯一未通过的断言是"①的成功响应里应含 `auto_prepared`"。
查证结论：**不是产品问题，是我的断言错了**——`确保调试器已暂停`（`MCP_Server.wsv:1661-1664`）
在**事件日志里已有 `Debugger.paused`** 时**立即返回真**、不做任何动作；既然没做事，自然没有 `auto_prepared` 可报。

**顺带记一个由此暴露的隐患（P2，待测）**：该早返回只看"日志里有没有 paused 事件"，而事件日志要跨导航/跨轮次保留，
所以 E1 取到的"活帧"**可能是陈旧的**。本轮它恰好取到了可用帧并成功返回，但这条链路的可靠性
需要专门测量（例如：导航后不重新暂停就直接 evaluate，看是否会用陈旧帧）。已列入下一轮。

### 101.5 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | 271/312 已测 |
| 通过 | **234**（本轮 232 -> 234）；失败 39 -> **37** |
| 把实例卡死 | 0；`CAPABILITY` = 0 |
| 本轮修复 | flow/evaluate 五项 + resume 幂等化（共 6 处） |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增验证 | `verify_flow_evaluate.py`（**10/11**，1 条为断言写错）、`fix_flow_evaluate.py`（7 处锚点唯一性前置校验） |

### 101.6 仍未做（下一轮）

- 台账还剩 **41** 个未测项。
- 101.4 的陈旧活帧隐患（P2，需专门测量）。
- `evaluate` 的 `parse:false` 原始路径仍会原样透传 CDP 错误（复核方案 E3b 需变更响应形状，当时判定**不做**，维持）。
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
