# -*- coding: utf-8 -*-
"""追加报告第 111 节(第95轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 111. 第95轮：用 `//# sourceURL` 打破「脚本 url 全为空串」的死结 —— "
        "auto/flow 由**无法测**变为**实测通过**")

SECTION = """

---

%s

### 111.1 长期障碍：本页所有脚本 url 都是空串 -> urlRegex 断点永远 0 命中

报告 §95/§96 记录过：`setBreakpointByUrl` 需要一个**能匹配上的 URL**，而本机实测"本页 8 个已注册脚本
的 url 全是空串"，于是任何 urlRegex 都得到 `"locations":[]`，`browser_debugger_auto` / `flow` 的
"按 URL 下断"路径**在本机不可能命中**，只能记成"目标未命中"；`return_value` / `set_variable`
也因此拿不到真实断点帧。这是"工具看起来不能用、其实测不了"的典型困境。

### 111.2 解法（实测）：给注入的脚本加一行 `//# sourceURL=...`

```js
window.mcpBpFn=function mcpBpFn(){ var v=1; return v; };
window.mcpBpTimer=setInterval(window.mcpBpFn,300);
//# sourceURL=https://example.com/mcp-breakpoint-probe.js     <-- 关键这一行
```

实测（`_audit/diag_breakpoint_e2e.py`，干净重启、严格按"导航->启用调试器->注入->确认定时器在跑->下断"）：

| 观察 | 结果 |
|---|---|
| 脚本注册表里的 url | `https://example.com/mcp-breakpoint-probe.js`（对比：不写 sourceURL 时 url 为空串） |
| 探针是否真在跑 | `{"tick":15,"timer":"number"}` 且在涨 |
| `auto {breakpoint:"mcp-breakpoint-probe", line:3}`（`return v;` 那行） | **命中 1 次**，`completed:true` |
| 同上 `line:2`（`var v=1;`） | **命中 1 次** |
| `line:1`（函数声明行） | 0 命中（**符合预期**：声明行不是可执行位置） |

据此给台账补了共享前置（启用调试器 + 幂等注入带 sourceURL 的探针脚本）与覆盖，结果：

| 工具 | 修复前 | 现在 |
|---|---|---|
| `browser_debugger_auto` | 0 命中（无法测） | **pass 1.01s**（真命中 2 次） |
| `browser_debugger_flow` | 0 命中（无法测） | **pass 0.46s**（真命中） |

即：两个长期"测不了"的工具，现在是**实测可用**。

### 111.3 途中有三次我自己的测试自伤（全部被抓出并修正）

1. **清场动作污染了调试器状态**：上一个诊断脚本结尾为清场调了
   `Debugger.setBreakpointsActive {active:false}`，而该状态**持续生效** ->
   之后**任意行号**都 0 命中，看起来像产品缺陷。收尾已改为只 resume。
2. **在已被导航过的页面上直接下断**：当前文档里根本没有探针脚本，自然 0 命中（无效测量）。
3. **我自己的幂等判据撒谎**（最隐蔽的一个）：注入码写的是
   `if(window.mcpBpTimer)return 'exists';` —— 但 `clearInterval` 之后那个变量**仍是个数字（真值）**，
   于是判据认为"已注入"而**跳过重装**，定时器其实早死了 -> 断点永远 0 命中。
   已改为**无条件重装**（先清旧定时器再注入新脚本）。**教训：幂等判据必须验证"功能仍活着"，而不是"变量存在"。**

### 111.4 仍未解决（精确记录，供下一轮）

- `browser_reverse_return_value`：前置三步全部 OK（页面确实停在断点上），仍报
  `Debugger.setReturnValue 失败: Invalid parameters`。而工具构造的参数是
  `{"result":{"value":<value>}}`（`MCP_Server_Reverse.wsv:1239`），**与 CDP 的 CallArgument 形状一致**
  —— 所以不是参数拼错。需要一次**原始 CDP 对照探测**（直接 `browser_cdp_call Debugger.setReturnValue`
  用同样的 params，看内核回什么），才能判断是"帧位置不合法"还是别的。
- `browser_reverse_set_variable`：本轮它的 flow 前置在台账里返回 `ERR_GOOD`（前置自身失败），
  于是它拿不到帧、报"无法从暂停事件取到 call_frame_id"。前置链需要更稳健（例如前置失败时改为
  直接报"前置未就绪"而不是让被测工具背锅）。

### 111.5 本轮指标（未改 `src/`）

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测 |
| 通过 | **298**（本轮 296 -> 298） |
| 失败 | **9**（本轮 11 -> 9） |
| 前置缺失类失败 | 0；把实例卡死 0；幽灵注册 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41（未改源码） |
| 新增 | `_audit/diag_sourceurl_breakpoint.py`、`diag_breakpoint_e2e.py`、`fix_bp_inject_reinstall.py`、`read_ledger_notes.py` |

### 111.6 仍未做（下一轮）

- 111.4 的两条（`return_value` 需原始 CDP 对照；`set_variable` 需更稳健的前置）。
- 能力面 VIP 控制器缺口分析（已派只读复核，`_audit/_vip_gap_analysis.md`）。
- 台账剩 6 个"跳过项"未入账。
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
