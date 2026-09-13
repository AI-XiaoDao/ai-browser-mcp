# -*- coding: utf-8 -*-
r"""最后一个判别实验: **只重复工具路径的 get_document**(不做编辑), 看通道在哪一步死。
   A: 工具路径 get_document ×3(每次之后 execute_js)
   B: 对照: 裸 browser_cdp_call DOM.getDocument ×3(每次之后 execute_js)
两臂各用干净实例。

用法: py -3 _audit\probe_dom_repeat.py
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


def health(tag):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    print('       %-18s execute_js: %.2fs %s' % (tag, d, 'OK' if d < 1 else '慢/坏'))
    return d


def arm(name, use_tool):
    print('\n===== %s =====' % name)
    loop.kill_app()
    if not loop.start_app():
        print('  !! 启动失败'); return
    call("browser_navigate", {"url": "https://example.com/?rp=%d" % int(time.time())})
    health('基线')
    for i in (1, 2, 3):
        if use_tool:
            e, t, d = call("browser_vip_dom_get_document", {"depth": 3}, to=60)
        else:
            e, t, d = call("browser_cdp_call", {"method": "DOM.getDocument", "params": "{\"depth\":3,\"pierce\":false}"}, to=60)
        print('   DOM#%d isError=%-5s %6.2fs len=%d' % (i, e, d, len(t)))
        health('DOM#%d 后' % i)


arm('A 工具路径 get_document ×3', True)
arm('B 裸 CDP DOM.getDocument ×3', False)
