# -*- coding: utf-8 -*-
r"""诊断: ①强制显示窗口后内核滚轮是否生效; ②CDP版 browser_mouse_wheel 对照(应快且真滚)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def scrollY():
    e, t, d = call("browser_execute_js", {"code": "window.scrollY"}, to=60)
    return t, d


# 当前实例是上一轮⑦重启后的干净实例
e, t, d = call("browser_execute_js",
               {"code": "for(var i=0;i<60;i++){var d=document.createElement('div');d.textContent='row'+i+' '+('x'.repeat(200));document.body.appendChild(d)}window.scrollTo(0,0);'tall'"}, to=60)
print('造长页面: err=%s' % e)

print('== A 强制显示窗口后内核滚轮 ==')
e, t, d = call("browser_show_window", {"visible": True}, to=60)
print('  show_window: err=%s %.2fs %s' % (e, d, t[:80]))
e, t, d = call("browser_vip_mouse_wheel", {"x": 300, "y": 200, "delta_y": 400}, to=60)
print('  vip_wheel: err=%s %.2fs %s' % (e, d, t[:60]))
t2, d2 = scrollY()
print('  scrollY(毒化回读, 慢属正常): %s %.2fs' % (t2[:80], d2))

print('== B 重启后 CDP 版对照 ==')
import loop
loop.kill_app()
loop.start_app()
call("browser_navigate", {"url": "https://example.com/?wheelcdp=%d" % int(time.time())})
call("browser_execute_js",
     {"code": "for(var i=0;i<60;i++){var d=document.createElement('div');d.textContent='row'+i+' '+('x'.repeat(200));document.body.appendChild(d)}window.scrollTo(0,0);'tall'"}, to=60)
e, t, d = call("browser_mouse_wheel", {"x": 300, "y": 200, "delta_y": 400}, to=60)
print('  cdp wheel: err=%s %.2fs %s' % (e, d, t[:80]))
t3, d3 = scrollY()
print('  scrollY: %s %.2fs' % (t3[:80], d3))
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
print('  cdp 后 execute_js: err=%s %.2fs %s' % (e, d, t[:40]))
