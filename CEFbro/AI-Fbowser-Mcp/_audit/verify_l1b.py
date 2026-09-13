# -*- coding: utf-8 -*-
import io, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

print("=" * 100)
print("1. browser_reverse_extract 的 schema 声明")
print("=" * 100)
srv = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
for i, l in enumerate(srv):
    if '"browser_reverse_extract"' in l and "添加工具JSON" in l:
        for seg in l.strip().split("+ \",\" +"):
            print("   %s" % seg.strip()[:200])

print()
print("=" * 100)
print("2. 该工具的等长对照: reverse_search / reverse_string_refs 是否也读这两个键")
print("=" * 100)
core = io.open(os.path.join(SRC, "MCP_Server_Core.wsv"), encoding="utf-8").read().split("\n")
for i, l in enumerate(core):
    if re.search(r'yyjson取文本\s*\(参数JSON,\s*"(url_pattern|keyword)"\)', l):
        # 回溯所属分支
        owner = "?"
        for k in range(i, 0, -1):
            m = re.search(r'方法名\s*==\s*"([A-Za-z0-9_]+)"', core[k])
            if m:
                owner = m.group(1); break
        key = re.search(r'"([^"]+)"', l).group(1)
        print("   %-24s:%d  工具 %-30s 键 %s" % ("MCP_Server_Core.wsv", i + 1, owner, key))

print()
print("=" * 100)
print("3. json 里 url_pattern/keyword 是否被 reverse_extract 使用 (全文搜索)")
print("=" * 100)
for i, l in enumerate(core):
    if "url_pattern" in l or '"keyword"' in l:
        print("   %6d| %s" % (i + 1, l.strip()[:170]))

print()
print("=" * 100)
print("4. MCP_Kernel.wsv 分派_方案管理 的 unregister 分支")
print("=" * 100)
kk = io.open(os.path.join(SRC, "MCP_Kernel.wsv"), encoding="utf-8").read().split("\n")
start = next(k for k, l in enumerate(kk) if "分派_方案管理" in l and "方法" in l)
for k in range(start, min(start + 60, len(kk))):
    print("%6d| %s" % (k + 1, kk[k]))
