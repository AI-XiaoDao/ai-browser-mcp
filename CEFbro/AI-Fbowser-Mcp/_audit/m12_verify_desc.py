# -*- coding: utf-8 -*-
"""M12 — 验证描述改写结果 + 度量改善"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
NEW_ONLY = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "short_desc.json"), encoding="utf-8"))

srv = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read()
lines = srv.split("\n")

# 解析全部工具描述
desc = {}
for l in lines:
    m = re.match(r'\s*添加工具JSON\s*\(\s*"([^"]+)"\s*,\s*"([^"]*)"', l)
    if m and m.group(1) not in desc:
        desc[m.group(1)] = m.group(2)

print("=" * 96)
print("描述改写验证")
print("=" * 96)
print()
print("工具总数(解析到描述): %d" % len(desc))

TARGETS = list(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "short_desc.json"), encoding="utf-8")))
old = {n: d for n, d, _ in NEW_ONLY}

print()
print("--- 改写后的 37 条 (前后对比) ---")
print("%-42s %-14s %s" % ("工具", "旧 -> 新(字)", "新描述"))
print("-" * 118)
short_now = 0
for n, od, _ in sorted(NEW_ONLY):
    nd = desc.get(n, "")
    if len(nd) < 12:
        short_now += 1
    print("%-42s %3d -> %-4d %s" % (n, len(od), len(nd), nd[:78]))

# 全量统计
lens = sorted(len(d) for d in desc.values())
under12 = [n for n, d in desc.items() if len(d) < 12]
print()
print("=" * 96)
print("全量改善度量")
print("=" * 96)
print("  描述 <12 字的工具: 116 -> %d  (减少 %d)" % (len(under12), 116 - len(under12)))
print("  描述长度: 最短 %d / 中位 %d / 最长 %d" % (lens[0], lens[len(lens)//2], lens[-1]))
tot = sum(len(d.encode("utf-8")) for d in desc.values())
print("  描述总字节: %d" % tot)
print()
print("  仍 <12 字的工具(未改写):")
for n in sorted(under12):
    print("     %-42s %s" % (n, desc[n]))
