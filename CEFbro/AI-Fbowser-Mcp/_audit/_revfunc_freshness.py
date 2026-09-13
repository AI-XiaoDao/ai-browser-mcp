# -*- coding: utf-8 -*-
"""只读新鲜度校验: 现在重新抽取 src\MCP_Kernel.wsv 的注入串, 与本次分析所用的 _revfunc_runtime.js 逐字节比对。"""
import io, re, hashlib
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

src = io.open(r"src\MCP_Kernel.wsv", "r", encoding="utf-8-sig", newline="").read().split("\n")
line = [l for l in src if "JSON.stringify((function(){var out=[];var seen={}" in l][0]
lit = re.match(r'^\s*注入代码 = "(.*)"\s*$', line).group(1)
parts = lit.split('" + 到文本 (最大数) + "')
rt = parts[0] + "500" + parts[1]
old = io.open(r"_audit\_revfunc_runtime.js", "r", encoding="utf-8", newline="").read()

print("total lines in MCP_Kernel.wsv :", len(src))
print("line number of injected string:", src.index(line) + 1)
print("re-extracted len", len(rt), "sha256", hashlib.sha256(rt.encode()).hexdigest()[:16])
print("analyzed     len", len(old), "sha256", hashlib.sha256(old.encode()).hexdigest()[:16])
print("IDENTICAL (分析对象 == 当前源码):", rt == old)
print("still contains defect '}})return':", "}})return out.slice(0,MAX)" in rt)
print("still contains defect \"}})[\":", "}})['XMLHttpRequest'" in rt)
