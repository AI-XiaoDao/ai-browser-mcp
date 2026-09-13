# -*- coding: utf-8 -*-
"""找出"已实现但未在 添加工具JSON 注册"的工具 → AI 代理完全看不到的能力。"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

FILES = ["MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_VIP.wsv",
         "MCP_Kernel.wsv", "MCP_Server_HTTP.wsv", "MCP_Server_Workflow.wsv",
         "MCP_Server_Utils.wsv", "MCP_Callbacks.wsv"]

# 1) 所有实现分支:  方法名 == "tool_name"
BRANCH = re.compile(r'([\u4e00-\u9fff_A-Za-z][\u4e00-\u9fff_A-Za-z0-9_]*)\s*==\s*"([a-z][a-z0-9_]{2,})"')
# 2) 所有注册:  添加工具JSON ("name" ...
REG = re.compile(r'添加工具JSON\s*\(\s*"([^"]+)"')

branches = {}   # name -> [(file, line)]
for f in FILES:
    if not os.path.exists(os.path.join(SRC, f)):
        continue
    for i, l in enumerate(lines_of(f)[0]):
        s = l.strip()
        if s.startswith("#") or s.startswith("@") or s.startswith("//"):
            continue
        for m in BRANCH.finditer(l):
            branches.setdefault(m.group(2), []).append((f, i + 1))

regs = {}
for f in FILES:
    if not os.path.exists(os.path.join(SRC, f)):
        continue
    for i, l in enumerate(lines_of(f)[0]):
        for m in REG.finditer(l):
            regs.setdefault(m.group(1), []).append((f, i + 1))

# 也扫描其它文件里的注册
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".wsv") or f in FILES or ".~vbak" in f:
        continue
    for i, l in enumerate(lines_of(f)[0]):
        for m in REG.finditer(l):
            regs.setdefault(m.group(1), []).append((f, i + 1))

impl_only = sorted(set(branches) - set(regs))
reg_only = sorted(set(regs) - set(branches))

print("=" * 100)
print("工具注册一致性")
print("=" * 100)
print("  已注册: %d   已实现分支: %d" % (len(regs), len(branches)))
print("  已实现但未注册 (AI 看不到): %d" % len(impl_only))
print("  已注册但无实现分支 (调用必失败): %d" % len(reg_only))
print()
print("-" * 100)
print("已实现但未注册 — AI 代理完全不可见的能力")
print("-" * 100)
for n in impl_only:
    locs = branches[n]
    print("  %-32s %s" % (n, ", ".join("%s:%d" % (a, b) for a, b in locs[:3])))
print()
print("-" * 100)
print("已注册但无实现分支")
print("-" * 100)
for n in reg_only:
    print("  %-32s %s" % (n, ", ".join("%s:%d" % (a, b) for a, b in regs[n][:3])))

# 输出 JSON 供后续脚本使用
out = {"impl_only": impl_only, "reg_only": reg_only,
       "branches": {k: v for k, v in branches.items()}, "regs": {k: v for k, v in regs.items()}}
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_reg_gap.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print()
print("saved _reg_gap.json")
