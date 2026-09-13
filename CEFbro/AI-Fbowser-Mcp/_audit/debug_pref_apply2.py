# -*- coding: utf-8 -*-
r"""诊断2: 换 minimum_font_size(可观测) 与 非法名 看置首选项是否真被内核消费。
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


def font():
    e, t, d = call("browser_execute_js", {"code": "String(getComputedStyle(document.body).fontSize)"})
    return t


print('当前字号:', font())
e, t, d = call("browser_set_preference", {"name": "webkit.webprefs.minimum_font_size", "value": "30"})
print('set minimum_font_size=30: err=%s %s' % (e, t[:80]))
e, t, d = call("browser_navigate", {"url": "https://example.com/?minf=%d" % int(time.time())}, to=90)
print('新导航: err=%s %.2fs' % (e, d))
print('  字号(期望 >=30px):', font())

e, t, d = call("browser_set_preference", {"name": "no.such.pref.xyz", "value": "1"})
print('非法名 no.such.pref.xyz: err=%s %s' % (e, t[:120]))
