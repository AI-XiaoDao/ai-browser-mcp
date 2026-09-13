# -*- coding: utf-8 -*-
r"""调试: search_script list 原始回包 —— 看 scripts_json 里有没有探针脚本。
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


e, t, d = call("browser_reverse_search_script", {"action": "list"}, to=90)
print('err=%s %.2fs' % (e, d))
print('RAW:')
print(t[:3000])
