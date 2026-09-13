# -*- coding: utf-8 -*-
r"""诊断: 清代理后再次导航是否真正恢复。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
MARK = "s5recover%d" % int(time.time())


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


def href():
    e, t, d = call("browser_execute_js", {"code": "String(location.href)"})
    return t


print('当前 href:', href())
e, t, d = call("browser_navigate", {"url": "https://example.net/?%s=1" % MARK, "wait_for_load": True}, to=90)
print('navigate: err=%s %.2fs %s' % (e, d, t[:80]))
time.sleep(2.0)
print('2s 后 href:', href())
