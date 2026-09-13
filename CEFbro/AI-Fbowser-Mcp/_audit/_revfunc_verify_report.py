# -*- coding: utf-8 -*-
"""只读校对: 报告里引用的注入串/修复片段是否与源码逐字一致。"""
import io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

rep = io.open(r"_audit\_revfunc_rootcause.md", "r", encoding="utf-8").read()
rt = io.open(r"_audit\_revfunc_runtime.js", "r", encoding="utf-8", newline="").read()
fixed = io.open(r"_audit\_revfunc_runtime_fixed.js", "r", encoding="utf-8", newline="").read()
src = io.open(r"src\MCP_Kernel.wsv", "r", encoding="utf-8-sig", newline="").read()

checks = [
    ("报告是否含运行期真串(逐字)", rt in rep),
    ("报告是否含 .wsv 原始字面量(含 到文本(最大数))", r'var MAX=" + 到文本 (最大数) + ";var FIL=' in rep),
    ("报告修复点1 前片段(源码中存在)", "}})}catch(e){}})['XMLHttpRequest','WebSocket','Promise'," in src),
    ("报告修复点1 后片段", "}})}catch(e){}});['XMLHttpRequest','WebSocket','Promise'," in rep),
    ("报告修复点2 前片段(源码中存在)", "}})return out.slice(0,MAX)})())" in src),
    ("报告修复点2 后片段", "}});return out.slice(0,MAX)})())" in rep),
    ("修复后参考串已生成", len(fixed) == len(rt) + 2),
    ("源码仍含缺陷(未被我改动)", ")return out.slice(0,MAX)" in src),
]
for name, ok in checks:
    print(("OK   " if ok else "FAIL ") + name)

# 交叉: 报告里的"替换前/替换后"两对片段, 拼回后应等于 fixed
print("修复片段拼接校验:",
      ("}})}catch(e){}})" + ";" + "['XMLHttpRequest'") in fixed and
      ("}})" + ";" + "return out.slice") in fixed)
