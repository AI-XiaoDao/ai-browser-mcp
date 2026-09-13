# -*- coding: utf-8 -*-
"""紧凑工具目录: 名 | 文件:行 | 分派器 | 描述 | schema 属性"""
import io, json, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))
out = []
for name in sorted(d["tools"]):
    t = d["tools"][name]
    br = d["branch"].get(name, [])
    who = sorted(set("%s(%s)" % (b["in"], b["sym"]) for b in br))
    sch = ",".join(p["name"] for p in t["schema"])
    out.append("### %s\n  @%s:%d  分派: %s\n  schema: %s\n  desc: %s" %
               (name, t["file"], t["line"], "; ".join(who[:3]), sch or "(无)", t["desc"][:400]))
io.open(os.path.join(HERE, "_cg2_toolcat.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("工具目录写出,", len(d["tools"]), "条")
# 所有 action 枚举值汇总
vals = {}
for name, t in d["tools"].items():
    for p in t["schema"]:
        if p["name"] in ("action", "动作", "method"):
            vals.setdefault(name, []).append(p)
print("\n== 带 action 的工具及枚举值(从 schema 描述中提取) ==")
for n in sorted(vals):
    for p in vals[n]:
        print("%-38s %-8s => %s" % (n, p["name"], p["desc"][:260]))
