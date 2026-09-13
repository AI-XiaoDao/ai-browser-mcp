# -*- coding: utf-8 -*-
"""追加报告第 108 节(第92轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 108. 第92轮：查清 instrument_script 卡死会话的**机理**，找出唯一可行的恢复动作（并更正 §102 的结论）")

SECTION = """

---

%s

### 108.1 机理（读源码 + 实测双向确认）：自检探针被自己的插装拦住，进而占住 CDP 队列

`browser_reverse_instrument_script` 的 `install` 里有一段**自检探针**（`MCP_Server_Reverse.wsv:969`）：

```volcano
ivProbe = 执行CDP并同步等待 (…, "Runtime.evaluate", "{\\"expression\\":\\"(function(){return 0})()\\"…}", 3000)
```

它想验证"新脚本执行前到底会不会真的暂停"。但此刻刚装上的
**`beforeScriptExecution` 插装恰恰是对"执行脚本"生效的** —— 于是：

1. 探针自己去 `Runtime.evaluate`（执行一段脚本）-> **触发了刚装上的插装**；
2. 页面在脚本执行前暂停 -> 这条 `Runtime.evaluate` **永不返回**；
3. 本项目是**单条 CDP 队列 + 协议锁**（`执行CDP并同步等待` 的同步等待），这条永久 pending 的请求
   **把队列占住** -> 之后所有走 CDP 的工具全部超时；
4. `browser_status` 仍正常（0.02s），因为它是**原生**路径、不经 CDP。

这与实测完全吻合：装入后 `browser_execute_js` 35s 超时、`browser_debugger_last_paused` 超时，
而 `browser_status` 一切正常。

**所以这不是"插装坏了"，而是"探测手段被自己的插装拦住"+"单队列被占"。**

### 108.2 三条候选恢复路径，逐条实测（每轮干净重启）

`_audit/diag_instrument_recovery.py`：

| 恢复动作 | 结果 | 备注 |
|---|---|---|
| `browser_debugger_resume` | **不能恢复** | 30.5s 后 JS 仍 35s 超时 |
| **`browser_reverse_instrument_script action=suppress`** | **能恢复** ✔ | 45.71s，返回体里带 `auto_prepared: "Debugger.resume(页面原卡在断点, 已自动恢复并重试成功)"` |
| `browser_debugger_disable` | **不能恢复** | 30.6s 后 JS 仍超时 |

**关键结论：不需要重启进程** —— `suppress` 就能把 JS 通道救回来，它靠的正是项目既有的
**卡死自救**（等满预算 -> 自动 resume -> **重试一次**）这条链路。

**这更正了我在 §102 的结论**。当时我写的是"`browser_debugger_resume` 与 `action=suppress` **都无法恢复**，
只有重启进程才能恢复"。当时的原始记录是 `suppress -> 45.00s EXC:timed out` ——
而本次实测该调用需要 **45.71s**。也就是说：**那是我客户端的 45s 超时把它掐断了**，
不是产品做不到。**又一次"把客户端超时误当产品失败"。**

### 108.3 我试图把它改快，结果**把它改坏了**（有实测为证，已回退）

看到"恢复要 45s"，我顺手把预算压短（resume 5000ms、setSkipAllPauses 8000ms），想让它几秒内恢复。
实测结果反而是：

```
[browser_reverse_instrument_script] isError=True 38.74s
   setSkipAllPauses 失败: timeout
-> JS 恢复? False
```

原因：这条链路能成功，靠的是**等满预算后自救重试一次**；预算压短后，**重试那次也没等到结果**就放弃了。
已从备份回退（复核：`_sup` 那行恢复为 15000ms，我加的 `_srs` 行为 0 处），
并复测确认**恢复能力回来了**（`suppress -> 能恢复`）。
**教训：不要为了"看起来更快"去压一个正在工作的超时自救链路的预算 —— 先测，再动。**

### 108.4 提示文案按实测更正

`suppress` 成功后的 `note` 原本只写"已跳过全部暂停"。现补上实测事实：
**这是唯一能恢复的动作（约 45s，走卡死自救），`browser_debugger_resume` 与 `browser_debugger_disable` 都不能恢复。**

### 108.5 本轮我自己的又一次"测试失去判别力"

第一次跑恢复测量时，三轮里 `install` **全都被拒绝**了 —— 因为我上一轮给 `install` 加了**确认闸**（§102），
而我的测试脚本**没传 `confirm:true`**。于是插装根本没装上，JS 通道一直是好的，
结果被打成"**三个候选都能恢复**" —— 一个毫无判别力的结论。
是逐行读原始输出时发现 `install 需要显式确认` 才察觉的（**不是**看最后那行汇总）。
**产品契约变了，测试脚本必须跟着改**；而"全都通过"这种过于漂亮的结果应当先怀疑。

### 108.6 本轮指标（仅改 1 处提示 + 1 次回退，未新增能力）

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测 |
| 通过 | **296** |
| 失败 | **11**（OTHER 4 / TARGET 3 / PARAM 2 / GUARD 2） |
| 前置缺失类失败 | **0**；把实例卡死 0；幽灵注册 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `_audit/diag_instrument_recovery.py`（三条恢复路径的对照测量） |

### 108.7 仍未做（下一轮）

- `install` 的**探针本身**是否可改为不触发自己插装的验证方式（例如先 `setSkipAllPauses` 再探针、
  探完恢复）—— 但那会让"是否真的拦截"这个自检失去意义，属设计取舍，需专门设计再验证。
- 台账剩 6 个"跳过项"未入账；`browser_reverse_return_value` / `set_variable` 需真命中断点。
- 陈旧活帧隐患（§101.4）；能力面其余候选缺口（`命令行` 系列、菜单/快捷键 13 项等）。
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
