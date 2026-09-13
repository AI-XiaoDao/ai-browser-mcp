# -*- coding: utf-8 -*-
"""B4 — 生成名质量 QA: 找出别扭/可疑的合成, 供批量修正"""
import json, os, re, collections, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(OUT, "english_names.json"), encoding="utf-8"))

BAD_TOKENS = ["Way", "X", "DoDo", "ToTo", "AndAnd", "Member", "Re",
              "Times", "Ask", "Walk", "Give", "Let", "Be", "Take", "OnOn"]

allnames = []
for k, v in d["classes"].items():
    if v["en"]:
        allnames.append(("类", k, v["en"]))
for k, v in d["methods"].items():
    if v["en"]:
        allnames.append(("方法", k, v["en"]))
for k, v in d["vars"].items():
    allnames.append(("变量", k, v["en"]))
for k, v in d["params"].items():
    allnames.append(("参数", k, v["en"]))

print("生成名总数:", len(allnames))
print()
hits = collections.defaultdict(list)
for kind, k, en in allnames:
    for t in BAD_TOKENS:
        if t in en and not (t == "X" and re.search(r"(^|[a-z])X", en) is None):
            hits[t].append((kind, k, en))
print("=" * 100)
print("可疑 token 命中")
print("=" * 100)
for t, lst in sorted(hits.items(), key=lambda x: -len(x[1])):
    print()
    print("--- %s (%d 条) ---" % (t, len(lst)))
    for (kind, k, en) in lst[:14]:
        print("   [%s] %-46s -> %s" % (kind, k[-46:], en))
    if len(lst) > 14:
        print("   ... 另有 %d 条" % (len(lst) - 14))

print()
print("=" * 100)
print("超长名 (>= 36 字符) TOP 25")
print("=" * 100)
for kind, k, en in sorted(allnames, key=lambda x: -len(x[2]))[:25]:
    print("   %-3d [%s] %-46s -> %s" % (len(en), kind, k[-46:], en))

print()
print("=" * 100)
print("重复 token 相邻 (如 XxxXxx)")
print("=" * 100)
n = 0
for kind, k, en in allnames:
    for m in re.finditer(r"\b(\w{3,})\1", en):
        print("   [%s] %-46s -> %s" % (kind, k[-46:], en)); n += 1
        break
    if n > 20:
        break
if n == 0:
    print("   无")
