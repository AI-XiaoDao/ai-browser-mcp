# -*- coding: utf-8 -*-
r"""诊断: ①`browser_event` 查询 app_startup_* 的**查询侧闸门**到底看哪个开关? ②handler 拒绝文案全文。
用法: py -3 _audit\probe_startup_gate.py
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


def call(n, a=None, to=30):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,)
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)

for kind in ("app_startup_cmdline", "app_startup_request_context_ready", "app_startup_message_pump"):
    e, t = call("browser_event", {"event_type": kind, "limit": 20})
    print('  查询 %-38s isError=%-5s %s' % (kind, e, t[:120]))

print('\n开 startup 族开关后再查:')
e, t = call("browser_collect", {"action": "event_startup_enable"})
print('  enable -> isError=%s %s' % (e, t[:150]))
for kind in ("app_startup_cmdline", "app_startup_request_context_ready"):
    e, t = call("browser_event", {"event_type": kind, "limit": 20})
    print('  查询 %-38s isError=%-5s %s' % (kind, e, t[:150]))

print('\n事件开关状态:')
e, t = call("browser_kernel_events_all", {"action": "status"})
print('  %s' % t[:400])

print('\nhandler 拒绝文案全文:')
e, t = call("browser_inject", {"type": "handler", "persist": True, "code": "1", "inject_id": "dbg"})
print('  isError=%s' % e)
print('  %s' % t)
