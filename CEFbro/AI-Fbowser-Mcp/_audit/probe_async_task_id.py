# -*- coding: utf-8 -*-
r"""查清"异步任务 id 到底在回包的哪个字段"(用于把 mcp_result 的台账探针改成真值)。"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    t = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
    return bool(rr.get("isError")), t, dt


TS = int(time.time())
for tag, args in (("navigate async_only", {"url": "https://example.com/?asp=%d" % TS, "async_only": True}),
                  ("execute_js async_only", {"code": "1+1", "async_only": True}),
                  ("wait async_only", {"action": "selector", "selector": "h1", "async_only": True})):
    e, t, dt = call(tag.split()[0].join([]) or ("browser_" + ("navigate" if "navigate" in tag else "execute_js" if "execute" in tag else "wait")), args)
    print('== %s (%.2fs err=%s)' % (tag, dt, e))
    print('   %s' % t.replace('\n', ' ')[:400])
    try:
        o = json.loads(t)
        print('   keys=%s' % sorted(o.keys()))
        d = o.get("data")
        if isinstance(d, dict):
            print('   data.keys=%s' % sorted(d.keys()))
    except Exception as ex:
        print('   (非JSON: %r)' % ex)
    print()

print('== mcp_result 试用上面拿到的 task_id ==')
e, t, dt = call("browser_navigate", {"url": "https://example.com/?asp2=%d" % TS, "async_only": True})
tid = ""
try:
    o = json.loads(t)
    for k in ("task_id", "request_id", "id"):
        if isinstance(o.get(k), str):
            tid = o[k]
    d = o.get("data")
    if isinstance(d, dict):
        for k in ("task_id", "request_id", "id"):
            if isinstance(d.get(k), str):
                tid = d[k]
except Exception:
    pass
print('   task_id=%r' % tid)
time.sleep(1.5)
e, t, dt = call("mcp_result", {"request_id": tid, "consume": True})
print('   mcp_result -> err=%s %.2fs %s' % (e, dt, t.replace('\n', ' ')[:300]))
