# -*- coding: utf-8 -*-
"""验收 converter 修复: browser_scrape 现在必须**一次调用**就把提取结果带回来。

区分性判据:
  · 修复前(同步) -> 回空串 ""            (转换器读不到工具专属键 text)
  · 修复前(异步) -> {"_async":true,...}  需要再调 mcp_result
  · 现在        -> 同一次响应里就有 "Example Domain", 且没有 _async
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


def call(n, a, to=90):
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

print("== browser_scrape 一次调用(不轮询) ==")
t0 = time.time()
e, t = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1"}, 90)
el = time.time() - t0
print("   isError=%s | 用时 %.2fs | %s" % (e, el, t[:500]))
print()
ok = (not e) and ('Example Domain' in t) and ('_async' not in t) and (t.strip() != '""')
print("   [%s] 一次调用即得提取结果(含 Example Domain、无 _async、非空)" % ('PASS' if ok else 'FAIL'))
print("   含 Example Domain: %s" % ('Example Domain' in t))
print("   含 _async        : %s" % ('_async' in t))
print("   为空串           : %s" % (t.strip() == '""'))

print("\n== 对照: extract_selector 换成 body(全文提取)也应有内容 ==")
e2, t2 = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "body"}, 90)
print("   isError=%s | %s" % (e2, t2[:220]))
print("   [%s] 全文提取非空" % ('PASS' if (not e2 and t2.strip() not in ('""', '')) else 'FAIL'))
