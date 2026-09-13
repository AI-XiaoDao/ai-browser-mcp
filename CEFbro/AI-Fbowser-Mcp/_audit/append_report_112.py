# -*- coding: utf-8 -*-
"""追加报告第 112 节(第96轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 112. 第96轮：`browser_reverse_return_value` **必然失败**的根因 —— 本机要旧协议参数名 "
        "`newValue`（不是新版 CDP 的 `result`）")

SECTION = """

---

%s

### 112.1 用**内核原文**定位，而不是继续读自己的代码

§111.4 记录：`browser_reverse_return_value` 的前置三步全 OK（页面确实停在断点上），
却报 `Debugger.setReturnValue 失败: Invalid parameters`；而代码构造的参数
`{"result":{"value":…}}`（`MCP_Server_Reverse.wsv:1239`）**与当前 CDP 规范一致**。
光读自己的代码看不出问题，于是做**原始 CDP 对照**（绕过工具封装，同一暂停帧）：

```
browser_cdp_call Debugger.setReturnValue  params={"result":{"value":true}}
-> {"code":-32602,"message":"Invalid parameters",
    "data":"Failed to deserialize params.newValue - BINDINGS: mandatory field missing at position 31"}
```

**内核自己把字段名说出来了：它要 `newValue`。** 本项目发的是 `result` —— 于是该工具**恒定失败**。

### 112.2 三形状对照（同一暂停帧，原始 CDP）

| 参数形状 | 结果 |
|---|---|
| `{"newValue":{"value":true}}` | **成功 `{}`** ✔ 采用 |
| `{"newValue":true}` | `Failed to deserialize params.newValue - CBOR: map start expected`（说明 newValue 必须是**对象**） |
| `{"result":{"value":true}}`（原实现） | `mandatory field missing at position 31` |

修改：`rvParams = "{\\"newValue\\":{\\"value\\":" + rvValue + "}}"`，并在源码里写明这段实测依据。
台账随之 **fail -> pass（0.04s，真命中断点帧）**。

**这是一类反复出现的差异，不是孤例**：本项目自己早就记过一例 ——
`Debugger.setInstrumentationBreakpoint` 在本机要旧协议的 `instrumentation`，而不是新版 `eventName`。
本机 CEF 的内核绑定用的是**旧协议参数名**，遇到"参数看起来完全正确却报 Invalid parameters"时，
应当优先怀疑这一层，并用 `browser_cdp_call` 把内核原文问出来。

### 112.3 `browser_reverse_set_variable` 仍未通过 —— 机理已查明

它的失败是 `无法从暂停事件取到 call_frame_id`。机理：我为它配的前置是
`flow {resume:false}`（停在断点上、不 resume），而 **`flow` 在构造自己的响应时就把那条
`Debugger.paused` 事件取走并清除了**；等被测工具运行时，事件日志里已经不剩 paused 记录，
于是它拿不到帧 ID。

**修法方向（下一轮，二选一）**：
① 让 `set_variable` 在"事件日志无 paused"时**回退到活帧获取**（与 `evaluate` 的 E1 同源逻辑）；
② 或换一个"停住但不消费事件"的前置。
这一条属**前置链设计问题**，不该算在被测工具头上 —— 与 §111.4 记的判断一致。

### 112.4 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测 |
| 通过 | **299**（本轮 298 -> 299） |
| 失败 | **8**（本轮 9 -> 8） |
| 失败性质 | PARAM 2 / TARGET 2 / GUARD 2 / OTHER 2 |
| 前置缺失类失败 | **0**；`CAPABILITY` 0；把实例卡死 0；幽灵注册 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 本轮修复 | 1 个"必然失败"的真缺陷（参数名）+ 2 个"测不了"的工具转实测通过（§111） |
| 新增 | `_audit/diag_setreturnvalue_ab.py`、`diag_setreturnvalue_paramname.py` |

### 112.5 仍未做（下一轮）

- 112.3 的 `set_variable` 前置链修法。
- 能力面 VIP 控制器缺口分析（只读复核 `_audit/_vip_gap_analysis.md` 在跑）。
- 台账剩 6 个"跳过项"未入账（已受控实测）。
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
