# -*- coding: utf-8 -*-
"""补一刀: 上一步只查了**中文方法名**。但项目里有 `@` 开头的内嵌 C++ 片段,
C++ 侧调用的是 `@输出名` 的**英文符号**(例如 TryNavigateWelcomePage)。
英文符号引用同样算"有人用", 必须一并证实零引用才能删。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
FILES = ["main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
         "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
         "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
         "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
         "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv"]

EN = {
    "MCP_Server.wsv:124": "TryRestoreWelcomePageNavigate",
    "MCP_Server.wsv:163": "TryNavigateWelcomePage",
    "MCP_Server.wsv:3606": "CDPGetScriptSource",
    "MCP_Server.wsv:5225": "DispatchNetworkLogCommand",
    "MCP_Server.wsv:7083": "ParseMatchMode",
    "MCP_Server.wsv:7652": "RecordNetworkLogItem",
    "MCP_Server.wsv:7945": "NormalizeURL",
    "MCP_Server.wsv:9413": "SendCORS500Response",
}

lines = []
for f in FILES:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        for i, ln in enumerate(open(p, 'rb').read().decode('utf-8').split('\n'), 1):
            lines.append((f, i, ln))

print('%-26s %-32s %s' % ('位置', '英文符号', '出现处(除定义行)'))
print('-' * 100)
for loc, sym in EN.items():
    f0, l0 = loc.split(':')
    l0 = int(l0)
    hits = [(f, i) for f, i, ln in lines if sym in ln]
    other = [h for h in hits if not (h[0] == f0 and h[1] == l0)]
    at_hits = [(f, i) for f, i, ln in lines if sym in ln and ln.lstrip().startswith('@')]
    print('%-26s %-32s %s' % (loc, sym, other if other else '无 -> 可删'))
    if at_hits:
        print('     注意: 出现在 @ 行: %s' % at_hits)
