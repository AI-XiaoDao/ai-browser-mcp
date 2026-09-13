# -*- coding: utf-8 -*-
"""只读: 从 src/MCP_Kernel.wsv 抽取 browser_kernel_reverse_functions 注入的那段 JS(逐字),
写出到 _audit/_revfunc_injected.js, 并做括号配平/深度追踪, 便于定位可疑点。
不修改任何 .wsv。"""
import io, os, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

WSV = r"src\MCP_Kernel.wsv"
OUT = r"_audit\_revfunc_injected.js"

with io.open(WSV, "r", encoding="utf-8-sig", newline="") as f:
    lines = f.read().split("\n")

target = None
for i, ln in enumerate(lines, 1):
    if "JSON.stringify((function(){var out=[];var seen={}" in ln:
        target = (i, ln)
        break
if target is None:
    print("NOT FOUND")
    sys.exit(1)
lineno, raw = target
print("line no:", lineno)
print("raw line length:", len(raw))
print("raw contains backslash:", "\\" in raw)

# 定位赋值: 注入代码 = "..."
eq = raw.index('注入代码 = "')
body = raw[eq + len('注入代码 = "'):]
# 去掉行尾最后一个引号(以及可能的空白)
body = body.rstrip()
assert body.endswith('"'), repr(body[-40:])
js = body[:-1]
print("js length:", len(js))
print("js contains backslash:", "\\" in js)
print("js contains double-quote:", '"' in js)
print("js contains newline:", "\n" in js or "\r" in js)

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(js)
print("wrote", OUT)

# 括号/引号状态机: 检测字符串外的括号配平, 并打印每个 try/catch 的位置与深度
depth = 0
paren = 0
brack = 0
instr = None
esc = False
stack = []
trace = []
for idx, ch in enumerate(js):
    if instr:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == instr:
            instr = None
        continue
    if ch in "'\"`":
        instr = ch
        continue
    if ch == "{":
        depth += 1
        stack.append(("{", idx, depth))
    elif ch == "}":
        trace.append(("close-brace", idx, depth))
        depth -= 1
        if stack:
            stack.pop()
    elif ch == "(":
        paren += 1
    elif ch == ")":
        paren -= 1
    elif ch == "[":
        brack += 1
    elif ch == "]":
        brack -= 1

print("final brace depth:", depth, "paren:", paren, "bracket:", brack)
print("unterminated string:", instr)

# 打印 try { ... } 的文本片段(便于人工核对守卫范围)
import re
for m in re.finditer(r"try\{", js):
    start = m.start()
    print("---- try at", start, "context:")
    print(js[max(0, start - 60): start + 260])
