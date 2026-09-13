# -*- coding: utf-8 -*-
"""M5 — 补测: 异步 stub 计数 与 非 JSON content 抽样"""
import json, os, collections
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(OUT, "probe_raw.json"), encoding="utf-8"))

ok = [r for r in rows if r["cat"] == "OK"]
print("OK 工具数: %d" % len(ok))

asy = [r for r in ok if "_async" in r["detail"]]
print()
print("=== 返回 _async 的工具: %d ===" % len(asy))
for r in asy:
    print("   %-44s %s" % (r["name"], r["detail"][:78].replace("\n", " ")))

print()
print("=== content 不是合法 JSON 的工具 ===")
bad = []
for r in ok:
    t = r["detail"].strip()
    if t.startswith("{"):
        try:
            json.loads(t)
        except Exception:
            bad.append(r)
print("共 %d 个:" % len(bad))
for r in bad:
    print("   %-44s %s" % (r["name"], r["detail"][:78].replace("\n", " ")))
