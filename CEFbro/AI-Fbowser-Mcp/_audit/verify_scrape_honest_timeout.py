# -*- coding: utf-8 -*-
"""验证竞态修复的**安全性**: 目标页永远加载不出来时, 必须**如实超时/失败**,
而不能退回"返回上一个页面的数据"(那正是修掉的静默错数据)。

对照: 修复前 phase0 只看"未加载" -> 会立刻提取旧页面 -> 返回旧页面的 h1。
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

print("== 先让页面处于一个**已知**状态(=欢迎页 h1 可识别) ==")
call("browser_navigate", {"url": "http://127.0.0.1:62882/", "wait_for_load": True})
time.sleep(0.6)
e, t = call("browser_evaluate", {"code": "document.querySelector('h1')?document.querySelector('h1').innerText:'(无h1)'"})
print("   当前页 h1: %s" % t[:120])

print("\n== 目标页不可达(黑洞地址), max_ms=6000: 应如实超时/失败 ==")
t0 = time.time()
e, t = call("browser_scrape", {"url": "https://10.255.255.1/", "extract_selector": "h1",
                               "max_ms": 6000}, 120)
el = time.time() - t0
print("   用时 %.1fs isError=%s -> %s" % (el, e, t[:300]))

bad = ('AI浏览器' in t) or ('MCP Server' in t)
print("\n   [%s] 没有把「上一个页面」的数据当成结果返回" % ('PASS' if not bad else 'FAIL'))
print("   [%s] 给出了可辨识的失败/超时" % ('PASS' if (e or '超时' in t or '失败' in t or 'error' in t.lower()) else 'FAIL'))
