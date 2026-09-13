# -*- coding: utf-8 -*-
r"""验收: browser_startup_args 只读回执工具是否可用(以及初始状态是否如实)。"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=45):
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


for label, args in (('get(缺省)', {}), ('list', {"action": "list"})):
    e, t = call("browser_startup_args", args)
    print('== %s == isError=%s' % (label, e))
    print('   %s' % t[:700])
    print()

# 只读回执工具不应改变任何状态: 再查一次应完全一致
e1, t1 = call("browser_startup_args", {})
e2, t2 = call("browser_startup_args", {})
print('两次调用一致(纯只读): %s' % (t1 == t2))
