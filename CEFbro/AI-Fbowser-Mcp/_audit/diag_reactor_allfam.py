# -*- coding: utf-8 -*-
"""开全部事件族后再测 resource_response 规则; 并完整打印事件时间线(上一版脚本截断到200字符, 是我的缺陷)。
目的: 判定"具体事件名对不上"到底是族闸门问题, 还是反应器比对问题。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=30, cut=400):
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


print("1) 全事件族: enable ->", raw("browser_kernel_events_all", {"action": "enable"}, 25, 160))
raw("browser_kernel_reactor", {"action": "clear"})
raw("browser_collect", {"action": "clear"})
MARK = "MARK_ALLFAM_%d" % int(time.time() % 10000)
print("2) 规则 resource_response ->", raw("browser_kernel_reactor",
      {"action": "add", "event": "resource_response",
       "code": "document.title='%s'" % MARK, "cooldown_ms": 100}, 20, 160))
print("3) 导航 ->", raw("browser_navigate",
      {"url": "https://example.com/?allfam=%d" % int(time.time()), "wait_for_load": True}, 30, 120))
time.sleep(1.5)
t = raw("browser_get_title", {}, 20, 80)
print("4) 标题 =", t, "| 触发 =", MARK in t)
print()
print("5) 事件时间线(完整, 看 resource_* 是否真的被记录):")
tl = raw("browser_event", {"limit": 80}, 25, 3000)
print("   ", tl)
print()
print("   含 resource_response =", "resource_response" in tl,
      "| 含 resource_request =", "resource_request" in tl,
      "| 含 load_start =", "load_start" in tl)
raw("browser_kernel_reactor", {"action": "clear"})
