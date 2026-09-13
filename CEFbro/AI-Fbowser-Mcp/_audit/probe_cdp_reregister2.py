# -*- coding: utf-8 -*-
r"""重做: 截图后 CDP 坏掉, **真正的**注销+重挂观察者能否救回?
上一版失败是因为 `browser_vip_enable_devtools_observer {enable:false}` 被它自己的守卫拒绝
(它只认字符串 true/false/1/0/on/off, 布尔 false 会被当成"无法识别") —— 即**根本没执行注销**。

本版用字符串取值: enable="false"(注销) → enable="true"(重挂)。

用法: py -3 _audit\probe_cdp_reregister2.py
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
    print('    %-38s isError=%-5s %6.2fs %s' % (tag, e, d, t[:100].replace('\n', ' ')))
    return e, t, d


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?rg3=%d" % int(time.time())})
show('基线 execute_js', 'browser_execute_js', {"code": "1+1"})
show('截图', 'browser_screenshot', {"format": "png", "width": 600, "height": 400})
show('截图后 execute_js(预期 ~30s)', 'browser_execute_js', {"code": "2+2"})
print('  -- 真·注销(enable="false") --')
show('enable="false"', 'browser_vip_enable_devtools_observer', {"enable": "false"})
show('注销后 execute_js(通道应仍坏)', 'browser_execute_js', {"code": "3+3"})
print('  -- 真·重挂(enable="true") --')
show('enable="true"', 'browser_vip_enable_devtools_observer', {"enable": "true"})
show('重挂后 execute_js(希望 0.03s)', 'browser_execute_js', {"code": "4+4"})
show('重挂后原始 CDP evaluate', 'browser_cdp_call',
     {"method": "Runtime.evaluate", "params": "{\"expression\":\"8+8\",\"returnByValue\":true}"})
show('重挂后再截一张图', 'browser_screenshot', {"format": "png", "width": 300, "height": 200})
show('第二次截图后 execute_js', 'browser_execute_js', {"code": "5+5"})
