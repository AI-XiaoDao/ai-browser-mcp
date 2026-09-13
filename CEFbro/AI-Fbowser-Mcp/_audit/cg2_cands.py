# -*- coding: utf-8 -*-
"""解析 _classlib_gap.md 得到 363 候选(按类), 并与 JSON 中的类库方法/参数表关联。"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
md = io.open(os.path.join(HERE, "_classlib_gap.md"), encoding="utf-8").read()

cands = []
cur = None
for ln in md.split("\n"):
    m = re.match(r"^###\s+(.+?)\s+\((\d+)\)", ln)
    if m:
        cur = m.group(1)
        continue
    if cur and ln.startswith("`"):
        for name in re.findall(r"`([^`]+)`", ln):
            cands.append({"cls": cur, "method": name})

data = json.load(io.open(os.path.join(HERE, "_cg2_data.json"), encoding="utf-8"))
# 类库方法索引: (cls, method) -> 首个定义
idx = {}
for c in data["classlib"]:
    k = (c["cls"], c["method"])
    if k not in idx:
        idx[k] = c

for cd in cands:
    k = (cd["cls"], cd["method"])
    if k in idx:
        cd["file"] = idx[k]["file"]
        cd["params"] = idx[k]["params"]
        cd["note"] = idx[k]["note"]
    else:
        cd["file"] = ""
        cd["params"] = []
        cd["note"] = ""

print("候选总数 = %d" % len(cands))
missing = [c for c in cands if not c["file"]]
print("无法在类库源码中定位的 = %d" % len(missing))
for c in missing[:40]:
    print("   %s :: %s" % (c["cls"], c["method"]))
byc = {}
for c in cands:
    byc.setdefault(c["cls"], []).append(c["method"])
print("\n按类:")
for k in sorted(byc, key=lambda x: -len(byc[x])):
    print("  %-38s %d" % (k, len(byc[k])))

json.dump(cands, io.open(os.path.join(HERE, "_cg2_cands.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
