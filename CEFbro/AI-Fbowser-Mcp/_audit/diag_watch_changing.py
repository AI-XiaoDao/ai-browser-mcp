# -*- coding: utf-8 -*-
"""决定性测试: 监视每次采样必然变化的表达式 Date.now()。
若仍无 watch_changed -> 比对/记录路径确实坏了;
若出现 -> 之前用 document.title(常值) 测不出来, 是我的测试表达有问题。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=25, cut=4000):
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


raw("browser_navigate", {"url": "https://example.com/?wn=%d" % int(time.time()),
                         "wait_for_load": True}, 30, 80)
raw("browser_kernel_watch", {"action": "clear"}, 20, 80)
print("1) start 必然变化的表达式 ->", raw("browser_kernel_watch",
      {"action": "start", "expression": "String(Date.now())", "key": "ts",
       "interval_ms": 500}, 20, 160))
time.sleep(4.0)
tl = raw("browser_event", {"limit": 200}, 25)
print("2) 时间线含 watch_changed =", "watch_changed" in tl)
i = tl.find("watch_changed")
print("   片段:", tl[max(0, i - 20):i + 260] if i >= 0 else "(无)")
raw("browser_kernel_watch", {"action": "clear"}, 20, 80)
