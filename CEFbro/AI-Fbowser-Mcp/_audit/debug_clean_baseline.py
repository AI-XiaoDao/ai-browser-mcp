# -*- coding: utf-8 -*-
r"""诊断: 干净重启后基线健康(排除残留进程/代理)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

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


loop.kill_app()
time.sleep(3)
loop.start_app()
call("browser_navigate", {"url": "https://example.com/?clean=%d" % int(time.time())}, to=90)
for i in range(3):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    print('  health#%d err=%s %.2fs %s' % (i, e, d, t[:40]))
e, t, d = call("browser_status", {})
print('  status err=%s %.2fs' % (e, d))
e, t, d = call("browser_get_text", {}, to=60)
print('  get_text err=%s %.2fs %s' % (e, d, t[:60]))
