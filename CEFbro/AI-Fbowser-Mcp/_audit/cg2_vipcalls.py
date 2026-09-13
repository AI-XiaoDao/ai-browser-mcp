# -*- coding: utf-8 -*-
"""列出 src 中所有对 VIP控制器/浏览器对象的方法调用: 变量.方法名 ("""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
CALL = re.compile(r'\b(vip_ctrl|vipCtrl|vipctl|vip|ctrl|控制器)\s*\.\s*([\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa50-9A-Za-z_]*)\s*\(')
out = {}
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".wsv") or "~vbak" in fn:
        continue
    for i, ln in enumerate(io.open(os.path.join(SRC, fn), encoding="utf-8", errors="replace").read().split("\n"), 1):
        for m in CALL.finditer(ln):
            out.setdefault(m.group(2), []).append("%s:%d" % (fn, i))
for k in sorted(out):
    print("%-42s %2d  %s" % (k, len(out[k]), ", ".join(out[k][:5])))
print("\n合计", len(out))
