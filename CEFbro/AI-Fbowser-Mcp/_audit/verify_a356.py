# -*- coding: utf-8 -*-
"""核实 A3-B 与 A5-2 的两处候选"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

print("=" * 100)
print("1. MCP_Server_Form.wsv 的分派比较写法 (解释 A3-B 的 9 个 browser_fill_*)")
print("=" * 100)
ls = lines_of("MCP_Server_Form.wsv")[0]
n = 0
for i, l in enumerate(ls):
    if "fill_" in l and ("方法名" in l or "命令名" in l):
        print("   %4d| %s" % (i + 1, l.strip()[:160])); n += 1
        if n >= 6: break

print()
print("=" * 100)
print("2. workflow_* 的分派写法")
print("=" * 100)
ls2 = lines_of("MCP_Server_Workflow.wsv")[0]
n = 0
for i, l in enumerate(ls2):
    if re.search(r"workflow", l) and ("方法名" in l or "是否以" in l):
        print("   %4d| %s" % (i + 1, l.strip()[:160])); n += 1
        if n >= 6: break

print()
print("=" * 100)
print("3. mcp_status/mcp_result/mcp_help 的分派写法")
print("=" * 100)
ls3 = lines_of("MCP_Server_Core.wsv")[0]
n = 0
for i, l in enumerate(ls3):
    if re.search(r'"(mcp_status|mcp_result|mcp_help|mcp\.status)"', l):
        print("   %4d| %s" % (i + 1, l.strip()[:160])); n += 1
        if n >= 5: break

print()
print("=" * 100)
print("4. MCP_Server_Workflow.wsv:549 上下文 —— 该处是否持有 MCP执行锁?")
print("=" * 100)
for k in range(500, 575):
    if k < len(ls2):
        mark = " <<<" if k == 548 else ""
        print("   %4d| %s%s" % (k + 1, ls2[k][:150], mark))

print()
print("=" * 100)
print("5. MCP_Server.wsv:6917 上下文 (已知 P0-5 候选)")
print("=" * 100)
ls4 = lines_of("MCP_Server.wsv")[0]
for k in range(6898, 6932):
    if k < len(ls4):
        mark = " <<<" if k == 6916 else ""
        print("   %4d| %s%s" % (k + 1, ls4[k][:150], mark))
