# -*- coding: utf-8 -*-
r"""定位(关键): 截图之后 **CDP 通道到底怎么了** —— 逐项对照, 找出是哪一环坏掉。

已知(两臂实测): 任意截图(整页或普通)之后, 下一条 CDP 类工具要 30~35s(有时直接超时失败);
`execute_js` 能返回正确值, 说明它最终走了**原生回退**而不是 CDP。

本探针在**同一实例**内按顺序量:
  ① 基线 execute_js / 原始 CDP Runtime.evaluate / cdp_status
  ② 截一张图
  ③ 逐项复测: 原始 CDP Runtime.evaluate、execute_js、cdp_status、dom_query、debugger_enable、browser_status
判据: 谁变慢/变坏, 就锁定在那一环。

用法: py -3 _audit\probe_screenshot_cdp_state.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

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


def show(tag, n, a=None, to=90):
    e, t, d = call(n, a, to)
    print('    %-30s isError=%-5s %6.2fs %s' % (tag, e, d, t[:110].replace('\n', ' ')))
    return e, t, d


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?cdpst=%d" % int(time.time())})

print('== ① 截图前 ==')
show('execute_js', 'browser_execute_js', {"code": "1+1"})
show('原始 CDP Runtime.evaluate', 'browser_cdp_call',
     {"method": "Runtime.evaluate", "params": "{\"expression\":\"2+2\",\"returnByValue\":true}"})
show('cdp_status', 'browser_cdp_status', {})

print('\n== ② 截一张图(800x600) ==')
show('screenshot', 'browser_screenshot', {"format": "png", "width": 800, "height": 600})

print('\n== ③ 截图后逐项复测 ==')
show('原始 CDP Runtime.evaluate', 'browser_cdp_call',
     {"method": "Runtime.evaluate", "params": "{\"expression\":\"3+3\",\"returnByValue\":true}"})
show('execute_js', 'browser_execute_js', {"code": "4+4"})
show('cdp_status', 'browser_cdp_status', {})
show('dom_query', 'browser_dom_query', {"selector": "h1"})
show('debugger_enable', 'browser_debugger_enable', {})
show('browser_status(原生)', 'browser_status', {})
show('再截图一张', 'browser_screenshot', {"format": "png", "width": 400, "height": 300})
show('截图后又 execute_js', 'browser_execute_js', {"code": "5+5"})
