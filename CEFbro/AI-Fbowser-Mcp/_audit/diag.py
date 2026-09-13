# -*- coding: utf-8 -*-
import sys, os, json
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
src = open(os.path.join(OUT, "a9c_symbols.py"), encoding="utf-8").read()
head = src.split("# ---------- EM ----------")[0]
g = {"__file__": os.path.join(OUT, "a9c_symbols.py"), "__name__": "a9c"}
exec(compile(head, "a9c", "exec"), g)
classes, hdrs = g["classes"], g["hdrs"]
compatible, align_lcs = g["compatible"], g["align_lcs"]
norm_cpp_class = g["norm_cpp_class"]
det = json.load(open(os.path.join(OUT, "char_pinyin.json"), encoding="utf-8"))
print("dict chars:", len(det))
print()
print("--- 关键类名逐字核对 ---")
align_parts = g["align_parts"]
for nm, cpp in [("MCP命令服务器", "rg_MCPMingLingFuWuQi"),
                ("MCP_VIP分派", "rg_MCP_VIPFenPa"),
                ("MCPDevTools观察者", "rg_class_MCP_DevToolsgchzh")]:
    parts = align_parts(nm, cpp)
    print("%-22s vs %-30s -> %s" % (nm, cpp, parts))
print()
print("--- 字典中相关字的值 ---")
for ch in list("命令服务器分派观察者"):
    print("   %s -> %s" % (ch, det.get(ch, "(未收录)")))
print()
print("--- 与生成头直接核对: 生成头里 命令服务器 的拼音是 MingLingFuWuQi ---")

for c in ["MCP命令服务器", "MCP_VIP分派", "类_MCP_DevTools观察者", "MCP_常量"]:
    if c not in classes:
        print("!! missing class", c); continue
    W = [x[0] for x in classes[c]["methods"]]
    print()
    print("=== %s  wsv方法数=%d ===" % (c, len(W)))
    print("  前6个方法:", W[:6])
    rows = []
    for fn, h in hdrs.items():
        H = [x[0] for x in h["methods"]]
        nm = c[2:] if c.startswith("类_") else c
        okc = compatible(nm, "rg_" + norm_cpp_class(h["class"]), det)
        p = align_lcs(W, H, det) if (okc and H) else []
        rows.append((len(p), fn, len(H), okc))
    rows.sort(reverse=True)
    for (sc, fn, nh, okc) in rows[:5]:
        print("  %-44s 头方法=%3d classCompat=%-5s LCS=%3d" % (fn, nh, okc, sc))
