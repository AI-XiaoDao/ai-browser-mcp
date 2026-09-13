# -*- coding: utf-8 -*-
"""对 A 组疑似项做"原文字面量"取证: 该参数名作为字符串字面量在全工程出现过吗?
若连字面量都没有 → 铁证: 源码从不读该参数。
若出现 → 打印出现位置, 人工判断是否属于该工具的处理链。"""
import io, os, re, sys, json
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
TXT, LN = {}, {}
for f in PROJ:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        t = io.open(p, encoding="utf-8").read()
        TXT[f] = t
        LN[f] = t.split("\n")

d = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "_param_audit.json"), encoding="utf-8"))

print("=" * 100)
print("A 组逐条原文取证 — 参数名是否作为字符串字面量出现过")
print("=" * 100)

summary = {"no_literal": [], "literal_elsewhere": []}
for name, keys, sf, sl in d["ignored"]:
    print()
    print("【%s】" % name)
    for k in keys:
        lit = '"%s"' % k
        hits = []
        for f, t in TXT.items():
            for i, l in enumerate(LN[f]):
                if lit in l and not l.strip().startswith("#"):
                    hits.append((f, i + 1, l.strip()))
        if not hits:
            print("   %-14s 字面量 %s 全工程 0 次  → ★铁证真缺陷" % (k, lit))
            summary["no_literal"].append((name, k))
        else:
            print("   %-14s 字面量出现 %d 次:" % (k, len(hits)))
            for f, i, l in hits[:4]:
                print("        %s:%d  %s" % (f, i, l[:110]))
            summary["literal_elsewhere"].append((name, k, len(hits)))

print()
print("=" * 100)
print("汇总")
print("=" * 100)
print("  ★铁证真缺陷 (参数名全工程无字面量): %d 项" % len(summary["no_literal"]))
for n, k in summary["no_literal"]:
    print("      %-40s %s" % (n, k))
print()
print("  ? 字面量存在但不在我的读取覆盖内 (需人工判定): %d 项" % len(summary["literal_elsewhere"]))
for n, k, c in summary["literal_elsewhere"]:
    print("      %-40s %-14s 出现 %d 次" % (n, k, c))
