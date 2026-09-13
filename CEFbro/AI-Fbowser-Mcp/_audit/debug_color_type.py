# -*- coding: utf-8 -*-
r"""诊断: 颜色类型 text(0) vs bg(4) 对 置颜色/置颜色_索引 的接受度。
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


def run_spec(spec):
    call("browser_context_menu", {"action": "set", "items": spec}, to=60)
    e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
    e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
    print('  get: %s' % t[:800])
    # 重新起一个实例(模态约束)
    loop.kill_app()
    loop.start_app()
    call("browser_navigate", {"url": "https://example.com/?dbg162=%d" % int(time.time())})


loop.kill_app()
loop.start_app()
call("browser_navigate", {"url": "https://example.com/?dbg162a=%d" % int(time.time())})
print('== A: color/colorat text(0) ==')
run_spec("item|自建项|26501|1|0|\ncolor||26501|text:FF102030|0|\ncolorat||0|text:FF102030|0|")
print('== B: color/colorat bg(4) ==')
run_spec("item|自建项|26501|1|0|\ncolor||26501|bg:FF102030|0|\ncolorat||0|bg:FF102030|0|")
