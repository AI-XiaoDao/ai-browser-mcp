# -*- coding: utf-8 -*-
"""追加报告第 107 节(第91轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 107. 第91轮：C 线「幽灵注册」查清 —— 实际为 0，并**更正我早期那个「16 个幽灵注册」的误报**")

SECTION = """

---

%s

### 107.1 先修测量，再下结论：我的第一版审计脚本把别名误报成幽灵

任务 D/C 线的原始描述里写着"**16 个'有号无实现'**"。本轮我用
`_audit/ghost_registry_audit.py` 做三向核对（命令注册表 / `添加工具JSON` / 派发分支），
第一版直接报出 **260 个**"幽灵注册"、**98 个**"有号无实现" —— 数字大得离谱，于是我先怀疑测量而不是产品，
逐条查明是**三个叠加的测量缺陷**：

1. **别名未归一**：注册表里同一个工具常有**两种写法**（`browser.create` 与 `browser_create`），
   项目分派入口本身就有 `子文本替换 (方法名, "browser.", "browser_")` 做归一。第一版没归一 ->
   所有"带点别名"都被算成幽灵。
2. **派发写法不止一种**：除 `否则 (方法名 == "x")` 外，还有成组的
   `如果 (规范名 == "a" || 规范名 == "b" || …)`（`browser_fill_*` 族就是这种）-> 第一版只匹配 `方法名 ==`，
   把**明明有实现**的工具误判成"无实现"。
3. **短别名未解析**：注册表里大量条目是**短名别名**（`back` / `close` / `evaluate` / `dom_query` …），
   它们不是工具。

三处都修好后（并且"注册名、加 `browser_` 前缀、加 `mcp_` 前缀、点换下划线"四种形式都试过才算无法解析）：

| 类别 | 结果 |
|---|---|
| ① 幽灵注册（注册了但没暴露给 AI） | 83 条，**逐条看都是别名**（短名/带点形式） |
| ③ **真·有号无实现**（注册了、且连别名都算不上） | **1 条 —— 就是 `browser.` 这个前缀别名本身**，即实际为 **0** |
| ④ 暴露了却没有派发分支 | **0**（修好后从 20 降到 0，那 20 条都是我正则的漏匹配） |

**结论：C 线的"幽灵注册"实际上不存在。**
同时要如实更正：早期那份"**16 个有号无实现**"的结论，与我这轮的第一版是**同一个误报机制**造成的，
应当作废 —— 它是静态正则的产物，不是产品事实。

### 107.2 那 3 个"注册了但故意不暴露"的名字不是幽灵，而是**刻意的安全设计**

`browser_create_tab` / `browser_task_runner_post` / `browser_debugger_pause` 在命令注册表里有号、
也**有实现**，但**不在工具清单**里（AI 看不到）。实测直接调用它们，得到的是**明确的拒绝**：

- `browser_create_tab` -> `⛔ 远程创建标签页已禁用 | 原因: 本工具**刻意不实现**(项目未开放远程建标签页入口) …`
  （旧文案称"GUI窗口自动管理浏览器实例"，上一轮已按代码事实更正）
- `browser_task_runner_post` -> 同上风格
- `browser_debugger_pause` -> `Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) | 请用 debugger_flow …`

即：**有实现、有号、但不暴露，且被调用时诚实拒绝**。这是"隐藏危险入口"的正当做法，
不应按"幽灵注册"处理，也不应删掉它们的注册项（删了反而丢掉这层保护与可诊断性）。

### 107.3 方法论教训（比结论本身更重要）

**"某个工具到底有没有实现"这个问题，静态正则答不可靠。**
本轮实测：同一份源码，换个正则就能在"98 个无实现"和"0 个无实现"之间跳。
派发至少有 `方法名 ==` 与 `规范名 ==` 两种写法，还有前缀路由与别名归一，
任何一处漏掉都会得到数量级不同的错误结论。

**权威判据是行为**：台账逐个真调（307 个已测、296 pass、11 fail 且全部可行动），
配合"工具清单 + 直接调用"的交叉验证。这也是本项目一直坚持"逐个真调、不靠静态推断"的原因 ——
本轮正好给出一个反例证据。

### 107.4 本轮指标（未改 `src/`）

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测（+6 危险项已受控实测） |
| 通过 | **296** |
| 失败 | **11**（OTHER 4 / TARGET 3 / PARAM 2 / GUARD 2） |
| **前置缺失类失败** | **0** |
| 把实例卡死 | 0；`CAPABILITY` 失败 = 0 |
| **幽灵注册** | **0**（本轮查清） |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `_audit/ghost_registry_audit.py`（三向核对 + 别名归一 + 两种派发写法） |

### 107.5 仍未做（下一轮）

- 台账剩 **6** 个"跳过项"（已受控实测，未入账）。
- `browser_reverse_return_value` / `browser_reverse_set_variable`：需**真命中断点**才可能通过（当前页无脚本）——取舍项。
- `browser_reverse_instrument_script` 阻塞 JS 通道的**根因**；陈旧活帧隐患（§101.4）。
- 能力面其余候选缺口（类库 `命令行` 系列、菜单/快捷键 13 项、VIP 控制器 102 项的分诊）。
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
