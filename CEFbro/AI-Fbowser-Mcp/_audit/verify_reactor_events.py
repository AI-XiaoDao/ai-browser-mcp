# -*- coding: utf-8 -*-
"""反应器事件级验收 —— 用"不会被导航覆盖"的观测方式，判定各事件名是否真的匹配。

设计:
  · 晚期事件(resource_response): 事件在文档载入后才到, 即时改标题即可观测。
  · 早期事件(navigate): 事件在导航开始时到, 此时新文档还没建立 —— 即时改标题会被新页面覆盖,
    因此用 setTimeout 延迟 2.5 秒再写, 等载入完成后落地。
  · 对照: 故意用一个不存在的事件名, 应当**不触发**(证明匹配是真的在比对, 而不是无脑执行)。
"""
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
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n", " ")[:120]
    except Exception as ex:
        return "EXC:%s" % ex


def arm(tag, ev, code, wait=1.2):
    raw("browser_kernel_reactor", {"action": "clear"})
    raw("browser_kernel_reactor", {"action": "add", "event": ev, "code": code, "cooldown_ms": 200})
    raw("browser_navigate", {"url": "https://example.com/?ev=%d" % int(time.time() * 1000 % 999999),
                             "wait_for_load": True}, 30)
    time.sleep(wait)
    t = raw("browser_get_title", {})
    return t, ("MARK" in t)


M1 = "MARK_RESP_%d" % int(time.time() % 10000)
M2 = "MARK_NAV_%d" % int(time.time() % 10000)
M3 = "MARK_NONE_%d" % int(time.time() % 10000)

print("== 反应器事件级验收 ==")
t1, ok1 = arm("A) resource_response + 即时改标题", "resource_response",
              "document.title='%s'" % M1)
print("   A resource_response : 标题=%-22s 触发=%s" % (t1[:22], ok1))

t2, ok2 = arm("B) navigate + 延迟2.5秒改标题", "navigate",
              "setTimeout(function(){document.title='%s'},2500)" % M2, wait=4.0)
print("   B navigate(延迟写)   : 标题=%-22s 触发=%s" % (t2[:22], ok2))

t3, ok3 = arm("C) 不存在的事件名(对照, 应不触发)", "no_such_event_xyz",
              "document.title='%s'" % M3)
print("   C 不存在的事件名     : 标题=%-22s 触发=%s(期望 False)" % (t3[:22], ok3))

print()
print("   判定: 匹配逻辑真的在工作 =", (ok3 is False))
print("         resource_response 匹配 =", ok1, " | navigate 匹配 =", ok2)
raw("browser_kernel_reactor", {"action": "clear"})
