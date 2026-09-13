# -*- coding: utf-8 -*-
r"""第131轮收尾: 报告 ## 151 + `_gap_verified.md` 补第131轮进展(含"全量 MISSING=0"里程碑)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 151. 第131轮：**全量 323 工具**的"实现读却代理看不到"参数清零（20 个参数 / 12 个工具）

### 151.1 先把尺子修准，再全量量一遍
上一轮的 `_audit/_show_branch_params.py` 又暴露两个自身缺陷，都已修：
1. **花括号配平必须跳过字符串字面量**：分支体里内嵌 JS（`"(function(){...})()"`）时，字符串里的 `{}`
   会把分支切到几十行之外 —— 实测把 `browser_debugger_script_source` 误报出 **60 多条假 MISSING**；
2. **不给工具名时默认全量扫**（此前传空前缀会扫 0 个，静默给出"没问题"的假结论）。

修好后跑 `--brief`（全量）：**323 个工具，有差异 48 个**，其中
**MISSING（实现读了却代理看不到）= 12 个工具 / 20 个参数**，其余 36 个是 EXTRA（声明了但分支体没读到）——
后者绝大多数是**委托给共享助手**读取造成的（`debugger_flow`→`执行Debugger断点流程JSON`、`kernel_reactor`→`分派_反应器`…），
属扫描器已知局限，**不动**。

### 151.2 本轮补齐的 20 个参数（类型全部由实现的读取函数判定）
| 工具 | 补上的参数 |
|------|-----------|
| `browser_back` / `browser_forward` | `wait_for_load`、`async_only`（这两个工具**原本连 schema 都没有**） |
| `browser_reload`、`browser_navigate` | `async_only` |
| `browser_cdp_event` | `event`（与 `event_name` 等价，实现两者都读） |
| `browser_console_eval` | `file`（**从文件读脚本** —— 同时也是绕开 HTTP 通道 ~1MB arguments 限制的手段） |
| `browser_file_dialog` | `file_path`、`path`（该工具此前也没有 schema） |
| `browser_intercept` | `width`、`height`、`x`、`y`（`popup_config` 的几何参数） |
| `browser_reverse_extract` | `script_id` |
| `browser_reverse_instrument_script` | `verify`（它自己的描述里就提到 `verify:false` 关自检，却没声明这个参数） |
| `browser_reverse_websocket` | `requestId`（CDP 原生拼写别名） |
| `mcp_help` | `name`、`tool`（**查单个工具的详细说明** —— 此前这个用法代理看不到） |

### 151.3 验收（`_audit/verify_round131.py`，9/9）
- **穷尽性**：重跑全量扫描 —— **MISSING = 0**（用"发现问题的同一把尺子"证明问题消失，比逐条断言更有力）；
- 行为层抽样：`console_eval {file:…}` 真从文件读到脚本并执行（`FILE_JS_OK`）、`mcp_help {name:…}` 返回单工具说明、
  `navigate {async_only:true}` 立刻返回成功。

### 151.4 本轮又踩到两个坑（都记下来了）
1. **补 schema 要先看用的哪个 helper**：`browser_cdp_event`/`browser_console_eval` 用的是 `单参数Schema文本`，
   而我的通用插入按"行尾最后一个实参"定位属性列表，结果把属性表达式塞进了**描述字符串内部** ——
   编译通过、快检全过，但**运行时 schema 里没有新参数**（全量扫描因此仍报 2 条 MISSING）。
   整行重写为 `多属性Schema文本` 才修好。教训：**改完必须用 `tools/list` 复核**（这条已在第127轮记过一次，本轮再次验证）。
2. **描述不能想当然**：我给 `async_only` 写的是"true=立刻返回 task_id"，实测 `navigate {async_only:true}`
   回的是 `已导航到: …`（**不等载入、立刻返回成功，不返回 task_id**）—— 已按实现改正。
   这也说明"探针的期望值必须来自实现或真机，不能来自直觉"。

### 151.5 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
**系统性结论：全量 323 个工具中，"实现读却未声明"的参数已为 0**（可随时用
`py -3 _audit\\_show_branch_params.py --brief` 复跑复核）。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 151.' in text:
        text = text[:text.index('## 151.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第131轮进展**'
    old = '> **第130轮进展**'
    add = (mark + '：**全量 323 工具扫描 → MISSING(实现读却未声明) 清零**：12 个工具共 20 个参数补齐'
           '（back/forward 的 wait_for_load+async_only、cdp_event 的 event、console_eval 的 file、'
           'file_dialog 的 file_path/path、intercept 的 x/y/width/height、reverse_extract 的 script_id、'
           'instrument_script 的 verify、reverse_websocket 的 requestId、mcp_help 的 name/tool）。'
           '扫描器同时修了两个自身缺陷（花括号配平要跳过字符串、空前缀要全量扫）。验收 9/9，'
           '其中"重跑全量扫描 MISSING=0"是穷尽性证明。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第131轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
