# -*- coding: utf-8 -*-
r"""第128轮收尾: 报告 ## 148 + `_gap_verified.md` 第四节补第128轮进展。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 148. 第128轮：内核族两处"静默假成功"修复 + 幽灵工具 `browser_debugger_pause` 从"看不见"变为"看得见的守卫"

### 148.1 `browser_kernel_scheme action=register`：空内容也回 success（已修）
原实现（`MCP_Kernel.wsv:411-416`）只在"`body` 为空**且** `file` 存在"时才读文件，于是：
- `file` 路径**写错/不存在** → 被**静默忽略** → 注册出一个**空内容**方案，却回 `success`；
- `data` 与 `file` **都不给** → 同样注册空方案 + `success`。
调用方会以为"内容已挂上"，而页面拿到的是空文档 —— 典型的静默假成功。

修法：`file` 给了但不存在 → 明确报错（附绝对路径要求）；读回为空 → 报错；两者都不给 → **拒绝注册**。
验收（本机临时文件当预言机）：`data/file 都不给 → 拒绝`、`file 不存在 → 拒绝`、`file 存在 → 成功(20 字符)`、
`data 直接给 → 成功(10 字符)` 四条全通过。

### 148.2 `browser_kernel_ipc_clear` / `browser_kernel_ipc_queue`：action 语义静默退化（已修）
工具描述写"action 必填且只能为 clear"，但实现（`MCP_Kernel.wsv:544-554`）**不校验**：
- `browser_kernel_ipc_clear` 不传 `action` → 落到默认分支**读取队列**并回 `success`（调用方以为已清空，实际什么都没清）；
- 未知 `action`（如拼错的 `cleer`）→ 同样静默退化为读取 + `success`。

修法：工具名为 `browser_kernel_ipc_clear` 且未给 `action` 时按 `clear` 处理；未知 `action` 明确拒绝并列出支持值。
验收：`ipc_clear {}` → `渲染侧IPC队列已清空`；`action=cleer` → `未知 action: cleer | 支持 clear(清空) / queue(读取…)`；
`action=queue` 与空参（ipc_queue）仍照旧读取（回归通过）。

### 148.3 幽灵工具 `browser_debugger_pause`：从"看不见"到"看得见的守卫"
实测（本轮）：`tools/list` 里**没有**它 —— 但按名字直接调用**有效**，返回实现里写好的诚实拒绝
（`Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) | 请用 debugger_flow 一键断点 或 debugger_enable →
set_breakpoint → navigate → wait_paused`）。即：**既不是死代码，也不是可用能力，而是"看不见的守卫"**。
处理（与既有先例 `browser_close_try` 的「⛔ 恒失败 + 指明替代」写法保持一致）：**补上注册行**，让代理一次就能读到
"为什么不能这么做 + 该怎么做"。工具数 322 → **323**；调用它**仍然按设计拒绝**（未把守卫变成能力）。
台账按"人工受控·行为与设计一致"记 **pass**（与 `browser_close_try` 同做法），故仍为 **320 通过 / 3 刻意设计**。
副作用（正面）：`cleanup_scan.py` 的"刻意的守卫分支"由 3 项降为 2 项 —— 因为它现在是一个**正常注册的工具**了。

### 148.4 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**
（幽灵注册 0；未广告别名 2 与刻意守卫 2 均为已记录的**非缺口**）。
本轮验收：`_audit/verify_kernel_guards.py` **12/12**（同时覆盖幽灵工具可发现性、方案注册守卫、IPC 语义）。
剩余（`_audit/_gap_verified.md` 第四节）：`browser_fingerprint` 的 19 个维度参数、debugger 家族 CDP 原生别名、
`browser_execute_js` 的 `file`/`code_base64`、`workflow_run` 的 steps 字段表、`reverse_websocket query` 语义、
`browser_collect` 的 keyword/limit、公共层参数（`sync_wait`/`async_only`/`browser_id`）声明统一。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 148.' in text:
        text = text[:text.index('## 148.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    old = '> **第127轮进展**'
    mark = '> **第128轮进展**'
    add = (mark + '：已修 `kernel_scheme` 的"空内容也回 success"、`kernel_ipc_clear/queue` 的 action 静默退化（'
           '未知 action 会退化成读取）；幽灵工具 `browser_debugger_pause` 已补注册（322→323），'
           '从"看不见的守卫"变成"看得见的守卫"（调用仍按设计拒绝），台账按人工受控记 pass。'
           '验收 `_audit/verify_kernel_guards.py` 12/12。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第128轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
