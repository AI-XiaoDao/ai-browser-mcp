# -*- coding: utf-8 -*-
"""三臂验收 Phase 0 的"双证据"判据(地址已变 OR 载入已结束)。

臂1 冷启动首调(地址会变)        -> 必须返回**目标页**数据
臂2 目标==当前页(地址不变, 原地) -> 必须**不误判也不死等**(应较快返回该页数据)
臂3 目标不可达(等不到任何证据)   -> 必须**如实超时**, 绝不返回上一个页面的数据
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

print("== 臂1: 冷启动后**第一次**调用 scrape(目标 example.com) ==")
t0 = time.time()
e, t = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1"}, 90)
el = time.time() - t0
print("   %.2fs isError=%s -> %s" % (el, e, t[:160].replace('\n', ' ')))
arm("冷启动首调拿到**目标页**数据(不是欢迎页)",
    (not e) and ('Example Domain' in t) and ('AI浏览器' not in t),
    "%.2fs | %s" % (el, t[:120]))

print("\n== 臂2: 目标==当前页(地址不变, 靠'载入已结束'证据) ==")
t0 = time.time()
e, t = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1",
                               "max_ms": 15000}, 90)
el = time.time() - t0
print("   %.2fs isError=%s -> %s" % (el, e, t[:160].replace('\n', ' ')))
arm("地址不变时**不误判也不死等**", (not e) and ('Example Domain' in t) and el < 12,
    "%.2fs | %s" % (el, t[:120]))

print("\n== 臂3: 目标不可达(两个证据都等不到) ==")
t0 = time.time()
e, t = call("browser_scrape", {"url": "https://10.255.255.1/", "extract_selector": "h1",
                               "max_ms": 6000}, 120)
el = time.time() - t0
print("   %.1fs isError=%s -> %s" % (el, e, t[:200]))
arm("等到超时即如实报错, 不返回上一个页面的数据",
    e and ('Example Domain' not in t),
    "%.1fs | %s" % (el, t[:150]))

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
