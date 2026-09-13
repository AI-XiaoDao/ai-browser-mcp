# -*- coding: utf-8 -*-
r"""诊断: 清理任务 mcp_result 的实际文本。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


e, t, d = call("browser_clear_cache", {"targets": "cookies"}, to=60)
print('submit: err=%s %s' % (e, t[:120]))
m = re.search(r"task_[0-9_]+", t)
tid = m.group(0) if m else ""
for i in range(6):
    e2, t2, _ = call("mcp_result", {"request_id": tid}, to=30)
    print('  poll#%d err=%s %s' % (i, e2, t2[:400]))
    if not e2:
        break
    time.sleep(1.0)
