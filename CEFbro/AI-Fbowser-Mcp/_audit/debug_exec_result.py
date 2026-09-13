# -*- coding: utf-8 -*-
r"""诊断: mcp_result 轮询原文(找 6*7 结果的实际形态)。
"""
import json
import os
import re
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
loop.start_app()
call("browser_navigate", {"url": "https://example.com/?dbg156=%d" % int(time.time())})
call("browser_vip_enable_js_env", {"enable": True, "confirm": True})
e, t, d = call("browser_vip_execute_js_context",
               {"code": "6*7", "timeout_ms": 30000, "repl_mode": False, "user_gesture": True,
                "silent": False, "disable_breaks": False, "include_command_line_api": True}, to=60)
print('submit: err=%s %s' % (e, t[:120]))
m = re.search(r"task_[0-9_]+", t)
tid = m.group(0) if m else ""
print('task_id=', tid)
for i in range(8):
    e2, t2, d2 = call("mcp_result", {"task_id": tid}, to=30)
    print('  poll#%d err=%s %.2fs %s' % (i, e2, d2, t2[:300]))
    time.sleep(1.0)
