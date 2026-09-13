# -*- coding: utf-8 -*-
"""验证假设: 反应器规则不触发, 是因为**对应事件族未启用**(各事件处理函数外层有族级闸门)。
若先 browser_collect event_resource_enable 再注册 resource_response 规则, 应当能触发。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=30):
    try:
        r = urllib.request.Request(
            B + "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": n, "arguments": a}}).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=t).read().decode())
        rr = d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n", " ")[:110]
    except Exception as ex:
        return "EXC:%s" % ex


def arm(tag, enable_action, ev, mark):
    raw("browser_kernel_reactor", {"action": "clear"})
    if enable_action:
        print("   %-30s 事件族: %s" % (tag, raw("browser_collect", {"action": enable_action})))
    else:
        print("   %-30s 事件族: 未开启" % tag)
    print("   %-30s 规则  : %s" % ("", raw("browser_kernel_reactor",
          {"action": "add", "event": ev, "code": "document.title='%s'" % mark, "cooldown_ms": 100})))
    raw("browser_navigate", {"url": "https://example.com/?fam=%d" % int(time.time() * 1000 % 99999),
                             "wait_for_load": True}, 30)
    time.sleep(1.5)
    t = raw("browser_get_title", {})
    return t, (mark in t)


M1 = "MARK_NOFAM_%d" % int(time.time() % 10000)
M2 = "MARK_FAM_%d" % int(time.time() % 10000)

print("== 对照实验: 事件族闸门假设 ==")
t1, ok1 = arm("A) 不开族", None, "resource_response", M1)
print("   -> 标题=%-20s 触发=%s" % (t1[:20], ok1))
t2, ok2 = arm("B) 开 event_resource 族", "event_resource_enable", "resource_response", M2)
print("   -> 标题=%-20s 触发=%s" % (t2[:20], ok2))
print()
print("   假设成立(开族才触发) =", (ok1 is False and ok2 is True))
raw("browser_kernel_reactor", {"action": "clear"})
