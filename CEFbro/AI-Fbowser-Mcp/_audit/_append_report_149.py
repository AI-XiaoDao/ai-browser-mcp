# -*- coding: utf-8 -*-
r"""第129轮收尾: 报告 ## 149 + `_gap_verified.md` 第四节补第129轮进展。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 149. 第129轮：指纹/采集两族补齐 21 个未声明参数 + 把"通用参数与 1MB 墙"写进代理最先读到的文案

### 149.1 本轮先做了一个**可复用测量件**，再动手
新增 `_audit/_show_branch_params.py`：按花括号配平切出某工具的**分派分支**，用 7 种读取函数正则抽参数，
并**按读取函数判定类型提示**（`yyjson取整数`→integer、`取文本`→string、`取逻辑`→boolean…），
再与运行时 `tools/list` 的 schema 声明做双向差集（`--diff`）。
它把上一轮三个只读子代理的机械方法固化成**每条命令都能复跑**的工具，避免以后凭印象改 schema。

### 149.2 补齐 21 个"实现真读却代理看不到"的参数
| 工具 | 实现读取（本轮复核） | 原 schema | 补齐 |
|------|----------------------|-----------|------|
| `browser_fingerprint` | 19 个参数（min/max/seed、sample_rate/channels/frames_per_buffer、public_ip/local_ip/host/disable、offset_h/offset_m/name/iana、tls_min/tls_max/ciphers、action/config） | 只有 `action`/`config` | **+17**（类型由读取函数判定，非猜测） |
| `browser_collect` | action/keyword/limit/clear/max_ms | 只有 `action` | **+4**（描述里早就写了 keyword/limit，代理却看不到） |

验收 `_audit/verify_fp_collect_schema.py` **8/8**：声明层（参数真的出现在 `tools/list`）+ 行为层
（`fingerprint action=count`、`collect console_get + keyword/limit` 回归可用；一次性传全部 17 个新参数不报"未知参数"）。

### 149.3 把两条"最该早知道"的事实写进代理最先读到的文案
代理加载 MCP 后最先读到的是 **`initialize` 响应的 `instructions`**（由 `MCP_Server.wsv` 的 `指引` 变量产生），
其次是 `mcp_help`。本轮在两处都补上：
- **所有工具通用参数**：`browser_id` / `max_ms` / `async_only` / `sync_wait` —— 它们由入口统一处理，
  多数工具的 schema 未逐个声明（上一轮审计的结构性发现），不说明就只能靠代理猜；
- **大参数注意**：MCP HTTP 通道在请求体约 1MB 处会被内核直接断连且**没有错误码**，
  大内容请用文件类参数（如 `browser_create_url_request` 的 `body_file`）或 WebSocket/stdio 通道
  —— 这正是第126轮实测出来的传输边界，写在最前面能直接避免"无响应→反复重试"；
- `mcp_help` 另加一句："本列表是**速览**，完整清单（权威）请用 `tools/list`"（该列表是手工维护的常用工具索引，
  并不覆盖全部 323 个工具，此前没有说明这一点）。

验收 `_audit/verify_agent_guidance.py` **8/8**：真调 `initialize` 确认 `instructions` 里含这两段（**不只看源码**
—— 上一轮踩过"改了 schema 但运行时没生效"的坑）；`mcp_help` 文本可解析且含新提示；`tools/list` 仍为 323 个。

### 149.4 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
本轮验收：`verify_fp_collect_schema.py` **8/8**、`verify_agent_guidance.py` **8/8**、
`verify_kernel_guards.py` **12/12**（上轮成果无回退）。
剩余：debugger 家族 CDP 原生别名、`browser_execute_js` 的 `file`/`code_base64`、`workflow_run` 的 steps 字段表、
`reverse_websocket query` 语义、`browser_get_text.max_chars`（声明但未读，需逐点复核后再定去留）。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 149.' in text:
        text = text[:text.index('## 149.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第129轮进展**'
    old = '> **第128轮进展**'
    add = (mark + '：`browser_fingerprint` 补 17 个未声明参数（类型由实现读取函数判定）、'
           '`browser_collect` 补 4 个；把"通用参数(browser_id/max_ms/async_only/sync_wait)"与'
           '"HTTP 通道 ~1MB 会被断连且无错误码"写进 `initialize.instructions` 与 `mcp_help` 提示；'
           '新增可复用测量件 `_audit/_show_branch_params.py`。验收 8/8 + 8/8。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第129轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
