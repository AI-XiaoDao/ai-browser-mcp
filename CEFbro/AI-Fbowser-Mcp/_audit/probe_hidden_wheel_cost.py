# -*- coding: utf-8 -*-
r"""量"隐藏窗口时 mouseWheel 要多久"(决定 browser_mouse_wheel 是否需要与触摸同样的快速失败守卫)。

已知(本轮实测): 隐藏态 mouseMoved 5.08s / mousePressed·Released 0.03s / dispatchTouchEvent 30s 不返回。
滚轮走的是合成器的滚动管线, 与 hover 不同, 必须单独量。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=120):
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
    return bool(rr.get("isError")), t, dt


def cdp(method, params, tag):
    e, t, dt = call("browser_cdp_call", {"method": method, "params": json.dumps(params)})
    print('   %-30s %6.2fs err=%-5s %s' % (tag, dt, e, t.replace('\n', ' ')[:60]))
    return dt


def js(expr):
    e, t, dt = call("browser_execute_js", {"code": expr})
    try:
        return json.loads(t).get("message", "")
    except Exception:
        return t


def vis(v):
    call("browser_show_window", {"visible": v})


print('== 页面准备(注入高页面以便滚动可观测) ==')
vis(True)
time.sleep(0.6)
js("document.body.insertAdjacentHTML('beforeend',"
   "'<div style=\"height:3000px\">tall</div>'); window.scrollTo(0,0); 'ok'")
print('   初始 scrollY =', js("String(window.pageYOffset)"))

print('\n== 可见态: 滚轮直发 ==')
cdp("Input.dispatchMouseEvent",
    {"type": "mouseWheel", "x": 200, "y": 200, "deltaX": 0, "deltaY": 120}, '可见 mouseWheel')
time.sleep(0.4)
print('   scrollY =', js("String(window.pageYOffset)"))

print('\n== 隐藏态: 滚轮直发(直发预算 30s, 不受工具内部 8s 限制) ==')
vis(False)
time.sleep(1.2)
cdp("Input.dispatchMouseEvent",
    {"type": "mouseWheel", "x": 200, "y": 200, "deltaX": 0, "deltaY": 120}, '隐藏 mouseWheel')
time.sleep(0.4)
print('   scrollY =', js("String(window.pageYOffset)"))

print('\n== 隐藏态: 工具本身(内部预算 8s) ==')
e, t, dt = call("browser_mouse_wheel", {"x": 200, "y": 200, "delta_y": 120})
print('   browser_mouse_wheel %6.2fs err=%-5s %s' % (dt, e, t.replace('\n', ' ')[:130]))
time.sleep(0.4)
print('   scrollY =', js("String(window.pageYOffset)"))

print('\n== 恢复可见: 对照 ==')
vis(True)
time.sleep(0.8)
e, t, dt = call("browser_mouse_wheel", {"x": 200, "y": 200, "delta_y": 120})
print('   browser_mouse_wheel %6.2fs err=%-5s %s' % (dt, e, t.replace('\n', ' ')[:130]))
time.sleep(0.4)
print('   scrollY =', js("String(window.pageYOffset)"))
js("(function(){var d=document.querySelectorAll('div');for(var i=0;i<d.length;i++)"
   "if(d[i].style.height==='3000px')d[i].remove();window.scrollTo(0,0);return 'cleanup'})()")
