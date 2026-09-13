# -*- coding: utf-8 -*-
"""为 A(确认缺口)/C(存疑) 项抽取完整声明块(方法行 → 方法体 '{' 之前的所有行)。"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
V = json.load(io.open(os.path.join(HERE, "_cg2_verdict.json"), encoding="utf-8"))
want = {}
for r in V:
    if r["verdict"] in ("A", "C"):
        want.setdefault((r["file"], r["method"]), r)

src_cache = {}
def lines(fn):
    if fn not in src_cache:
        src_cache[fn] = io.open(os.path.join(LIB, fn), encoding="utf-8",
                                errors="replace").read().split("\n")
    return src_cache[fn]

out = {}
for (fn, meth), r in want.items():
    ls = lines(fn)
    for i, ln in enumerate(ls):
        m = re.match(r"\s*方法\s+(%s)\b" % re.escape(meth), ln)
        if not m:
            continue
        # 收集从 i 到方法体起始 '{' 之前(或 60 行内)的所有行
        block = []
        j = i
        while j < len(ls) and j < i + 60:
            s = ls[j].strip()
            block.append(s)
            if j > i and s == "{":
                break
            j += 1
        # 参数行(过滤掉注释/空行)
        params = [b for b in block if b.startswith("参数") or b.startswith("方法")]
        out["%s::%s" % (r["cls"], meth)] = {"file": fn, "line": i + 1,
                                            "decl": " ".join(params)}
        break
json.dump(out, io.open(os.path.join(HERE, "_cg2_adecl.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
print("抽取 =", len(out), "/", len(want))
for k in sorted(out):
    if k not in ("%s::%s" % (want[[w for w in want if "%s::%s" % (want[w]["cls"], want[w]["method"]) == k][0]]["cls"], ""),):
        pass
miss = [k for k in want if k not in out]
print("缺失:", miss)
for k in sorted(out):
    print("%-52s %s" % (k, out[k]["decl"][:220]))
