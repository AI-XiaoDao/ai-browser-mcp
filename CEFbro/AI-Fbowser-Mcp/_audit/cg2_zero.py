# -*- coding: utf-8 -*-
"""列出无同名直调的候选, 按类聚合; 并对每个给出相关工具 top5(用类库注解+名字分词)"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))
cands = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
JOIN = ""
for fn in sorted(os.listdir(SRC)):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        JOIN += io.open(os.path.join(SRC, fn), encoding="utf-8", errors="replace").read()

zero = []
for c in cands:
    if not re.search(re.escape(c["method"]) + r"\s*\(", JOIN):
        zero.append(c)

byc = {}
for c in zero:
    byc.setdefault(c["cls"], []).append(c)
print("无同名直调候选 = %d, 分布于 %d 个类\n" % (len(zero), len(byc)))
for cls in sorted(byc, key=lambda x: -len(byc[x])):
    print("### %s (%d)" % (cls, len(byc[cls])))
    for c in byc[cls]:
        print("   - %s   [%s]" % (c["method"], c["file"]))
    print()
json.dump([{k: v for k, v in c.items()} for c in zero],
          io.open(os.path.join(HERE, "_cg2_zero.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
