# -*- coding: utf-8 -*-
"""判定 检查定时监视 是否真被进入并提交求值:
用带副作用的表达式 (window.__w 自增)。若函数每拍都提交, __w 会持续增长;
若 __w 始终未定义 -> 函数没被进入(或提交失败)。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=25, cut=300):
    try:
        r = urllib.request.Request(
            B + "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": n, "arguments": a}}).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=t).read().decode())
        rr = d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n", " ")[:cut]
    except Exception as ex:
        return "EXC:%s" % ex


raw("browser_navigate", {"url": "https://example.com/?wt=%d" % int(time.time()),
                         "wait_for_load": True}, 30, 80)
raw("browser_execute_js", {"code": "window.__w=0"}, 20, 60)
print("1) list(清空前) ->", raw("browser_kernel_watch", {"action": "clear"}, 20, 100))
print("2) start 自增表达式 ->", raw("browser_kernel_watch",
      {"action": "start", "expression": "(window.__w=(window.__w||0)+1)",
       "key": "cnt", "interval_ms": 500}, 20, 160))
for i in (1, 2, 3):
    time.sleep(1.0)
    v = raw("browser_execute_js", {"code": "String(window.__w)"}, 20, 60)
    print("   %ds 后 window.__w = %s" % (i, v))
print("3) list(监视任务是否登记) ->", raw("browser_kernel_watch", {"action": "list"}, 20, 200))
raw("browser_kernel_watch", {"action": "clear"}, 20, 80)
