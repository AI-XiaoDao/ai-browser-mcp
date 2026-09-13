# -*- coding: utf-8 -*-
r"""找出台账里缺失(未测)的工具名: 对照 tools/list 与 _tool_ledger.json。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
b = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                           headers={"Content-Type": "application/json"})
o = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
tools = {t["name"] for t in (o.get("result") or {}).get("tools") or []}
print('tools/list count:', len(tools))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tool_ledger.json'), encoding='utf-8') as f:
    ledger = json.load(f)
print('ledger count:', len(ledger))
missing = sorted(tools - set(ledger.keys()))
print('missing(未测):', missing)
