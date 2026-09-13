# -*- coding: utf-8 -*-
r"""确认 mcp_result 的 request_id 契约: 它到底按什么键取结果?

实测线索: 用 request_id="1" 调用成功, 并回出**上一次调用**(JSON-RPC id=1)的结果。
若按"客户端 JSON-RPC id"取值, 那么换一个独特 id(如 4242)先调一次工具, 再用 request_id="4242"
就应能取回那次调用的结果。这条契约决定了台账探针该怎么给真值(原来用假 id "mcp_probe" 恒失败)。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, rid=1, to=60):
    b = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    t = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
    return bool(rr.get("isError")), t


print('== A. 用独特 id=4242 调一个可辨识的工具 ==')
e, t = call("browser_execute_js", {"code": "'MARKER-4242'"}, rid=4242)
print('   调 execute_js(id=4242) -> err=%s %s' % (e, t[:120]))

print('\n== B. 用 mcp_result 按 4242 取 ==')
e, t = call("mcp_result", {"request_id": "4242", "consume": True})
print('   -> err=%s %s' % (e, t[:300]))

print('\n== C. 负对照: 一个从未用过的 id ==')
e, t = call("mcp_result", {"request_id": "999042", "consume": True})
print('   -> err=%s %s' % (e, t[:200]))

print('\n== D. 用 id=7777 做一次"等待型"调用后取 ==')
e, t = call("browser_wait", {"what": "load_end", "timeout_ms": 1500}, rid=7777)
print('   调 browser_wait(id=7777) -> err=%s %s' % (e, t[:160]))
e, t = call("mcp_result", {"request_id": "7777", "consume": True})
print('   取 7777 -> err=%s %s' % (e, t[:220]))
