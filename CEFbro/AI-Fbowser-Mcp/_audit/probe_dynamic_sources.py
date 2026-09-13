# -*- coding: utf-8 -*-
r"""探明可用的"运行期真值"来源: 网络请求ID(给 browser_network_body) 与 异步任务ID(给 mcp_result)。"""
import json
import os
import sys
import time
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


print('--- 1) 异步任务ID来源候选 ---')
for tool, args in (('browser_get_source', {"async_only": True}),
                   ('browser_evaluate', {"code": "1+1", "async_only": True})):
    e, t = call(tool, args)
    print('   %-18s isError=%s %s' % (tool, e, t[:260]))

print('\n--- 2) 网络请求ID来源 ---')
call("browser_navigate", {"url": "https://example.com/?netid=%d" % int(time.time()), "wait_for_load": True})
e, t = call("browser_network", {"action": "list"})
print('   browser_network list: isError=%s len=%d' % (e, len(t)))
print('   %s' % t[:600])
