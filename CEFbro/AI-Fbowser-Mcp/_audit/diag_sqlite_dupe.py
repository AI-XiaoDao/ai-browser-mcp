# -*- coding: utf-8 -*-
"""直接读应用自己的 SQLite 异步结果库, 检验"同名键被重复追加"假设。
这是完全独立的证据源(不经过 MCP 协议, 不经我的推断)。"""
import sqlite3, json, re, sys
DB = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\_int\AI-Fbowser-Mcp\debug\x64\linker\mcp_cache.db"
con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
cur = con.cursor()
print("表:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")])
print("async_results 行数:", cur.execute("SELECT COUNT(*) FROM async_results").fetchone()[0])
print()
rows = cur.execute("SELECT task_id, result_json FROM async_results ORDER BY rowid DESC LIMIT 400").fetchall()
dupe = []
scrape = []
for tid, js in rows:
    if not js:
        continue
    n = len(re.findall(r'"_phase"\s*:', js))
    if n > 1:
        dupe.append((tid, n, js[:220]))
    if '"_extract_task_id"' in js or '"what":"scrape"' in js.replace(" ", ""):
        scrape.append((tid, n, js[:300]))
print("含重复 \"_phase\" 键的行数: %d / %d" % (len(dupe), len(rows)))
for tid, n, js in dupe[:6]:
    print("  %s  出现 %d 次: %s" % (tid, n, js))
print()
print("scrape 相关行: %d" % len(scrape))
for tid, n, js in scrape[:6]:
    print("  %s  _phase出现%d次: %s" % (tid, n, js))
# 统计所有键的重复情况
from collections import Counter
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
allkeys = Counter()
dupkinds = Counter()
for tid, js in rows:
    if not js:
        continue
    keys = re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', js)
    c = Counter(keys)
    for k, v in c.items():
        if v > 1:
            dupkinds[k] += 1
print()
print("出现重复的键名(按行数计):", dupkinds.most_common(15))
