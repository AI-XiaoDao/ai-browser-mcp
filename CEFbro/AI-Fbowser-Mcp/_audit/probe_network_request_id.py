# -*- coding: utf-8 -*-
r"""browser_network_body 的运行期真值: 请求ID从哪来?
先开 detail_enable 制造可用的 request_id, 再取一条真实ID喂给 browser_network_body。
"""
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
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def val(t):
    try:
        return json.loads(t)
    except Exception:
        return {}


print('detail_enable: %s' % call("browser_network", {"action": "detail_enable"})[1][:200])
call("browser_navigate", {"url": "https://example.com/?netbody=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(1.0)
e, t = call("browser_network", {"action": "list"})
obj = val(t)
logs = ((obj.get("data") or {}).get("network_logs") or [])
print('网络日志条数=%d' % len(logs))
rid = None
for it in logs[:8]:
    print('   keys=%s' % sorted(it.keys()))
    for k in ("request_id", "requestId", "id"):
        if it.get(k):
            rid = it[k]
            break
    if rid:
        break
print('取到 request_id=%r' % rid)
if rid:
    e2, t2 = call("browser_network_body", {"request_id": str(rid)})
    print('browser_network_body(真实ID): isError=%s %s' % (e2, t2[:300]))
