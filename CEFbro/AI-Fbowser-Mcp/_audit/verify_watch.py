# -*- coding: utf-8 -*-
"""验证 browser_kernel_watch 是否真在采样: 启动监视 -> 改变被监视值 -> 时间线里是否出现 watch_changed。
观测口径 = 事件时间线(可靠), 不是最终状态。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=30, cut=8000):
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


print("== browser_kernel_watch 是否真在采样 ==")
raw("browser_navigate", {"url": "https://example.com/?w=%d" % int(time.time()),
                         "wait_for_load": True}, 30, 100)
key = "wk%d" % int(time.time() % 10000)
print("1) 启动监视 key=%s (interval 1000ms) ->" % key,
      raw("browser_kernel_watch",
          {"action": "start", "expression": "document.title", "key": key,
           "interval_ms": 1000}, 25, 200))
print("2) 改变被监视值(document.title) ->",
      raw("browser_execute_js", {"code": "document.title='WATCHED_A'"}, 20, 100))
time.sleep(3.0)   # 至少 2~3 个采样周期
print("3) 再改一次 ->", raw("browser_execute_js", {"code": "document.title='WATCHED_B'"}, 20, 100))
time.sleep(3.0)
tl = raw("browser_event", {"limit": 200}, 25)
print("4) 时间线含 watch_changed =", "watch_changed" in tl)
print("   时间线含 WATCHED_A/B =", ("WATCHED_A" in tl) or ("WATCHED_B" in tl))
i = tl.find("watch_changed")
if i >= 0:
    print("   片段:", tl[max(0, i - 30):i + 220])
raw("browser_kernel_watch", {"action": "clear"}, 20, 100)
