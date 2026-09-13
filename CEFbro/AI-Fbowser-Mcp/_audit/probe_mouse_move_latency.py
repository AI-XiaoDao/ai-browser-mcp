# -*- coding: utf-8 -*-
r"""browser_mouse_move 单调用延迟定位: 分离"鼠标调用本身慢"与"之后的读取慢"。

背景: fastcheck 的 "mouse_move 后 CDP 仍可用" 臂要求 两次调用合计 <3s, 最近实测 5.1s,
而同一时刻 browser_dom_query 单独只要 0.02s => 慢的一定是 browser_mouse_move 自己。
本脚本回答: 它慢在哪(CDP 派发? 退到内核注入? 固定等待?), 以及 CDP 通道事后是否还健康。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
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


def pair(label, args):
    e, t, dt = call("browser_mouse_move", args)
    e2, t2, dt2 = call("browser_dom_query", {"selector": "h1"})
    print('%-38s move=%6.2fs err=%-5s | dom=%5.2fs err=%-5s | 合计 %5.2fs'
          % (label, dt, e, dt2, e2, dt + dt2))
    print('       move 返回: %s' % t.replace('\n', ' ')[:150])
    print('       dom  返回: %s' % t2.replace('\n', ' ')[:90])
    return dt, dt2


print('== 基线: 不注入鼠标, 只量读取 ==')
_, t0, dt0 = call("browser_dom_query", {"selector": "h1"})
print('   browser_dom_query 单独 %.2fs -> %s' % (dt0, t0[:60]))

print('\n== 连续 3 次 mouse_move(x,y) ==')
for i in range(3):
    pair('第%d次 x=300,y=200' % (i + 1), {"x": 300, "y": 200})
    time.sleep(0.3)

print('\n== 会话是否还健康 ==')
e, t, dt = call("browser_execute_js", {"code": "1+1"})
print('   browser_execute_js %.2fs err=%s -> %s' % (dt, e, t[:60]))
e, t, dt = call("browser_cdp_call", {"method": "Runtime.evaluate",
                                     "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"})
print('   browser_cdp_call   %.2fs err=%s -> %s' % (dt, e, t[:60]))
