# -*- coding: utf-8 -*-
"""找出"恒失败/已禁用"的工具分支 —— 这些必须在描述里警告 AI"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

PAT = re.compile(r"命令失败\s*\(.{0,200}?(不支持|已禁用|已废弃|恒失败|不支持该|不支持此)")
hits = []
for f in FILES:
    ls, _ = lines_of(f)
    for i, l in enumerate(ls):
        if classify(l) == "EMBED":
            continue
        code = re.sub(r"//.*$", "", l)
        if not PAT.search(code):
            continue
        own = "?"
        for k in range(i, 0, -1):
            m = re.search(r'方法名\s*==\s*"([A-Za-z0-9_]+)"', ls[k])
            if m:
                own = m.group(1); break
        hits.append((f, i + 1, own, l.strip()[:110]))

print("恒失败/已禁用的工具分支: %d 处" % len(hits))
for f, n, own, t in hits:
    print("  %-24s:%-6d %-42s" % (f, n, own))
    print("        %s" % t)

# 对照: 这些工具在工具表里的描述
srv = lines_of("MCP_Server.wsv")[0]
names = set(o for _, _, o, _ in hits if o != "?")
print()
print("=== 它们在 tools/list 里的描述 ===")
for i, l in enumerate(srv):
    m = re.search(r'添加工具JSON\s*\(\s*"([^"]+)"\s*,\s*"([^"]*)"', l)
    if m and m.group(1) in names:
        warn = "✅有警告" if ("禁用" in m.group(2) or "不支持" in m.group(2) or "已废弃" in m.group(2)) else "❌无警告"
        print("  %-42s %-8s %s" % (m.group(1), warn, m.group(2)[:70]))
