# -*- coding: utf-8 -*-
"""为 363 个候选生成证据块: 参数表 / src 直调点 / 字面量命中 / 相关工具。
输出 _cg2_evidence.txt
"""
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
            files[fn] = f.read().split("\n")

def call_sites(method, limit=6):
    pat = re.compile(re.escape(method) + r"\s*\(")
    out = []
    for fn, ls in files.items():
        for i, ln in enumerate(ls, 1):
            if pat.search(ln):
                out.append("%s:%d %s" % (fn, i, ln.strip()[:150]))
                if len(out) >= limit:
                    return out
    return out

def lit_hits(s, limit=6):
    out = []
    for fn, ls in files.items():
        for i, ln in enumerate(ls, 1):
            if s in ln:
                out.append("%s:%d %s" % (fn, i, ln.strip()[:150]))
                if len(out) >= limit:
                    return out
    return out

tools = d["tools"]
out = []
for c in cands:
    name = c["method"]
    out.append("=" * 100)
    out.append("### %s :: %s   [候选]" % (c["cls"], name))
    out.append("来源文件: %s" % c["file"])
    if c["note"]:
        out.append("注释: %s" % c["note"][:160])
    ps = " | ".join("%s%s" % (p[0], (" " + p[1])[:70] if p[1] else "") for p in c["params"])
    out.append("参数表: %s" % (ps if ps else "(无参数)"))
    cs = call_sites(name)
    out.append("src 直调点(%d):" % len(cs))
    for x in cs:
        out.append("    " + x)
    lh = lit_hits(name)
    out.append("字面量命中(%d):" % len(lh))
    for x in lh:
        out.append("    " + x)
    # 关键词→工具
    toks = [t for t in re.split(r"[_]", name) if len(t) >= 2]
    rel = []
    for tn, tv in tools.items():
        blob = tn + " " + tv["desc"] + " " + " ".join(
            p["name"] + p["desc"] for p in tv["schema"])
        sc = sum(1 for t in toks if t and t in blob)
        if sc:
            rel.append((sc, tn))
    rel.sort(key=lambda x: -x[0])
    out.append("相关工具(关键词): %s" % ", ".join("%s(%d)" % (n, s) for s, n in rel[:14]))
    out.append("")

io.open(os.path.join(HERE, "_cg2_evidence.txt"), "w", encoding="utf-8", newline="\n").write(
    "\n".join(out))
print("写出 _cg2_evidence.txt, %d 行" % len(out))
