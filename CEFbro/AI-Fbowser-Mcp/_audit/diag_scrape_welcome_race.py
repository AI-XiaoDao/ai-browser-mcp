# -*- coding: utf-8 -*-
"""browser_scrape 首调返回**欢迎页**的 h1(而非目标 URL 的) —— 是竞态还是稳定行为?

0.03s 就返回了结果, 不可能是"导航+提取"的真实耗时 => 怀疑拿到的是**导航前的页面**内容
(浏览器启动时停在欢迎页)。若首次调用给的是**另一个页面的数据**, 那是比报错更危险的静默错数据。
本脚本: 重复多次, 记录耗时与内容, 并加"先导航到目标页再 scrape"的对照臂。
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

print("== A) 冷启动后**立即** scrape h1(目标 example.com) 连做 4 次 ==")
for i in range(4):
    t0 = time.time()
    e, t = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1"}, 90)
    print("   第%d次 %.2fs isError=%s -> %s" % (i + 1, time.time() - t0, e, t[:150].replace('\n', ' ')))

print("\n== B) 当前 URL 是什么? ==")
print("   %s" % call("browser_get_url", {})[1][:200])

print("\n== C) 先导航到目标页, 再 scrape h1(对照) ==")
call("browser_navigate", {"url": "https://example.com/", "wait_for_load": True})
time.sleep(0.5)
t0 = time.time()
e, t = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1"}, 90)
print("   %.2fs isError=%s -> %s" % (time.time() - t0, e, t[:200].replace('\n', ' ')))
