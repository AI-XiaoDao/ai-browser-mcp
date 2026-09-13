# -*- coding: utf-8 -*-
"""把 URI 解码的两参四种组合一次跑完, 确认**有没有任何一种**能完整还原 "a%20b%26c%3Dd"。

已知:
  (to_utf8=真, keep=真) -> "a%20b%26c%3Dd" 原样(只还原非 ASCII)
  (to_utf8=真, keep=假) -> 什么都不还原
待测: to_utf8=假 的两种组合 —— CEF 的 convert_to_utf8 关掉后可能是"原始百分号解码"。
"""
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
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


SRC = "a%20b%26c%3Dd"
for utf8 in (True, False):
    for keep in (True, False):
        args = {"data": SRC}
        if utf8 is not True:
            args["to_utf8"] = utf8
        if keep is not True:
            args["keep_escaped"] = keep
        e, t = call("browser_uri_decode", args)
        print('to_utf8=%-5s keep_escaped=%-5s -> %s%s'
              % (utf8, keep, t[:110], '  ★完整还原!' if '"decoded":"a b&c=d"' in t else ''))

print()
# 参考: 同一 source 在页面里用 decodeURIComponent 的结果(证明期望值本身没错)
e, t = call("browser_execute_js", {"code": "decodeURIComponent('a%20b%26c%3Dd')"})
print('页面内 decodeURIComponent 参考结果: %s' % t[:160])
