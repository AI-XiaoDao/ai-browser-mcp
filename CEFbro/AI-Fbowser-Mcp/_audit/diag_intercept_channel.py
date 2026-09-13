# -*- coding: utf-8 -*-
"""手写过滤器通道(modify/block)到底有没有生效? —— 用**正文**作观测量。

为什么之前的观测量不对: block 返回的屏蔽页 HTML 是
  <html><head><meta charset="UTF-8"></head><body>资源已屏蔽 (MCP intercept block)</body></html>
**没有 <title>**, 所以"标题是否变化"根本判不出拦截是否发生。
本轮改看 document.body.innerText, 并同时测 modify(把 "Example Domain" 改成 "MODIFIED"),
两者都是"改写响应体"的同一通道, 能互相印证。
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
URL = "https://example.com/?filterprobe=1"


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


def nav_body():
    call("browser_navigate", {"url": URL, "wait_for_load": True}, 90)
    time.sleep(0.5)
    e, t = call("browser_evaluate",
                {"code": "(document.body?document.body.innerText:'').slice(0,120)"}, 40)
    return t.strip()[:160]


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

print("== 0) 清空规则 + 基线正文 ==")
print("   clear -> %s" % call("browser_intercept", {"action": "clear"})[1][:100])
base = nav_body()
print("   基线正文: %r" % base)

print("\n== 1) modify: 把 Example Domain 改成 MODIFIED ==")
e, t = call("browser_intercept", {"action": "modify", "url": "example.com",
                                  "search_text": "Example Domain",
                                  "replace_text": "MODIFIED"})
print("   modify -> isError=%s %s" % (e, t[:150]))
b1 = nav_body()
print("   正文: %r" % b1)
print("   [%s] modify 生效(正文含 MODIFIED)" % ('PASS' if 'MODIFIED' in b1 else 'FAIL'))

print("\n== 2) block: 屏蔽同一 URL ==")
call("browser_intercept", {"action": "clear"})
e, t = call("browser_intercept", {"action": "block", "url": "example.com"})
print("   block -> isError=%s %s" % (e, t[:150]))
b2 = nav_body()
print("   正文: %r" % b2)
print("   [%s] block 生效(正文含 资源已屏蔽)" % ('PASS' if '资源已屏蔽' in b2 else 'FAIL'))

print("\n== 3) 诊断: 规则是否真的进了存储? 用 unmodify 探测 ==")
e, t = call("browser_intercept", {"action": "unmodify", "url": URL})
print("   unmodify -> %s" % t[:200])
print("   (若报 1 条, 说明规则**确实存在**, 问题在'过滤器未被调用/未安装'这一侧)")

call("browser_intercept", {"action": "clear"})
print("\n== 4) 收尾后正文(应回到基线) ==")
b3 = nav_body()
print("   %r" % b3)
