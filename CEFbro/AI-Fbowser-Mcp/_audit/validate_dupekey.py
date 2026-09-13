# -*- coding: utf-8 -*-
import sqlite3, re, sys
sys.path.insert(0, ".")
from dupekey_scan import keys_at_depth1
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
DB = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\_int\AI-Fbowser-Mcp\debug\x64\linker\mcp_cache.db"
con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\","/"), uri=True)
rows = con.execute("SELECT task_id, result_json FROM async_results").fetchall()
print("行数 =", len(rows))

print("\n=== 1) 用简单正则复查(与早先发现一致?) ===")
n_phase = n_poll = 0
for tid, js in rows:
    if not js: continue
    if len(re.findall(r'"_phase"\s*:', js)) > 1:
        n_phase += 1; print("  _phase重复:", tid, js[:150])
    if len(re.findall(r'"_poll_count"\s*:', js)) > 1:
        n_poll += 1
print("  _phase 重复行 = %d, _poll_count 重复行 = %d" % (n_phase, n_poll))

print("\n=== 2) 检测器自证: 对**故意构造的坏状态**是否能检出 ===")
bad = '{"_waiting":true,"what":"scrape","_phase":0,"extract_selector":"h1","_phase":3,"_extract_task_id":"t1"}'
good = '{"_waiting":true,"what":"scrape","_phase":3,"_extract_task_id":"t1"}'
nested = '{"a":{"_phase":1,"_phase":2},"_phase":3}'
for name, js in (("坏状态(顶层重复)", bad), ("好状态", good), ("嵌套重复(顶层不重复)", nested)):
    ks = keys_at_depth1(js)
    from collections import Counter
    d = {k: v for k, v in Counter(ks).items() if v > 1}
    print("  %-22s 顶层键=%s 重复=%s" % (name, ks, d))
print("\n预期: 坏状态应报 _phase 重复; 好状态无; 嵌套重复在顶层不应报(本检测器只看顶层)")
