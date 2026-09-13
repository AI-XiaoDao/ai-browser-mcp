# -*- coding: utf-8 -*-
"""只读: 还原 browser_kernel_reverse_functions 的"运行时"注入 JS (含 火山 字符串拼接求值),
写出 _audit/_revfunc_runtime.js (MAX 用默认值 500), 供 node --check 做语法判定。"""
import io, re, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

WSV = r"src\MCP_Kernel.wsv"
OUT = r"_audit\_revfunc_runtime.js"

with io.open(WSV, "r", encoding="utf-8-sig", newline="") as f:
    lines = f.read().split("\n")

lineno = None
raw = None
for i, ln in enumerate(lines, 1):
    if "JSON.stringify((function(){var out=[];var seen={}" in ln:
        lineno, raw = i, ln
        break
assert raw

m = re.match(r'^\s*注入代码 = "(.*)"\s*$', raw)
assert m, "unexpected line shape"
lit = m.group(1)
print("line", lineno, "literal len", len(lit))

# 火山 字符串拼接: "A" + 到文本 (最大数) + "B"  -> A + <500> + B
parts = lit.split('" + 到文本 (最大数) + "')
print("concat parts:", len(parts))
assert len(parts) == 2, parts[:1]
runtime = parts[0] + "500" + parts[1]

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(runtime)
print("runtime len:", len(runtime))
print("wrote", OUT)

# 逐字打印(便于报告引用)。分段打印, 避免单行过长被截断。
SEG = 200
for i in range(0, len(runtime), SEG):
    print("[%04d] %s" % (i, runtime[i:i + SEG]))

# try/catch 配平统计
print("try{ count:", runtime.count("try{"))
print("catch(e){} count:", runtime.count("catch(e){}"))
print("catch count (any):", len(re.findall(r"catch\(", runtime)))
