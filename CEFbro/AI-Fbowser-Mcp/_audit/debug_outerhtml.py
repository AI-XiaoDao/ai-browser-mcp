# -*- coding: utf-8 -*-
r"""调试 set_outer_html 回读未确认: 打印完整回包。
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


e, t, d = call("browser_execute_js",
               {"code": "var s2=document.createElement('span');s2.id='sp2';s2.textContent='x';document.body.appendChild(s2);'ok'"})
print('setup err=%s %.2fs %s' % (e, d, t[:60]))

e, t, d = call("browser_vip_dom_node_edit",
               {"action": "set_outer_html", "selector": "#sp2", "value": "<b id='bold'>BB</b>", "confirm": True}, to=60)
print('set_outer_html err=%s %.2fs' % (e, d))
print('FULL RESPONSE:')
print(t)
