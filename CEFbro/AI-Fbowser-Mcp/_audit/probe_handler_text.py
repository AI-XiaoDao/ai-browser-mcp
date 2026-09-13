# -*- coding: utf-8 -*-
r"""查清: handler 拒绝文案里 `type=js` 这个子串为什么匹配不上(逐码点检查)。
用法: py -3 _audit\probe_handler_text.py
"""
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=30):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")


t = call("browser_inject", {"type": "handler", "persist": True, "code": "1", "inject_id": "dbg2"})
i = t.find("type=")
print('文本长度 =', len(t))
print('type= 出现位置 =', i)
print('该处 repr =', repr(t[max(0, i - 10):i + 40]))
print("'type=js' in t =", "type=js" in t)
print("'type=js ' in t =", "type=js " in t)
print('码点:', [hex(ord(c)) for c in t[i:i + 12]])
