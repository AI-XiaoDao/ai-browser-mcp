# -*- coding: utf-8 -*-
r"""诊断: set_proxy 第4参 true/false 对 CDP 通道的影响(对照臂, 每臂重启)。
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


def health(tag):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    print('  [%s] err=%s %.2fs' % (tag, e, d))


def arm(tag, prompt):
    loop.kill_app()
    loop.start_app()
    call("browser_navigate", {"url": "https://example.com/?d164=%d" % int(time.time())})
    health(tag + ' 基线')
    e, t, d = call("browser_set_proxy", {"address": "127.0.0.1:1", "close_s5_error_prompt": prompt}, to=60)
    print('  %s set: err=%s %s' % (tag, e, t[:70]))
    health(tag + ' set后')
    call("browser_clear_proxy", {})
    health(tag + ' clear后')


arm('A(prompt=false)', False)
arm('B(prompt=true)', True)
