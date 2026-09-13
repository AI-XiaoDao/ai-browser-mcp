# -*- coding: utf-8 -*-
"""用 fastcheck 的**原样参数**调 browser_scrape, 打印完整回包, 定位断言为何不通过。"""
import io
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

URL = "https://example.com/"
e, t = call("browser_scrape", {"url": URL, "extract_selector": "h1", "max_ms": 12000}, 90)
print("== 第一次调用(isError=%s, 长度 %d) ==" % (e, len(t)))
print(t[:1200])
print()
print("含 'Example Domain' : %s" % ('Example Domain' in t))
print("含 '提取失败'       : %s" % ('提取失败' in t))
print("含 '超时'           : %s" % ('超时' in t))
print("含 task_            : %s" % ('task_' in t))
print("含 _async           : %s" % ('_async' in t))
