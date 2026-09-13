# -*- coding: utf-8 -*-
"""对 param_audit 的 A 组疑似项逐条取证:
把每个 (工具, 参数名) 在全工程范围内的"读取点"全部列出来 (含读取对象变量名),
据此人工判定: 真缺陷 / 我的覆盖不全(误报)。"""
import io, os, re, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import SRC
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

PROJ = ["main.wsv", "MCP_Server.wsv", "MCP_Stdio.wsv", "MCP_BrowserEvents.wsv",
        "MCP_Callbacks.wsv", "MCP_Server_VIP.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_Core.wsv", "MCP_Server_Form.wsv", "MCP_Server_System.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv",
        "MCP_Server_Utils.wsv", "MCP_Server_Reverse.wsv", "MCP_Kernel.wsv"]
TXT = {}
for f in PROJ:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        TXT[f] = io.open(p, encoding="utf-8").read()

d = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "_param_audit.json"), encoding="utf-8"))

# 任意对象变量的读取 (不限对象名)
ANYREAD = r'yyjson取(?:文本|整数|小数|逻辑|逻辑_默认|数组|对象|文本_默认)\s*\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*,\s*"%s"'

print("=" * 100)
print("A 组疑似项逐条取证")
print("=" * 100)
for name, keys, sf, sl in d["ignored"]:
    print()
    print("─" * 100)
    print("工具 %s   (注册于 %s:%d)" % (name, sf, sl))
    print("─" * 100)
    for k in keys:
        pat = re.compile(ANYREAD % re.escape(k))
        hits = []
        for f, t in TXT.items():
            for m in pat.finditer(t):
                ln = t[:m.start()].count("\n") + 1
                hits.append((f, ln, m.group(1)))
        if not hits:
            print("  %-14s 全工程无任何 yyjson 读取点  → 真缺陷 (schema 声明但源码从不读)" % k)
        else:
            objs = sorted(set(h[2] for h in hits))
            print("  %-14s 读取点 %d 处, 对象变量: %s" % (k, len(hits), ", ".join(objs[:6])))
            for f, ln, o in hits[:3]:
                print("                 %s:%d  读取自 <%s>" % (f, ln, o))
