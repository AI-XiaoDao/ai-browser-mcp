# -*- coding: utf-8 -*-
"""反应器最终验收: 用**真实存在**的事件名 navigate 注册规则, 导航后标题应被改掉。
(此前用文档里写的 load_end —— 该事件名不存在, 规则会被接受但永不触发。)"""
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
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n", " ")[:140]
    except Exception as ex:
        return "EXC:%s" % ex


MARK = "MARK_NAV_%d" % int(time.time() % 10000)
print("== 反应器验收: 真实事件名 navigate ==")
print("   1) 注册规则:", raw("browser_kernel_reactor",
                             {"action": "add", "event": "navigate",
                              "code": "document.title='%s'" % MARK, "cooldown_ms": 200}))
print("   2) 导航     :", raw("browser_navigate",
                             {"url": "https://example.com/?nav=%d" % int(time.time()), "wait_for_load": True}, 30))
time.sleep(1.2)
t = raw("browser_get_title", {})
print("   3) 标题     :", t)
print("   >>> 用真实事件名触发 =", MARK in t)
raw("browser_kernel_reactor", {"action": "clear"})
