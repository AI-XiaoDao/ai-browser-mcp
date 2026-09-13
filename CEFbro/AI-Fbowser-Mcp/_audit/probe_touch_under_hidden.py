# -*- coding: utf-8 -*-
r"""摸清"隐藏态下 touch_press 超时/失败"之后会话到底处于什么状态(只读+两次触摸, 不做注入)。"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=90, show=True):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    t = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
    if show:
        print('   %-28s %6.2fs err=%-5s %s' % (n, dt, bool(rr.get("isError")), t.replace('\n', ' ')[:170]))
    return bool(rr.get("isError")), t, dt


def style():
    e, t, dt = call("browser_get_window_style", {}, show=False)
    try:
        return int(json.loads(t).get("style", "0"))
    except Exception:
        return -1


print('== 当前状态 ==')
s = style()
print('   GWL_STYLE=%s (WS_VISIBLE=%s)' % (s, bool(s & 0x10000000)))
call("browser_execute_js", {"code": "1+1"}, show=True)

print('\n== 可见态: 触摸三件套 ==')
call("browser_touch_press", {"x": 300, "y": 200})
call("browser_touch_move", {"x": 310, "y": 210})
call("browser_touch_release", {})

print('\n== 隐藏窗口后: 触摸三件套 + 会话健康 ==')
call("browser_show_window", {"visible": False}, show=True)
time.sleep(1.0)
call("browser_touch_press", {"x": 320, "y": 220})
call("browser_touch_release", {})
call("browser_execute_js", {"code": "1+1"}, show=True)
call("browser_dom_query", {"selector": "h1"}, show=True)
call("browser_cdp_call", {"method": "Emulation.setTouchEmulationEnabled",
                          "params": "{\"enabled\":true,\"maxTouchPoints\":5}"}, show=True)

print('\n== 恢复可见后: 触摸三件套 ==')
call("browser_show_window", {"visible": True}, show=True)
time.sleep(1.0)
call("browser_touch_press", {"x": 330, "y": 230})
call("browser_touch_release", {})
call("browser_execute_js", {"code": "1+1"}, show=True)
