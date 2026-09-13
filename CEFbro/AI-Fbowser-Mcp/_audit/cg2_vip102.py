# -*- coding: utf-8 -*-
"""列出 类_FBrowserVIP_控制器 的 102 候选, 标注是否有 src 直调"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
cands = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
JOIN = ""
for fn in sorted(os.listdir(SRC)):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        JOIN += io.open(os.path.join(SRC, fn), encoding="utf-8", errors="replace").read()
for c in cands:
    if c["cls"] != "类_FBrowserVIP_控制器":
        continue
    m = re.search(re.escape(c["method"]) + r"\s*\(", JOIN)
    tag = "直调" if m else "无直调"
    print("%-8s %s" % (tag, c["method"]))
