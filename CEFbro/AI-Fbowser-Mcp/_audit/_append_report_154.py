# -*- coding: utf-8 -*-
r"""第134轮收尾: 报告 ## 154 + `_gap_verified.md` 补第134轮进展。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 154. 第134轮：`file` 参数报错误导 + `code_base64` 未声明（"能用但把人带沟里"的一类缺陷）

### 154.1 实测过程与定性
先按"它是不是没实现"去测：`browser_execute_js {file: <临时目录里的 .js>}` → 报
`缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径)`（**好像没传参数**）。
但源码里 `解码JS代码` 明确有 file 分支，只是它带安全守卫 `验证安全路径 (code, 真)`。
于是做**对照实验**（`_audit/probe_exec_file_scope.py`）：

| 用法 | 结果 |
|------|------|
| `file` = **运行目录内**（exe 所在目录）的 .js | ✅ 正常执行（`RUN_DIR_FILE_OK:5`，`browser_evaluate` 同样） |
| `file` = 运行目录外（`C:\\Windows\\notepad.exe` 或 `%TEMP%`） | ❌ 报"缺少参数: 请提供 code 或 file" |
| `code_base64` | ✅ 正常执行（源码里既有的免转义通道，**但两个工具的 schema 都没声明它**） |

⇒ 定性：**功能是实现了的**，缺陷在**失败文案误导**（调用方明明给了 `file`，却被回一句"没给参数"，
于是会去换方法反复试错 —— 这正是本目标要消灭的体验），以及 `code_base64` **不可发现**。

### 154.2 修法（两处文案 + 两处 schema，均在本轮验收）
1. Core 里那条误导报错有**两处**（execute_js 与另一个 JS 工具），都改为可行动版本：
   列出三种传法（`code` / `code_base64` / `file`）、点明 **file 仅允许进程运行目录内的文件**、
   并给出改法（把脚本放进运行目录，或改用 `code`/`code_base64`）、提醒文件必须存在且非空；
2. `browser_execute_js` 与 `browser_evaluate` 的 schema 各补声明 **`code_base64`**，
   并把 `file` 的描述补上"仅限运行目录内"这一**真实约束**。

### 154.3 验收（`_audit/verify_round134.py`，8/8）
- 目录外 `file` 仍被拒绝（安全守卫保留），且报错**点明限制、列出三种传法、给出改法**；
- `code_base64` 已在两个工具的 `tools/list` 里可见**且真能执行**（`B64_VERIFY:16`）；
- 运行目录内 `file` 仍正常（回归：`RUNDIR_OK:10`）。

### 154.4 为什么这类缺陷值得单独立一条
本项目已修过"声明了却没实现"（no-op 参数）、"实现支持却没声明"（代理看不到）；
本轮是第三种：**实现正确、声明正确，但失败路径把人引向错误结论**。
三种都属于"一次调用成功"的敌人，检查方式也不同 ——
前者要靠 `_show_branch_params.py --diff --closure`，后者要靠**对着文档真跑一遍**（本轮就是这么做才发现的）。

### 154.5 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 154.' in text:
        text = text[:text.index('## 154.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第134轮进展**'
    old = '> **第133轮进展**'
    add = (mark + '：`browser_execute_js/evaluate` 的 `file` **实测可用但失败文案误导** —— 目录外路径会被安全守卫拒绝，'
           '却报"缺少参数: 请提供 code 或 file"（调用方以为没传参）；已改为可行动报错（列出 code/code_base64/file 三种传法'
           '+ 点明"file 仅限进程运行目录内" + 给出改法）。同时把源码里既有但**未声明**的 `code_base64` 补进两个工具的 schema'
           '（免转义通道，适合含引号/换行/超大脚本）。验收 8/8。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第134轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
