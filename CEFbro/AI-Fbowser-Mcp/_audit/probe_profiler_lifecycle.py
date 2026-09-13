# -*- coding: utf-8 -*-
"""Profiler 域实测: enable/start/stop 的真实先后依赖。

疑点: browser_reverse_profiler 的 start / start_precise 都**只调 Profiler.enable**,
不调 Profiler.start; 若 start 是必需的, 则 stop 必然报 "not started", 整个工具族形同虚设。
顺序刻意如此: 先 stop(未 start)看内核原话, 再 start, 再 stop。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')


def c(n, a, to=45):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])
                   if i.get("type") == "text").replace('\\"', '"')[:230]


def cdp(m, p=None):
    return c("browser_cdp_call", {"method": m, "params": p or {}})


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
c("browser_navigate", {"url": "https://example.com/?prof=1", "wait_for_load": True})

print("== 全新进程, 直接 stop(未 start) ==")
print("   Profiler.stop                -> %s" % cdp("Profiler.stop"))
print("\n== 只 enable, 再 stop ==")
print("   Profiler.enable              -> %s" % cdp("Profiler.enable"))
print("   Profiler.stop (仅 enable 后) -> %s" % cdp("Profiler.stop"))
print("\n== 正规流程 enable -> start -> stop ==")
print("   Profiler.start               -> %s" % cdp("Profiler.start"))
time.sleep(0.6)
r = cdp("Profiler.stop")
print("   Profiler.stop (start 后)     -> %s" % r[:180])
print("\n== 精确覆盖率(既有工具走的路) ==")
print("   Profiler.startPreciseCoverage-> %s"
      % cdp("Profiler.startPreciseCoverage", {"callCount": True, "detailed": True}))
print("   Profiler.stopPreciseCoverage -> %s" % cdp("Profiler.stopPreciseCoverage"))
print("\n== 采样间隔字段核对 ==")
print("   setSamplingInterval{interval,maxDepth} -> %s"
      % cdp("Profiler.setSamplingInterval", {"interval": 100, "maxDepth": 32}))
