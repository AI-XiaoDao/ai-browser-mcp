# -*- coding: utf-8 -*-
"""M10 — 列出描述过短的工具, 附参数签名, 供逐条改写"""
import json, urllib.request, os

BASE = "http://127.0.0.1:9222"
tools = json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=25)
                   .read().decode("utf-8"))["tools"]

rows = []
for t in tools:
    d = t.get("description") or ""
    if len(d) < 12:
        props = (t.get("inputSchema") or {}).get("properties") or {}
        req = (t.get("inputSchema") or {}).get("required") or []
        sig = ", ".join("%s%s:%s" % (p, "*" if p in req else "", (v or {}).get("type", "?"))
                        for p, v in props.items())
        rows.append((t["name"], d, sig))

rows.sort()
print("描述 < 12 字的工具: %d 个" % len(rows))
print()
print("%-44s %-10s %s" % ("工具", "当前描述", "参数(带*为必填)"))
print("-" * 118)
for n, d, s in rows:
    print("%-44s %-10s %s" % (n, d, s))

# 按前缀分组统计, 便于分批改写
import collections
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
c = collections.Counter()
for n, _, _ in rows:
    c[n.split("_")[1] if n.startswith("browser_") else n] += 1
print()
print("按功能域分布:")
for k, v in c.most_common():
    print("   %-16s %d" % (k, v))

json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "short_desc.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
