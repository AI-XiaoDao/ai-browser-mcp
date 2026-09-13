# -*- coding: utf-8 -*-
"""排查: browser_scrape 纳入同步等待后, 回包变成了什么? (fastcheck 的 '提取得真值' 断言不再通过)

要区分三种可能:
  ① 同步等待超时 -> 变成 ⏱ 超时失败 (真回归)
  ② 等到了结果, 但**响应结构**与异步路径不同(键名/嵌套变了) -> 断言写法要跟着改(功能其实更好)
  ③ 结果里确实没有数据 -> 真缺陷
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


def c(n, a, to=90):
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
c("browser_navigate", {"url": "https://example.com/?sc=1", "wait_for_load": True})

print("== browser_scrape (默认参数, 与 fastcheck 的取法一致) ==")
e, t = c("browser_scrape", {"max_items": 30})
print("   isError=%s | 长度 %d" % (e, len(t)))
print("   %s" % t[:900])
print()
print("   含 超时: %s" % ('超时' in t))
print("   含 _async: %s" % ('_async' in t))
print("   含 Example: %s" % ('Example' in t))
print("   含 null: %s" % ('null' in t))

print("\n== 对照: browser_dom_get_html(同批纳入) ==")
e2, t2 = c("browser_dom_get_html", {"selector": "h1"})
print("   isError=%s | %s" % (e2, t2[:400]))
