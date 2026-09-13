# -*- coding: utf-8 -*-
"""追加报告第 113 节(第97轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 113. 第97轮：`set_variable` 根因是我猜错的那个 —— 它用了**另一套**暂停解析器"
        "（重复实现），改用共享主解析器后通过；台账**通过数达 300**")

SECTION = """

---

%s

### 113.1 先更正上一轮的假设（我又猜错了一次）

§112.3 我判断 `browser_reverse_set_variable` 拿不到帧，是因为
"我配的 `flow` 前置在构造自己的响应时把那條 `Debugger.paused` 事件**取走并清除**了"。
**这个解释是错的**，而我本可以更早发现：`browser_reverse_return_value` 用的是**完全相同的前置链**
（enable -> inject -> flow{resume:false}），它却**通过了**。同一前置、一个通过一个失败 ——
矛盾本身就说明问题不在前置，而在两个工具各自的代码。

### 113.2 真正的根因：它用了**另一套**暂停摘要解析器

`set_variable` 取帧的代码（`MCP_Server_Reverse.wsv:1279` 附近）调用的是：

```volcano
svSum = MCP命令服务器.从Debugger暂停文本构建摘要 (svPaused)
```

而**其它所有调试器工具**（`evaluate`（含我做过的零前置路径）/ `flow` / `inspect` / `auto`）
用的都是 `解析Debugger暂停摘要`。两套并存，且前者的第一步是：

```volcano
text = 解包CDPDevTools事件JSON (源JSON)
如果 (text == "") { 返回 ("{}") }        // 解包失败 -> 直接空摘要
```

解不出来就返回 `"{}"`（注意它产出的 JSON 里还带 `"_fallback":true` 标记，即它本来就是**兜底**路径），
于是 `call_frame_id` 恒为空 -> 工具必然报
`无法从暂停事件取到 call_frame_id | 请显式传 call_frame_id`。

**修法：改用与其它工具相同的共享主解析器**（`解析Debugger暂停摘要`）。台账随之
**fail -> pass（0.04s，真在断点帧上改写了变量）**。

这条同时是 **D 线"不重复造轮子"的一个实例**：同一个"从暂停事件取帧"的语义存在两份实现，
其中一份在本机事件格式下退化成空，另一份正常 —— 保留一份即可，且应当保留被多数工具验证过的那一份。

### 113.3 方法论：**用"通过的同族工具"当对照**定位问题

这轮真正的转折点是注意到"同一前置下 `return_value` 通过、`set_variable` 失败"。
在此之前我两次（§111.4 / §112.3）都在**前置链**上找原因，方向都错了。
**同族工具在相同前置下一个通一个不通 -> 差异必然在被测工具自身的代码里**，
这比继续推理前置更快也更确定。下一轮遇到同类分歧，优先做这种对照。

### 113.4 台账：通过数达到 **300**

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测（另 6 个危险项已受控实测） |
| **通过** | **300**（本轮 299 -> 300） |
| **失败** | **7**（本轮 8 -> 7） |
| 失败性质 | PARAM 2 / TARGET 2 / OTHER 2 / GUARD 1 |
| 前置缺失类失败 | **0**；`CAPABILITY` 0；把实例卡死 0；幽灵注册 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 本轮修复 | 1 个"必然失败"的真缺陷（用了残缺的重复解析器） |

剩下的 7 条失败都属允许类别（参数非法 / 目标不存在 / 显式确认闸 / 其它且可行动），
例如 `browser_find_by_hwnd`（句柄是运行时值，无法预置；消息已给出取得方式）。

### 113.5 仍在进行 / 下一轮

- **CDP 参数名兼容性普查**（只读复核在跑，产物 `_audit/_cdp_param_compat.md`）：
  本轮之前的 `setReturnValue` 说明本机内核用的是**旧协议参数名**，故系统排查"项目各处手拼的
  CDP params 是否有新协议名"—— 这是同一缺陷类的横向清理。
- 能力面 VIP 控制器缺口分析（`_audit/_vip_gap_analysis.md`）。
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
