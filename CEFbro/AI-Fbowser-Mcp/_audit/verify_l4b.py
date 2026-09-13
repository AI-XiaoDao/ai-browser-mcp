# -*- coding: utf-8 -*-
import io, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
core = io.open(os.path.join(SRC, "MCP_Server_Core.wsv"), encoding="utf-8").read().split("\n")

print("=" * 100)
print("L4b 三处候选的实际代码 (判断 0 是否被赋予了 schema 之外的语义)")
print("=" * 100)
for tag, a, b in [("set_breakpoint.line", 4208, 4220),
                  ("wait_paused.max_ms", 4384, 4392),
                  ("debugger_auto.max_ms", 4530, 4538)]:
    print("--- %s ---" % tag)
    for k in range(a - 1, min(b, len(core))):
        print("%6d| %s" % (k + 1, core[k].strip()[:140]))
    print()

print("=" * 100)
print("对照: 前任报告 §3.3 认定的真缺陷模式 (schema 中 0 有独立含义)")
print("=" * 100)
srv = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
for i, l in enumerate(srv):
    for key in ["duration_ms", "form_index"]:
        if '"' + key + '"' in l and "属性项JSON" in l:
            m = re.search(r'属性项JSON\s*\(\s*"' + key + r'"\s*,\s*"[^"]*"\s*,\s*"([^"]*)"', l)
            print("   %6d| %-14s %s" % (i + 1, key, m.group(1) if m else "?"))

print()
print("=" * 100)
print("L2b 中 browser_fill_select 的实际代码 (对照前任 §3.5 的 6 处)")
print("=" * 100)
form = io.open(os.path.join(SRC, "MCP_Server_Form.wsv"), encoding="utf-8").read().split("\n")
for k in range(264, 280):
    print("%6d| %s" % (k + 1, form[k].strip()[:150]))
