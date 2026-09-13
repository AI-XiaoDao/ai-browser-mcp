# -*- coding: utf-8 -*-
"""对每个候选, 打印 src 中出现的类库方法名(全名/前缀)所在文件:行, 便于判覆盖"""
import io, json, os, re, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
cands = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
ZF = json.load(io.open(os.path.join(HERE, "_cg2_zero.json"), encoding="utf-8"))
zero_names = set((c["cls"], c["method"]) for c in ZF)
files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        files[fn] = io.open(os.path.join(SRC, fn), encoding="utf-8", errors="replace").read().split("\n")

def find(s, limit=10):
    out = []
    for fn, ls in files.items():
        for i, ln in enumerate(ls, 1):
            if s in ln:
                out.append("   %s:%d %s" % (fn, i, ln.strip()[:170]))
                if len(out) >= limit:
                    return out
    return out

for arg in sys.argv[1:]:
    print("=" * 90)
    print("### 搜索:", arg)
    for x in find(arg):
        print(x)
