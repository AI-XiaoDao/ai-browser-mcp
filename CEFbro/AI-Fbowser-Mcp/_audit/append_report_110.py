# -*- coding: utf-8 -*-
"""追加报告第 110 节(第94轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 110. 第94轮：把 §101.4 记下的「陈旧活帧」隐患实测一遍 —— **未复现**（附判别性对照）"
        "＋ 近期改动回归复测 16/18 无回归")

SECTION = """

---

%s

### 110.1 被点名的隐患：`evaluate` 的"活帧"可能是陈旧帧

报告 §101.4 记过一条隐患：E1 让 `browser_debugger_evaluate` 在缺 `call_frame_id` 时自动取"活帧"，
而 `确保调试器已暂停` 的**第一步**只判断"事件日志里有没有 `Debugger.paused`"：

```volcano
如果 (取CDP事件数据JSON ("Debugger.paused") != "")
{
    返回 (真)
}
```

事件日志是**跨导航、跨轮次保留**的，所以理论上可能拿一条早就失效的旧帧去求值，
内核回 `Invalid call frame id`。**本轮把它当成一个可证伪的命题来测**（`_audit/diag_stale_live_frame.py`）：

| 步骤 | 结果 |
|---|---|
| ① 基线：干净页面 `evaluate`（缺帧 ID） | 成功 0.17s，`Example Domain` |
| ② 制造暂停（`browser_debugger_stack`） | 拿到帧 ID `-2548972779245533571.1.0` |
| ② 继续：`resume` -> **导航到新文档** `?stale=2` -> 再 `evaluate`（缺帧 ID） | **仍然成功** 0.17s，值正确 |
| ③ **对照**：显式传一个编造的帧 ID | 失败 `{"code":-32000,"message":"Invalid call frame id"}` |

**结论：隐患未复现。** ② 成功、③ 仍失败 —— 说明 ② 的成功**不是**因为"帧 ID 根本没被使用"
（否则 ③ 也会成功）。值得注意的是：那个帧 ID **跨一次完整导航仍然可用**，
说明本机 CEF 的帧/执行上下文标识比预期稳定，旧帧未必立刻失效。

**如实保留的余地**：`确保调试器已暂停` 的"只看日志里有没有事件"这一判据仍然是**宽松**的，
本轮只证伪了"导航后必失效"这一种猜想，不能证明所有场景（例如跨源导航、渲染进程崩溃重建、
极长时间后）都不会碰到陈旧帧。故这条从"待测隐患"降级为"已测未复现，判据仍偏宽松"，
不再占用优先级，但也不宣布它被彻底排除。

### 110.2 近期改动的回归复测：**16/18，无回归**

近几轮改动较多（新增用户标识通路、新增 `browser_show_window`、覆盖率自动补前置、
`install` 确认闸、多处文案更正、suppress 预算回退），因此对**所有被我改过或依赖被改代码**的工具
做了一次集中复测：

| 结果 | 工具 |
|---|---|
| **通过 16 个** | `browser_create` / `browser_find_by_tag` / `browser_user_tags` / `browser_list` / `browser_reverse_precise_coverage` / `browser_debugger_evaluate` / `browser_debugger_resume` / `browser_move_window` / `browser_set_auto_resize` / **`browser_show_window`** / `browser_get_run_style` / `browser_reverse_hook` / `browser_reverse_hook_multi` / `browser_reverse_search` / `browser_reverse_runtime` / `browser_execute_js` |
| 仍失败 2 个（**均为预期**） | ① `browser_reverse_instrument_script` -> `install 需要显式确认`（§102 刻意加的确认闸，属**设计内**的拒绝）；② `browser_debugger_flow` -> 12.40s 有界失败并带 `reason`/`hint`（example.com 无脚本，属合法"目标不存在"）|

即：**近期所有改动都没有破坏既有能力**；两个"失败"一个是刻意的安全闸、一个是已说明的合法失败。

### 110.3 本轮指标（未改 `src/`）

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测 |
| 通过 | **296** |
| 失败 | **11**（OTHER 4 / TARGET 3 / PARAM 2 / GUARD 2） |
| 前置缺失类失败 | **0**；把实例卡死 0；幽灵注册 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `_audit/diag_stale_live_frame.py`（陈旧帧隐患的判别性测量） |

### 110.4 仍未做（下一轮）

- `install` 是否可以带一个 `auto_suppress` 尾巴（装完立即 `setSkipAllPauses`，让调用方落在
  "插装已装但不拦"的可用状态）——需先实测该组合是否真能落在可用状态，属新一轮测量任务。
- 台账剩 6 个"跳过项"未入账（已受控实测过）；`browser_reverse_return_value` / `set_variable`
  需真命中断点（当前页无脚本）。
- 能力面其余候选缺口：类库 `命令行` 系列（早期已证不可行）、菜单/快捷键 13 项、VIP 控制器 102 项分诊。
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
