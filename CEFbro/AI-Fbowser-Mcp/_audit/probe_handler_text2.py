# -*- coding: utf-8 -*-
r"""继续查: 文案里每一处 "type" 之后的码点到底长什么样(找是不是全角/近似字符)。
用法: py -3 _audit\probe_handler_text2.py
"""
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


t = call("browser_inject", {"type": "handler", "persist": True, "code": "1", "inject_id": "dbg3"})
print('总长 %d' % len(t))
pos = -1
while True:
    pos = t.find("type", pos + 1)
    if pos < 0:
        break
    seg = t[pos:pos + 14]
    print('  @%-4d %r  码点=%s' % (pos, seg, [hex(ord(c)) for c in seg[:12]]))
i = t.find("persist")
print('\npersist 附近: %r' % t[max(0, i - 24):i + 30])
