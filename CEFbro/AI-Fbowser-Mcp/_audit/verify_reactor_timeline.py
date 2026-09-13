# -*- coding: utf-8 -*-
"""用**事件时间线**作为观测口径重新验收反应器(此前用"最终标题"——会被页面自身的标题赋值覆盖, 是错的观测)。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=30, cut=6000):
    try:
        r = urllib.request.Request(
            B + "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": n, "arguments": a}}).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=t).read().decode())
        rr = d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n", " ")[:cut]
    except Exception as ex:
        return "EXC:%s" % ex


def arm(tag, enable, ev):
    raw("browser_kernel_reactor", {"action": "clear"})
    if enable:
        raw("browser_collect", {"action": enable}, 20, 100)
    raw("browser_collect", {"action": "clear"}, 20, 80)
    mark = "MK_%s_%d" % (tag, int(time.time() % 10000))
    raw("browser_kernel_reactor", {"action": "add", "event": ev,
        "code": "document.title='%s'" % mark, "cooldown_ms": 100}, 20, 120)
    raw("browser_navigate", {"url": "https://example.com/?obs=%d" % int(time.time()),
                             "wait_for_load": True}, 30, 100)
    time.sleep(1.2)
    tl = raw("browser_event", {"limit": 100}, 25)
    # 观测: 时间线里是否出现"标题被改成 mark"的 title_changed 事件
    hit = ("title\\\":\\\"%s" % mark) in tl or mark in tl
    print("   %-34s 事件=%-20s 时间线含标记=%s" % (tag, ev, hit))
    return hit


print("== 反应器验收(观测口径: 事件时间线, 而非最终标题) ==")
r1 = arm("RESFAM", "event_resource_enable", "resource_response")
r2 = arm("RESFAM", "event_resource_enable", "resource_request")
r3 = arm("NOFAM", None, "resource_response")
print()
print("   开族+resource_response =", r1, " | 开族+resource_request =", r2, " | 不开族 =", r3)
print("   说明: 开族才记录该族事件 -> 反应器才可能被调用; 不开族时不触发属**正确行为**(但用户看不到这个隐式前提)")
raw("browser_kernel_reactor", {"action": "clear"})
