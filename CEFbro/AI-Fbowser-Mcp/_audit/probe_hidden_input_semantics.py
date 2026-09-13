# -*- coding: utf-8 -*-
r"""细化"隐藏态输入语义": 鼠标移动/按下/抬起各自的成本, 以及**点击是否真的到达页面**(页面侧预言机)。

为什么必须做: 慢因文案里写了"每条 CDP Input 命令都固定约5秒", 而实测 mouse_click(按下+抬起) 在隐藏态
只要 0.05s —— 若不同事件类型成本不同, 文案就必须改准; 若按下/抬起只是"CDP 答应了但页面没收到",
那就是**假成功**, 更要说清楚。

做法: 动态注入一个固定坐标的测试按钮 + 计数器, 用页面侧计数当预言机(不依赖被测工具自述)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
BTN = "occ_probe_btn"


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


def js(expr, show=True):
    e, t, dt = call("browser_execute_js", {"code": expr})
    v = ""
    try:
        v = json.loads(t).get("message", "")
    except Exception:
        v = t
    if show:
        print('   js %-46s -> %s (%.2fs)' % (expr[:46], str(v)[:40], dt))
    return v


def cdp(method, params, tag):
    e, t, dt = call("browser_cdp_call", {"method": method, "params": json.dumps(params)})
    print('   %-34s %6.2fs err=%-5s' % (tag, dt, e))
    return dt


def vis(v):
    call("browser_show_window", {"visible": v})


def style():
    try:
        return int(json.loads(call("browser_get_window_style", {})[1]).get("style", "0"))
    except Exception:
        return -1


print('== 页面现状 ==')
print('   URL  :', js("location.href"))
print('   标题 :', js("document.title"))
print('   h1   :', js("(document.querySelector('h1')||{}).textContent||'__NO_H1__'"))

print('\n== 注入测试按钮与页面侧计数器 ==')
vis(True)
time.sleep(0.6)
js("(function(){var o=document.getElementById('%s');if(o)o.remove();"
   "window.__occ={move:0,down:0,up:0,click:0};"
   "var b=document.createElement('button');b.id='%s';b.textContent='occ';"
   "b.style.cssText='position:fixed;left:40px;top:120px;width:120px;height:40px;z-index:2147483647';"
   "b.addEventListener('mousemove',function(){window.__occ.move++});"
   "b.addEventListener('mousedown',function(){window.__occ.down++});"
   "b.addEventListener('mouseup',function(){window.__occ.up++});"
   "b.addEventListener('click',function(){window.__occ.click++});"
   "document.body.appendChild(b);return JSON.stringify(window.__occ)})()")
print('   坐标: 按钮中心 (100,140)')

print('\n== 可见态: 直发真实事件序列 ==')
cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 100, "y": 140, "buttons": 0}, '可见 mouseMoved')
cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 100, "y": 140, "button": "left", "clickCount": 1}, '可见 mousePressed')
cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 100, "y": 140, "button": "left", "clickCount": 1}, '可见 mouseReleased')
time.sleep(0.3)
print('   页面侧计数:', js("JSON.stringify(window.__occ)"))

print('\n== 隐藏窗口: 同样序列 ==')
vis(False)
time.sleep(1.2)
print('   WS_VISIBLE=', bool(style() & 0x10000000))
cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 100, "y": 140, "buttons": 0}, '隐藏 mouseMoved')
cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 100, "y": 140, "button": "left", "clickCount": 1}, '隐藏 mousePressed')
cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 100, "y": 140, "button": "left", "clickCount": 1}, '隐藏 mouseReleased')
time.sleep(0.3)
print('   页面侧计数:', js("JSON.stringify(window.__occ)"))

print('\n== 隐藏态用工具点击同一坐标(看工具自述 vs 页面事实) ==')
e, t, dt = call("browser_mouse_click", {"x": 100, "y": 140})
print('   browser_mouse_click  %.2fs err=%s %s' % (dt, e, t.replace('\n', ' ')[:110]))
time.sleep(0.3)
print('   页面侧计数:', js("JSON.stringify(window.__occ)"))

print('\n== 恢复可见: 再点一次(对照页面确实会响应) ==')
vis(True)
time.sleep(0.8)
e, t, dt = call("browser_mouse_click", {"x": 100, "y": 140})
print('   browser_mouse_click  %.2fs err=%s %s' % (dt, e, t.replace('\n', ' ')[:110]))
time.sleep(0.3)
print('   页面侧计数:', js("JSON.stringify(window.__occ)"))

print('\n== 清理测试按钮 ==')
js("(function(){var o=document.getElementById('%s');if(o)o.remove();return 'removed'})()" % BTN)
