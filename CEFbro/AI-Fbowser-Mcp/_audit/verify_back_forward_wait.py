# -*- coding: utf-8 -*-
"""验收 browser_back / browser_forward 的 wait_for_load（默认真）。

关键问题: **历史导航会不会触发 load_end**?
  · 会 -> 默认真即可(调用返回时页面已载入), 与 navigate/reload 一致;
  · 不会(命中 bfcache 只换文档不重新加载) -> 会表现为**超时**, 那时必须把默认改为假,
    并让调用方显式传 wait_for_load:true。
流程: 访问 A -> 访问 B -> back(默认) -> 看是否快速成功且 URL 回到 A -> forward -> 回到 B。
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
A = "https://example.com/?navA=1"
B = "https://example.com/?navB=2"
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


def url_now():
    return call("browser_get_url", {}, 40)[1].strip()[:80]


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:240])


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

print("== 准备: 依次访问 A 再访问 B(建立历史) ==")
call("browser_navigate", {"url": A, "wait_for_load": True}, 90)
call("browser_navigate", {"url": B, "wait_for_load": True}, 90)
# 等待"页面已稳定"再开测: 应用启动时会自己导航到欢迎页, 若与我们的导航竞争,
# 会多出一条历史项导致 back 落到欢迎页 —— 那是**探针时序**问题, 不是 back 的缺陷。
# 判据: 连续两次读到同一个 B 地址(用实时值, 不用可能滞后的缓存值)。
settled = 0
for _ in range(20):
    time.sleep(0.5)
    u = call("browser_evaluate", {"code": "location.href"}, 30)[1]
    if 'navB=2' in u:
        settled += 1
        if settled >= 2:
            break
    else:
        settled = 0
print("   稳定判据: 连续两次读到 B (settled=%d)" % settled)
print("   当前 URL: %s" % url_now())

print("\n== A) back(默认 wait_for_load) ==")
t0 = time.time()
e, t = call("browser_back", {}, 120)
el = time.time() - t0
time.sleep(0.4)
u = url_now()
print("   %.2fs isError=%s | %s" % (el, e, t[:220]))
print("   回退后 URL: %s" % u)
arm("back 未超时且返回成功", (not e) and ('超时' not in t) and ('失败' not in t),
    "%.2fs | %s" % (el, t[:160]))
arm("back 后确实回到了 A", 'navA=1' in u, u)

print("\n== B) forward(默认 wait_for_load) ==")
t0 = time.time()
e, t = call("browser_forward", {}, 120)
el = time.time() - t0
time.sleep(0.4)
u2 = url_now()
print("   %.2fs isError=%s | %s" % (el, e, t[:220]))
print("   前进后 URL: %s" % u2)
arm("forward 未超时且返回成功", (not e) and ('超时' not in t) and ('失败' not in t),
    "%.2fs | %s" % (el, t[:160]))
arm("forward 后确实回到了 B", 'navB=2' in u2, u2)

print("\n== C) 显式 wait_for_load:false(应立即返回, 不等载入) ==")
t0 = time.time()
e, t = call("browser_back", {"wait_for_load": False}, 60)
el = time.time() - t0
print("   %.2fs isError=%s | %s" % (el, e, t[:200]))
arm("显式 false 走快速路径(立刻返回)", (not e) and el < 2, "%.2fs | %s" % (el, t[:140]))

print("\n== D) 无历史时的诚实报错(不谎报成功) ==")
e, t = call("browser_forward", {}, 60)
print("   forward 到尽头 -> isError=%s %s" % (e, t[:200]))

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
