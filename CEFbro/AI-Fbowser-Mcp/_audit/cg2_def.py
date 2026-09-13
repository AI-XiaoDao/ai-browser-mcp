# -*- coding: utf-8 -*-
"""按方法名打印类库源码中的定义片段(方法行 + 参数行 + 注释)"""
import io, os, re, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
want = sys.argv[1:]
for fn in sorted(os.listdir(LIB)):
    if not fn.endswith(".wsv"):
        continue
    ls = io.open(os.path.join(LIB, fn), encoding="utf-8", errors="replace").read().split("\n")
    for i, ln in enumerate(ls):
        m = re.match(r"\s*方法\s+(\S+)", ln)
        if m and m.group(1) in want:
            print("=" * 90)
            print("### %s :: %s  (%s:%d)" % (fn, m.group(1), fn, i + 1))
            j = i
            while j < len(ls) and j < i + 14:
                s = ls[j].strip()
                if s and not (s.startswith("方法") or s.startswith("参数") or s.startswith("注释")
                              or s.startswith("\\") or s.startswith("@") or s.startswith('"')):
                    break
                print("   " + s[:230])
                j += 1
            print("   ...body...")
