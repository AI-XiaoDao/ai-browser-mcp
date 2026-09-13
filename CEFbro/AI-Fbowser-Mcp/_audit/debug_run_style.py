# -*- coding: utf-8 -*-
r"""诊断: browser_get_run_style 原始回包。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
     "params": {"name": "browser_get_run_style", "arguments": {}}}
r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                           headers={"Content-Type": "application/json"})
o = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
rr = o.get("result") or {}
txt = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
print('RAW:', txt)
