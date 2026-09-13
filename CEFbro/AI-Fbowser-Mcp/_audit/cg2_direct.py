# -*- coding: utf-8 -*-
"""统计每个候选的: src 直调点数 / 字面量命中数 / 相关工具 top3"""
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
files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        with io.open(os.path.join(SRC, fn), encoding="utf-8", errors="replace") as f:
            files[fn] = f.read()
JOIN = "\n".join(files.values())

rows = []
for c in cands:
    n = c["method"]
    direct = len(re.findall(re.escape(n) + r"\s*\(", JOIN))
    lit = JOIN.count(n)
    rows.append((c["cls"], n, direct, lit, len(c["params"]), c["file"]))

zero = [r for r in rows if r[2] == 0]
print("候选 = %d, 其中 src 中无同名直调 = %d, 有直调 = %d" % (len(rows), len(zero), len(rows) - len(zero)))
print("\n== 有同名直调的候选(疑似已实现/已覆盖) ==")
for r in sorted(rows, key=lambda x: -x[2]):
    if r[2]:
        print("%-42s %-34s direct=%d lit=%d" % (r[0], r[1], r[2], r[3]))
