# -*- coding: utf-8 -*-
r"""量"隐藏窗口时 Input.dispatchTouchEvent 到底要多久" —— 决定触摸派发预算该给多少。

背景: 隐藏窗口时 browser_touch_press 8.24s 后**报错**(文案误指"CDP 通道不可用"), 但同一状态下
  · Input.dispatchMouseEvent 约 5.1s 就返回且成功;
  · 直发 browser_cdp_call(Emulation.setTouchEmulationEnabled) 只要 0.01s(说明通道健康、仿真也没问题);
⇒ 怀疑超时发生在 touch 派发本身, 且 >8s。本脚本用直发 CDP 量准它(直发的等待预算比工具内部大)。

用法: py -3 _audit\probe_touch_hidden_cost.py
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
    print('   %-34s %6.2fs err=%-5s %s' % (n, dt, bool(rr.get("isError")), t.replace('\n', ' ')[:100]))
    return bool(rr.get("isError")), t, dt


def cdp(method, params, tag=''):
    e, t, dt = call("browser_cdp_call", {"method": method, "params": json.dumps(params)})
    print('      ↑ %s %s' % (tag, method))
    return dt, e, t


def vis(v):
    call("browser_show_window", {"visible": v})


print('== 可见态基准 ==')
vis(True)
time.sleep(0.8)
cdp("Input.dispatchTouchEvent",
    {"type": "touchStart", "touchPoints": [{"x": 300, "y": 200, "radiusX": 1, "radiusY": 1,
                                            "force": 1, "id": 0}]}, '可见')
cdp("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}, '可见')

print('\n== 隐藏后直发量测(不给工具内部 8s 预算限制) ==')
vis(False)
time.sleep(1.2)
cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 300, "y": 200, "buttons": 0}, '隐藏-鼠标对照')
cdp("Input.dispatchTouchEvent",
    {"type": "touchStart", "touchPoints": [{"x": 305, "y": 205, "radiusX": 1, "radiusY": 1,
                                            "force": 1, "id": 0}]}, '隐藏-触摸按下')
cdp("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 315, "y": 215, "radiusX": 1,
                                                                      "radiusY": 1, "force": 1, "id": 0}]},
    '隐藏-触摸拖动')
cdp("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}, '隐藏-触摸放开')

print('\n== 恢复可见 ==')
vis(True)
time.sleep(0.8)
cdp("Input.dispatchTouchEvent",
    {"type": "touchStart", "touchPoints": [{"x": 320, "y": 220, "radiusX": 1, "radiusY": 1,
                                            "force": 1, "id": 0}]}, '可见-再触摸')
cdp("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}, '可见-放开')
call("browser_execute_js", {"code": "1+1"})
