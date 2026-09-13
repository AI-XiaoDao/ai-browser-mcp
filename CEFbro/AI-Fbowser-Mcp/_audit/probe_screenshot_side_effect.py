# -*- coding: utf-8 -*-
r"""定位: 截图之后 `execute_js` 变慢/超时(实测 30~35s)到底是**截图副作用**还是**验证脚本自身的用法**?

两臂, 每臂独立重启:
  A 臂: 基线 execute_js → 1 次 full_page 截图 → execute_js → 再 2 次截图 → execute_js
  B 臂: 基线 execute_js → 3 次普通截图(800x600) → execute_js
另外观察: 截图回包是"同步拿到图片"还是"异步 task_id 需要 mcp_result"(决定脚本该怎么读)。

用法: py -3 _audit\probe_screenshot_side_effect.py
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


def js_time(tag):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    print('    %-34s isError=%-5s %6.2fs %s' % (tag, e, d, t[:70].replace('\n', ' ')))
    return d


def arm(name, shots):
    print('\n===== %s =====' % name)
    loop.kill_app()
    if not loop.start_app():
        print('  !! 启动失败'); return
    call("browser_navigate", {"url": "https://example.com/?ss=%d" % int(time.time())})
    call("browser_execute_js", {"code":
        "var d=document.createElement('div');d.style.height='5000px';document.body.appendChild(d);'ok'"})
    js_time('①基线')
    for i, args in enumerate(shots, 1):
        e, t, d = call("browser_screenshot", args, to=90)
        kind = 'SYNC-IMG' if 'base64' in t else ('TASK' if 'task_id' in t else 'OTHER')
        print('    截图#%d(%s) isError=%-5s %6.2fs -> %s len=%d' % (i, json.dumps(args, ensure_ascii=False)[:44], e, d, kind, len(t)))
        js_time('   截图#%d 后 execute_js' % i)
        time.sleep(0.3)


arm('A 臂: full_page 截图 x3', [{"format": "png", "full_page": True}] * 3)
arm('B 臂: 普通 800x600 截图 x3', [{"format": "png", "width": 800, "height": 600}] * 3)
