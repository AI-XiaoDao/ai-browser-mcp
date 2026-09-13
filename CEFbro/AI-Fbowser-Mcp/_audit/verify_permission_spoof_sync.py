# -*- coding: utf-8 -*-
"""验证 browser_permission_spoof 通过**名单路径**(不传 sync_wait)是否一次调用即得结果。

复刻第100轮那次超时的调用形态: 纯 {action:"apply"}, 不带 sync_wait / max_ms / async_only。
再做一次"连续调用多次"的压力臂, 看是否会像第100轮那样在连续调用中变慢/超时。
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
R = []


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


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:220])


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
call("browser_navigate", {"url": "https://example.com/?ps2=1", "wait_for_load": True})

print("== A) 纯 {action:'apply'}(名单路径, 第100轮就是这一形态超时的) ==")
t0 = time.time()
e, t = call("browser_permission_spoof", {"action": "apply"}, 120)
el = time.time() - t0
print("   %.2fs isError=%s | %s" % (el, e, t[:260]))
arm("一次调用即得结果(无超时/无回执)",
    (not e) and ('已伪装' in t) and ('超时' not in t) and ('_async' not in t),
    "%.2fs | %s" % (el, t[:160]))

print("\n== B) 压力臂: 连续 5 次(第100轮是在连续调用其它工具之后才超时的) ==")
times = []
for i in range(5):
    t0 = time.time()
    e, t = call("browser_permission_spoof", {"action": "apply"}, 60)
    el = time.time() - t0
    times.append(el)
    print("   第%d次 %.2fs isError=%s 含已伪装=%s 含超时=%s"
          % (i + 1, el, e, '已伪装' in t, '超时' in t))
arm("连续 5 次均成功且无超时",
    all(x < 5 for x in times), "各次耗时: %s" % ['%.2f' % x for x in times])

print("\n== C) 先跑几个注入类工具再来一次(复刻第100轮的上下文) ==")
call("browser_canvas_noise", {"action": "inject", "level": 1}, 60)
call("browser_inject", {"type": "js", "code": "window.__ps=1"}, 60)
t0 = time.time()
e, t = call("browser_permission_spoof", {"action": "apply"}, 60)
el = time.time() - t0
print("   %.2fs isError=%s | %s" % (el, e, t[:200]))
arm("在注入类工具之后仍成功(第100轮的上下文)", (not e) and ('已伪装' in t) and ('超时' not in t),
    "%.2fs | %s" % (el, t[:160]))

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
