# -*- coding: utf-8 -*-
import io, json, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))
print("== 比较符号(左值) 及其取值数 ==")
for k in sorted(d["symbols"], key=lambda x: -len(d["symbols"][x])):
    v = d["symbols"][k]
    print("%-28s %3d  例: %s" % (k, len(v), ", ".join(list(v)[:8])))
print()
print("== 有 schema 的工具示例(含 action 类) ==")
n = 0
for name, t in d["tools"].items():
    names = [p["name"] for p in t["schema"]]
    if "action" in names or "动作" in names or "method" in names:
        print("%-34s %s" % (name, names))
        n += 1
print("含 action 类参数的工具 =", n)
