# -*- coding: utf-8 -*-
r"""判定 mouse_move 的 ~5s 是"每会话一次性冷启动"还是"每次都有":

用法: py -3 _audit\probe_mouse_warm.py [次数]
在**刚重启**的实例上跑: 第一次慢(冷) 而后续快(热) ⇒ 一次性冷启动; 每次都慢 ⇒ 每次都退化。
在同一次会话里重复跑本脚本还可验证"热态是否持久"。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), dt


print('== browser_mouse_move 连续 %d 次(同一会话) ==' % N)
for i in range(1, N + 1):
    e, t, dt = call("browser_mouse_move", {"x": 100 + i * 7, "y": 120 + i * 5})
    print('   第%d次 %6.2fs err=%-5s %s' % (i, dt, e, t.replace('\n', ' ')[:70]))

print('\n== 对照: browser_reverse_input_cdp(kind=mouse) ==')
e, t, dt = call("browser_reverse_input_cdp", {"kind": "mouse", "type": "mouseMoved",
                                              "x": 250, "y": 250})
print('   reverse_input_cdp(mouse) %6.2fs err=%-5s %s' % (dt, e, t.replace('\n', ' ')[:90]))
e, t, dt = call("browser_reverse_input_cdp", {"kind": "mouse", "type": "mouseMoved",
                                              "x": 260, "y": 260})
print('   reverse_input_cdp(mouse) %6.2fs err=%-5s %s' % (dt, e, t.replace('\n', ' ')[:90]))

print('\n== 对照: browser_cdp_call(Input.dispatchMouseEvent) 直发 ==')
for i in range(2):
    e, t, dt = call("browser_cdp_call",
                    {"method": "Input.dispatchMouseEvent",
                     "params": "{\"type\":\"mouseMoved\",\"x\":270,\"y\":270,\"buttons\":0}"})
    print('   第%d次 %6.2fs err=%-5s %s' % (i + 1, dt, e, t.replace('\n', ' ')[:80]))

print('\n== 收尾: 会话是否健康 ==')
e, t, dt = call("browser_execute_js", {"code": "1+1"})
print('   browser_execute_js %6.2fs err=%-5s %s' % (dt, e, t[:40]))
e, t, dt = call("browser_get_url", {})
print('   browser_get_url    %6.2fs err=%-5s %s' % (dt, e, t[:60]))
