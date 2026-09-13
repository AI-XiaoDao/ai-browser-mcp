# -*- coding: utf-8 -*-
r"""确认: 开了 `event_app_enable`(查询侧总闸)之后, 启动期事件是否真的已经落库(证明 缓冲+默认开关 生效)。
用法: py -3 _audit\probe_startup_records.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

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


print('开总闸 event_app_enable:', call("browser_collect", {"action": "event_app_enable"})[1][:130])
for kind in ("app_startup_cmdline", "app_startup_request_context_ready", "app_startup_child_process",
             "app_startup_message_pump", "app_extension_created"):
    e, t = call("browser_event", {"event_type": kind, "limit": 20})
    print('  %-38s isError=%-5s %s' % (kind, e, t[:150]))

print('\n时间线里出现过的 app_* 事件名:')
e, t = call("browser_event", {"limit": 200})
try:
    o = json.loads(t)
    d = o.get("data") if isinstance(o.get("data"), dict) else o
    evs = d.get("events") or []
    names = sorted({(x.get("event") or x.get("event_name") or "") for x in evs if isinstance(x, dict)})
    app = [n for n in names if n.startswith("app_")]
    print('  时间线事件数=%d, app_* 名字=%s' % (len(evs), app or "(无)"))
    print('  全部名字(前 30)=%s' % names[:30])
except Exception as ex:
    print('  解析失败: %s | %s' % (ex, t[:200]))
