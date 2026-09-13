# -*- coding: utf-8 -*-
import io, json, os, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))
want = sys.argv[1:]
for n in want:
    t = d["tools"].get(n)
    if not t:
        print("!! 无此工具:", n)
        continue
    print("=" * 100)
    print("### %s  @%s:%d" % (n, t["file"], t["line"]))
    print("desc:", t["desc"])
    print("schema:")
    for p in t["schema"]:
        print("   - %-18s %-9s %s" % (p["name"], p["type"], p["desc"]))
    print("分派点:")
    for b in d["branch"].get(n, [])[:12]:
        print("   @%s:%d  %s == \"%s\"   in %s" % (b["file"], b["line"], b["sym"], n, b["in"]))
    print()
