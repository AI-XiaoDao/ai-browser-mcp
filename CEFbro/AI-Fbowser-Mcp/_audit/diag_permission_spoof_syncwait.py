# -*- coding: utf-8 -*-
"""用请求级 sync_wait 强制同步(不改名单), 复现/排除第100轮那次 20s 超时。

`应同步等待` 的第一条判据就是 `sync_wait`, 所以用它可以在**不改源码**的前提下走同步路径。
  能成功 -> 第100轮的超时是**当时环境**问题(疑似残留状态), 可安全把工具重新纳入名单
  仍超时 -> 是可复现缺陷, 需继续查 查询异步结果 的过滤条件
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
call("browser_navigate", {"url": "https://example.com/?sw=1", "wait_for_load": True})

print("== A) sync_wait:true (强制走同步路径, 预算由 max_ms 决定) ==")
t0 = time.time()
e, t = call("browser_permission_spoof",
            {"action": "apply", "sync_wait": True, "max_ms": 15000}, 120)
el = time.time() - t0
print("   用时 %.2fs isError=%s" % (el, e))
print("   %s" % t[:400])
print()
print("   含超时: %s | 含 _async: %s | 含 '已伪装': %s"
      % ('超时' in t, '_async' in t, '已伪装' in t))

print("\n== B) 对照: 同一工具异步(应立刻回回执) ==")
t0 = time.time()
e2, t2 = call("browser_permission_spoof", {"action": "apply", "async_only": True}, 60)
print("   用时 %.2fs isError=%s -> %s" % (time.time() - t0, e2, t2[:220]))
