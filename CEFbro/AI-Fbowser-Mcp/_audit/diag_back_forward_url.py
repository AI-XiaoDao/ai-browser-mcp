# -*- coding: utf-8 -*-
"""诊断 back/forward 验收为何时好时坏: 是"真的退错了页", 还是 `browser_get_url` 读的是**缓存值**?

两个独立观测量对照:
  · browser_get_url      -> 可能读 浏览器容器.最新地址(由事件回填的缓存)
  · browser_evaluate location.href -> 页面**实时**真值
若两者不一致 -> 说明是**缓存滞后**, 不是导航错; 若一致且都不是期望页 -> 才是真问题。
"""
import json
import os
import re
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
A = "https://example.com/?fA=1"
B = "https://example.com/?fB=2"


def call(n, a, to=120):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def live_url():
    e, t = call("browser_evaluate", {"code": "location.href"}, 40)
    m = re.search(r'"(https?://[^"]*)"', t)
    return m.group(1) if m else t.strip()[:60]


def cached_url():
    return call("browser_get_url", {}, 40)[1].strip()[:80]


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

print("== 准备: A -> B ==")
call("browser_navigate", {"url": A, "wait_for_load": True}, 90)
call("browser_navigate", {"url": B, "wait_for_load": True}, 90)
time.sleep(0.6)
print("   缓存URL=%s | 实时URL=%s" % (cached_url(), live_url()))

print("\n== back ==")
call("browser_back", {}, 90)
for d in (0.1, 0.5, 1.5):
    time.sleep(d)
    print("   +%.1fs 缓存URL=%s | 实时URL=%s" % (d, cached_url(), live_url()))

print("\n== forward ==")
call("browser_forward", {}, 90)
for d in (0.1, 0.5, 1.5):
    time.sleep(d)
    print("   +%.1fs 缓存URL=%s | 实时URL=%s" % (d, cached_url(), live_url()))

print("\n== 历史长度(实时) ==")
print("   history.length = %s" % live_url() and call("browser_evaluate",
      {"code": "String(history.length)"}, 40)[1].strip()[:40])
