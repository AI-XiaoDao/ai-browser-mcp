# -*- coding: utf-8 -*-
r"""清除上一轮探针持久化的垃圾代理("mcp_probe")。当前实例仍在运行。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
     "params": {"name": "browser_clear_proxy", "arguments": {}}}
r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                           headers={"Content-Type": "application/json"})
try:
    o = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
    rr = o.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
    print('clear_proxy: err=%s %s' % (rr.get("isError"), txt[:100]))
except Exception as ex:
    print('EXC: %r' % ex)
