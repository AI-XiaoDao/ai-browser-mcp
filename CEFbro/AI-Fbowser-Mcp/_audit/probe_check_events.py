# -*- coding: utf-8 -*-
r"""查看当前事件库里的 download_* 记录(不做任何触发), 用于判断"是没写库还是查询没取到"。"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


for label, args in (('时间线', {"limit": 40}),
                    ('download_*', {"event_type": "download_*", "limit": 20}),
                    ('download_complete', {"event_type": "download_complete", "limit": 5}),
                    ('download_progress', {"event_type": "download_progress", "limit": 5})):
    e, t = call("browser_event", args)
    print('== %s == isError=%s len=%d' % (label, e, len(t)))
    print('   %s' % t[:500].replace('\\"', '"'))
    print()
