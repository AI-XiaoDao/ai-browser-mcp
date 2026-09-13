# -*- coding: utf-8 -*-
r"""第130轮收尾: 报告 ## 150 + `_gap_verified.md` 补第130轮进展。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 150. 第130轮：把"声明了却从不读"的参数变成真的 + 三个工具的 schema/语义补齐（全部用测量件驱动）

### 150.1 先修测量件本身
上一轮做的 `_audit/_show_branch_params.py` 在 `MCP_Server_Reverse.wsv` 上**切错了分支**（把 `browser_reverse_websocket`
切成 2 行）。根因：该文件的行是**隔行留空**的，`否则 (方法名 == ...)` 的 `{` 在**下一行**，而我的配平从匹配行就开始计数，
于是还没进块 `depth` 就已经是 0。已修为"**先等到第一个 `{` 再开始配平**"；修完后同一工具量出 69 行、
并立刻暴露了它真正读的参数（`action`/`request_id`）—— **尺子不准，结论就全错**，这条经验值得记住。

### 150.2 `browser_get_text.max_chars`：从"声明未读"变成"真的生效"
测量件判定它是 `DECLARED_UNUSED`（schema 声明、实现从不读），源码核实截断处写死
`MCP_常量.截断_源码默认字节`（Core:629）。已改为：读 `max_chars` → 非法值/超上限回退默认（沿用 `view_source` 的既有写法）。
验收（真机）：不带参数取全文 5131 字；`max_chars=50` → 回包 `truncated_to=50` 且正文长度 **正好 50**；
`max_chars=999999999` → 回退默认且不报错。

### 150.3 `browser_debugger_set_breakpoint`：补齐 CDP 原生别名
测量件显示它读 `column/column_number/line/line_number/url`，而 schema 只有 `column/line/url`
⇒ 照抄 CDP 文档写 `line_number` 的调用方会以为参数被忽略。已补声明两个别名并注明"实现会读"。

### 150.4 `workflow_run`：入口四选一 + steps 字段表（**用真跑一遍证明文档与实现一致**）
- 测量件显示实现读 `name`/`file`/`definition`/`steps`/`on_error`，而 schema **只声明 name 且把 name 标成必填**
  ⇒ 用 `file`/`definition`/`steps` 的调用方在 schema 层面就被误导。已补 `file`、并把 required 清空（入口四选一）。
- steps 每步字段**从源码逐条核实**（`skip` / `delay_ms` / `tool|name` / `args|arguments` / `wait_async` /
  `max_ms` / `on_error`）后写进描述；
- 验收：真跑一个 3 步内联工作流 → 回包 `total_steps=3, success_count=3, failure_count=0`
  （文档里写的字段确实能用，而不是"描述好看"）。

### 150.5 `browser_reverse_websocket`：文实不符 + 必填参数不可见
测量件显示它读 `action`/`request_id`（另有 `requestId` 写法），schema 只有 `action`；且源码 863 行显示
`action=query` 实际调用的是 **`Network.getResponseBody`**（取某条请求的**响应体**），而旧描述把 query 也说成
"监听所有 WS 帧" —— 调用方会以为拿到解码后的 WS 帧。已补声明 `request_id` 并把两个 action 的真实语义分开写清。
验收：`action=query` 缺 `request_id` 时给可行动错误（`query 需要 request_id (从Network.requestWillBeSent事件获取)`）。

### 150.6 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
本轮验收：`_audit/verify_round130.py` **12/12**（四条全部含行为层证据，不只是查 schema）。
剩余：debugger 家族其余 CDP 别名、`browser_execute_js` 的 `file`/`code_base64`、`browser_fingerprint_*` 各子工具的
逐参数复核（本轮方法已可一键复跑：`py -3 _audit\\_show_branch_params.py --diff <工具名…>`）。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 150.' in text:
        text = text[:text.index('## 150.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第130轮进展**'
    old = '> **第129轮进展**'
    add = (mark + '：`browser_get_text.max_chars` 由"声明未读"改为**真的截断**（实测 truncated_to=50）；'
           '补 `set_breakpoint` 的 `line_number/column_number`、`workflow_run` 的 `file` 与 **steps 字段表**'
           '（真跑 3 步内联工作流验证 total_steps=3）、`reverse_websocket` 的 `request_id` 并把 query 的真实语义'
           '（Network.getResponseBody，**不是**解码后的 WS 帧）写清；修好测量件 `_show_branch_params.py` 的分支匹配'
           '（隔行留空的文件会切错）。验收 12/12。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第130轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
