# -*- coding: utf-8 -*-
"""为每个候选的 src 直调点定位其所属工具(最近的 方法名==/规范名== 分支)。
输出 _cg2_covmap.json : {cls::method: {"tool":..., "site":...}}
"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
cands = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
TOOLS = set(json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))["tools"])

BR = re.compile(r'(?:方法名|规范名|短名|规范工具|快速方法名)\s*==\s*"([^"]+)"')
DISP = re.compile(r'^\s*方法\s+([^\s<（(]+)')
files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        files[fn] = io.open(os.path.join(SRC, fn), encoding="utf-8", errors="replace").read().split("\n")

# 预计算每个文件每行的当前分支与方法
ctx = {}
for fn, ls in files.items():
    cur_tool = ""
    stack = []
    for i, ln in enumerate(ls):
        dm = DISP.match(ln)
        if dm:
            cur_tool = ""      # 进入新方法: 分支重置
        for m in BR.finditer(ln):
            if m.group(1) in TOOLS:
                cur_tool = m.group(1)
        ctx[(fn, i + 1)] = (cur_tool, dm.group(1) if dm else "")

out = {}
for c in cands:
    name = c["method"]
    pat = re.compile(re.escape(name) + r"\s*\(")
    hits = []
    for fn, ls in files.items():
        for i, ln in enumerate(ls, 1):
            if pat.search(ln):
                tool, meth = ctx.get((fn, i), ("", ""))
                hits.append({"file": fn, "line": i, "tool": tool, "in": meth})
    out["%s::%s" % (c["cls"], name)] = hits

json.dump(out, io.open(os.path.join(HERE, "_cg2_covmap.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
n = sum(1 for v in out.values() if v)
print("有直调的候选 =", n, "/", len(out))
for k, v in sorted(out.items()):
    if v:
        ts = sorted(set(x["tool"] or ("(%s)" % x["in"]) for x in v))
        print("%-52s -> %s" % (k, ", ".join(ts[:4])))
