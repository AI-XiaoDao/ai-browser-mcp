# -*- coding: utf-8 -*-
"""先看清两处真实回包再改验收脚本(不要凭猜测改断言)。"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])
                   if i.get("type") == "text")


for label, args in [
    ('A3 hex_encode input=base64 "qw=="', {"action": "hex_encode", "input": "base64", "data": "qw=="}),
    ('A4 hex_encode input=base64 "3q2+7w=="', {"action": "hex_encode", "input": "base64", "data": "3q2+7w=="}),
    ('C4 ts_to_text 0', {"action": "ts_to_text", "timestamp": 0}),
    ('C5 ts_to_text 1700000000', {"action": "ts_to_text", "timestamp": 1700000000}),
    ('C7 ts_to_text 2147483647', {"action": "ts_to_text", "timestamp": 2147483647}),
    ('C8 ts_to_text 2147483648', {"action": "ts_to_text", "timestamp": 2147483648}),
    ('C9 text_to_ts "1970-01-01 08:00:00"', {"action": "text_to_ts", "time_text": "1970-01-01 08:00:00", "chinese": False}),
    ('C10 verify_tz', {"action": "verify_tz"}),
]:
    print('== %s ==' % label)
    print('   %s' % call("browser_time_convert" if label.startswith('C') else "browser_codec", args)[:420])
