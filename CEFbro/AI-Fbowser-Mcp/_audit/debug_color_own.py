# -*- coding: utf-8 -*-
r"""诊断: colorat@17(自建项索引) text 类型是否接受。
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


def call(n, a=None, to=90):
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
loop.start_app()
call("browser_navigate", {"url": "https://example.com/?dbg162c=%d" % int(time.time())})
call("browser_context_menu", {"action": "set",
                              "items": "item|X|26501|1|0|\ncolorat||17|text:FF102030|0|"}, to=60)
e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
print('arm err=%s %.2fs' % (e, d))
e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
print('get: %s' % t[:700])
