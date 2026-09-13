# -*- coding: utf-8 -*-
"""B5 — 列出所有未被 TERMS 命中的多字中文串 (即被逐字拆译的元凶)"""
import sys, os, re, json, collections, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("b2", os.path.join(OUT, "b2_english.py"))
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)
TERMS, CHARS = b2.TERMS, b2.CHARS
CN = re.compile(r"[\u4e00-\u9fff]+")

inv = json.load(open(os.path.join(OUT, "inventory.json"), encoding="utf-8"))
names = [c["name"] for c in inv["classes"]] + \
        [m["name"] for m in inv["methods"]] + \
        [v["name"] for v in inv["vars"]] + \
        [p["name"] for p in inv["params"]]

frag = collections.Counter()
for n in names:
    for run in CN.findall(n):
        # 模拟贪婪匹配, 收集"被逐字拆开"的连续片段
        i, L = 0, len(run)
        cur = ""
        while i < L:
            hit = None
            for k in range(min(8, L - i), 0, -1):
                seg = run[i:i + k]
                if seg in TERMS:
                    hit = (k, seg); break
            if hit:
                if len(cur) >= 2:
                    frag[cur] += 1
                cur = ""; i += hit[0]
            else:
                cur += run[i]; i += 1
        if len(cur) >= 2:
            frag[cur] += 1

print("=" * 100)
print("未被 TERMS 命中、被逐字拆译的多字片段 (共 %d 个)" % len(frag))
print("=" * 100)
print()
# 按长度降序 + 频次
items = sorted(frag.items(), key=lambda x: (-len(x[0]), -x[1]))
line = []
for s, c in items:
    line.append("%s(%d)" % (s, c))
print("  " + "  ".join(line))
print()
print("--- 长度>=3 的片段 (优先补词条) ---")
for s, c in items:
    if len(s) >= 3:
        print("   %s x%d" % (s, c), end="")
print()
