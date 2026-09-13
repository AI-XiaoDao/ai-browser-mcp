# -*- coding: utf-8 -*-
"""干净重启后的对照: 事件族默认全关时, resource_response 反应器规则是否仍能触发?
观测口径 = 事件时间线(不可被页面自身标题赋值覆盖), 不是最终标题。
若触发 -> "事件族"不是隐式前提, 反应器完全可用;
若不触发 -> 存在隐式前提, 应在 add 时自动开族并 auto_prepared 上报。"""
import json
import os
import subprocess
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"
EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker', 'AI-Fbowser-Mcp.exe')


def raw(n, a, t=30, cut=6000):
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


print("== 冷重启(事件族回到默认全关) ==")
subprocess.run(["taskkill", "/F", "/IM", "AI-Fbowser-Mcp.exe"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        h = json.loads(urllib.request.urlopen(B + "/health", timeout=3).read())
        if h.get("tool_count"):
            print("   就绪 tools=%s" % h.get("tool_count"))
            break
    except Exception:
        pass
time.sleep(2.5)

raw("browser_navigate", {"url": "https://example.com/?ctl=1", "wait_for_load": True}, 30, 80)
mark = "CTL_%d" % int(time.time() % 10000)
print("   注册规则 resource_response ->", raw("browser_kernel_reactor",
      {"action": "add", "event": "resource_response",
       "code": "document.title='%s'" % mark, "cooldown_ms": 100}, 20, 120))
raw("browser_navigate", {"url": "https://example.com/?ctl=2", "wait_for_load": True}, 30, 80)
time.sleep(1.5)
tl = raw("browser_event", {"limit": 100}, 25)
print("   时间线含标记 =", mark in tl)
print("   时间线含 resource_response 事件 =", "resource_response" in tl)
print()
print("   判定: 族默认关时反应器仍触发 =", mark in tl)
print("        (若为 True -> 无隐式前提, 反应器可用; 若 False -> 需在 add 时自动开族)")
raw("browser_kernel_reactor", {"action": "clear"}, 20, 80)
