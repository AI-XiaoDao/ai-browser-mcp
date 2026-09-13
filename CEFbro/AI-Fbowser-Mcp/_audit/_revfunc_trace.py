# -*- coding: utf-8 -*-
"""只读: 对 _audit/_revfunc_runtime.js 做逐字符的括号深度追踪, 定位语法错误点。"""
import io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

js = io.open(r"_audit\_revfunc_runtime.js", "r", encoding="utf-8", newline="").read()
print("len", len(js))

depth = 0
paren = 0
instr = None
esc = False
marks = {}
for i, ch in enumerate(js):
    if instr:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == instr:
            instr = None
        continue
    if ch in "'\"":
        instr = ch
        continue
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth < 0:
            print("!!! depth<0 at", i, js[max(0, i - 40):i + 40])
            break
    elif ch == "(":
        paren += 1
    elif ch == ")":
        paren -= 1
        if paren < 0:
            print("!!! paren<0 at", i, js[max(0, i - 60):i + 60])
            break
    if js.startswith("return", i) and js[i - 1] == " ":
        print("at 'return' index", i, "brace depth:", depth, "paren:", paren)

print("final depth", depth, "paren", paren)

# 打印关键边界处的上下文
for key in ["'])}catch(e){}['location'", "}})}catch(e){}['location'", "}})['XMLHttpRequest'", "})return out.slice"]:
    j = js.find(key)
    print("---- boundary", repr(key), "at", j)
    if j >= 0:
        print(js[max(0, j - 80): j + 90])

# 用 node 求真实错误位置
io.open(r"_audit\_revfunc_syntax_check.js", "w", encoding="utf-8", newline="\n").write(
    "const fs=require('fs');const src=fs.readFileSync('_audit/_revfunc_runtime.js','utf8');\n"
    "try{ new (require('vm').Script)(src); console.log('PARSE OK'); }\n"
    "catch(e){ console.log('PARSE FAIL:', e.message); console.log('stack:', String(e.stack).split('\\n').slice(0,6).join('\\n')); }\n"
)
print("wrote _audit/_revfunc_syntax_check.js")
