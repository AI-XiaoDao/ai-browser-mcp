# -*- coding: utf-8 -*-
r"""诊断: 补丁 Q 的 CDP getDocument 路径为何 timeout? (先干净重启, 再逐步对照)
用法: py -3 _audit\probe_getdoc_path.py
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


def call(n, a=None, to=60):
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


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?gd=%d" % int(time.time())})
e, t, d = call("browser_execute_js", {"code": "1+1"})
print('基线 execute_js: isError=%s %.2fs %s' % (e, d, t[:40]))

print('\n[A] 裸 CDP: browser_cdp_call DOM.getDocument')
e, t, d = call("browser_cdp_call", {"method": "DOM.getDocument", "params": "{\"depth\":3,\"pierce\":false}"}, to=60)
print('    isError=%s %.2fs len=%d' % (e, d, len(t)))
print('    %s' % t[:200])

print('\n[B] 工具路径: browser_vip_dom_get_document(默认 cdp)')
e, t, d = call("browser_vip_dom_get_document", {"depth": 3}, to=60)
print('    isError=%s %.2fs len=%d' % (e, d, len(t)))
print('    %s' % t[:300])

print('\n[C] 再来一次工具路径(排除首次抖动)')
e, t, d = call("browser_vip_dom_get_document", {"depth": 3}, to=60)
print('    isError=%s %.2fs len=%d' % (e, d, len(t)))
print('    %s' % t[:300])

print('\n[D] 收尾 execute_js')
e, t, d = call("browser_execute_js", {"code": "2+2"})
print('    isError=%s %.2fs %s' % (e, d, t[:40]))
