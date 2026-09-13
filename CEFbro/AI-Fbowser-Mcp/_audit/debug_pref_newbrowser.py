# -*- coding: utf-8 -*-
r"""诊断3: pref 是否只对"设置之后新建的浏览器"生效。
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


e, t, d = call("browser_set_preference", {"name": "webkit.webprefs.default_font_size", "value": "24"})
print('set 24: err=%s %s' % (e, t[:60]))
e, t, d = call("browser_create", {"url": "https://example.com/?prefprobe=%d" % int(time.time()),
                                  "background": True, "tag": "pref_probe_146"}, to=90)
print('create bg: err=%s %.2fs %s' % (e, d, t[:60]))
time.sleep(1.0)
e, t, d = call("browser_list", {})
print('list: %s' % t[:300])
e, t, d = call("browser_execute_js", {"browser_id": 2,
                                      "code": "String(getComputedStyle(document.body).fontSize)"}, to=60)
print('browser2 字号(期望24px): err=%s %s' % (e, t[:120]))
# 清理: 关掉第二浏览器
e, t, d = call("browser_close", {"browser_id": 2}, to=60)
print('close 2: err=%s %s' % (e, t[:80]))
# 主浏览器健康
e, t, d = call("browser_execute_js", {"code": "1+1"})
print('主 execute_js: err=%s %.2fs %s' % (e, d, t[:60]))
