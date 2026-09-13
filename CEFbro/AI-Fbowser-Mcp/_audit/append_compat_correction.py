# -*- coding: utf-8 -*-
"""在 _audit/_cdp_param_compat.md 末尾追加"主代理实测更正"节。

必要性: 该审计的 AT RISK 前 5 条中已有 4 条被本机实测推翻(A1/A2 是真缺陷但机理不同、
A3 安全、A4 恰好相反、A5 字段名无误)。若只在报告里更正而不同步该文档,
下一轮读该文档的人(或子代理)会照着错清单去"修"本来正确的代码。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, '_audit', '_cdp_param_compat.md')

SEC = """
---

## 6. 主代理实测更正（同会话真实 MCP 调用；以此节为准）

> 本节由主代理用 `browser_cdp_call`（同步返回内核原始报错）逐条核验 §1.1 的 AT RISK 清单后追加。
> **§1.1 的 A1–A5 中已有 4 条被实测推翻**；§1.1 保留作"当时为何怀疑"的过程记录，不再作为结论。
> 复现脚本：`_audit/probe_cdp_param_names.py`、`_audit/probe_intercept_shape.py`、`_audit/probe_profiler_lifecycle.py`。

### 6.1 总闸结论：本机**忽略未知字段**

探针 `Debugger.setSkipAllPauses {"skip":true,"__mcp_probe_unknown_field":1}` → `{}`

⇒ 凡"多传了一个 PDL 里没有的字段"这一类风险**整体不成立**。
直接后果：A3（`runImmediately`）、A5（`maxDepth`）、`allowTriggeredUpdates`、`executionContextName`
**全部降级为安全**——这正是 §2 建议的 P-0 探针所要的答案。

### 6.2 逐条更正

| 条目 | 静态判定 | **实测结论** | 证据（内核原始返回） |
|---|---|---|---|
| A1/A2 `Network.setRequestInterception` | 方法可能已不存在 / 空参必失败 | **方法存在**，但**两种形状都发错了** → 已修复 | `{}` → `Failed to deserialize params.patterns - BINDINGS: mandatory field missing at position 8`；`{"patterns":["*"]}` → `... patterns - CBOR: map start expected at position 25`；`{"patterns":[{"urlPattern":"*","requestStage":"Request"}]}` → `{}`；`{"patterns":[]}` → `{}` |
| A3 `Page.addScriptToEvaluateOnNewDocument` | `runImmediately` 是新字段，可能被拒 → preload 100% 失效 | **两臂都被接受**，`runImmediately` 安全 | `{"source":"void 0"}` → `{"identifier":"1"}`；`{"source":"void 0","runImmediately":true}` → `{"identifier":"2"}` |
| A4 `DOMDebugger.setInstrumentationBreakpoint` | 疑与 `Debugger.*` 同族改名，应为 `instrumentation` | **恰好相反**：该命令要的就是 `eventName`，旧代码**本来就是对的** | `{"eventName":"setTimeout"}` → `{}`；`{"instrumentation":"setTimeout"}` → `Failed to deserialize params.eventName - BINDINGS: mandatory field missing at position 35` |
| A5 `Profiler.setSamplingInterval` | `maxDepth` 非该命令字段 | 字段名**无误**（未知字段被忽略）；但顺带查出**更严重的真缺陷**：该工具族漏调 `Profiler.start` | `{}` → `Failed to deserialize params.interval - BINDINGS: mandatory field missing at position 8`；`{"interval":100}` → `{}`；`{"interval":100,"maxDepth":32}` → `{}` |
| A6 `executionContextName` | 低危 | 未单独实测（总闸已覆盖该风险类型） | — |
| U-1「内核版本自相矛盾」 | 疑本机是旧内核 | **已定案：内核确为 Chromium 135**。旧参数名是本 CEF 构建的定制，**不是版本差异** | UA-CH 回读基线：`fullVersionList: Chromium 135.0.7049.115`、`platformVersion: 19.0.0` |

### 6.3 本轮由该审计**直接产出**的两个真实缺陷（已修复并验收）

1. **`browser_reverse_network_intercept`**：`enable` **两条路径 100% 失效**（见 6.2 A1/A2），
   且因走 `执行逆向CDP命令` 而**报 success**。已改为纯文本拼接对象数组 + `执行CDP并同步等待`；
   缺 `url_pattern` 时**明确失败**（刻意不默认「拦截全部」：本项目没有放行通道，会把页面挂死）。
   验收 `_audit/verify_network_intercept.py` **4/4**（含"匹配模式确实把导航挂住"的行为臂）。
2. **`browser_reverse_profile`**：`start`/`start_precise` 只调 `Profiler.enable`，**采样从未开始**；
   `stop` 的内核错误被吞、profile 被丢弃。已补 `Profiler.start`、改同步并回传截断标注的 profile。
   验收 `_audit/verify_profiler_lifecycle.py` **4/4**（取回 2992 字符真实 profile）。

### 6.4 仍然成立的结论（请保留）

- **§0.1-2 完全成立**：`执行逆向CDP命令` 吞参数错误 → 走它的工具"参数错也报成功"。
  这正是上面两个缺陷长期不可见的**根因**。台账里这 9 个工具的 `pass` 只是 `_async` 回执，
  **不能**作为"参数被接受"的证据。
- **风险必须逐命令实测**，不能按域、更不能按版本批量推断——本轮 A1/A4 一正一反即为反例。
"""


def main():
    data = open(DOC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '不应有BOM'
    text = data.decode('utf-8')
    if '## 6. 主代理实测更正' in text:
        print('已存在第 6 节, 跳过')
        return 0
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s, 原文行数 %d' % ('CRLF' if nl == '\r\n' else 'LF', text.count('\n') + 1))
    body = SEC.replace('\n', nl) if nl == '\r\n' else SEC
    if not text.endswith(nl):
        body = nl + body
    open(DOC, 'wb').write((text + body).encode('utf-8'))
    print('已追加; 新行数 %d' % (text.count('\n') + body.count('\n') + 1))
    return 0


sys.exit(main())
