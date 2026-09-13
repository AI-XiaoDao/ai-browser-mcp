# -*- coding: utf-8 -*-
"""定案: 本机 CDP requestId 到底是不是"数字串"?

background: browser_network_body 有一道前置格式守卫(取首字符, 必须在 "0123456789" 里),
不满足就直接拒绝, 理由是"CDP requestId 为数字串(形如 1000012345.5)"。
但实测 cdp_event 给出的真实 requestId 是 32 位十六进制串 —— 两者矛盾。
判断依据只能来自内核: 把真实 id 直接发给 Network.getResponseBody, 看是否返回响应体。
"""
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


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


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

print("== A) set_window_style 的真实参数名 ==")
os.system('py -3 "%s" browser_set_window_style' % os.path.join(ROOT, '_audit', 'show_schema.py'))

print("\n== B) 取一个真实 requestId ==")
c("browser_navigate", {"url": "https://example.com/?fmt=1", "wait_for_load": True})
c("browser_kernel_cdp_monitor", {"action": "add", "methods": "Network.*"})
c("browser_navigate", {"url": "https://example.com/?fmt=%d" % int(time.time()),
                       "wait_for_load": True})
time.sleep(0.6)
e, t = c("browser_cdp_event", {"event_name": "Network.requestWillBeSent"})
m = re.search(r'"requestId":"([^"]+)"', t)
rid = m.group(1) if m else ""
kind = "全数字" if rid.isdigit() else ("含点数字" if re.fullmatch(r'[0-9.]+', rid or 'x')
                                      else ("十六进制" if re.fullmatch(r'[0-9A-Fa-f]+', rid or 'x')
                                            else "其它"))
print("   真实 requestId = %r  形态判定 = %s  长度 = %d" % (rid, kind, len(rid)))

print("\n== C) 把这个真实 id 直接发给内核 Network.getResponseBody ==")
if rid:
    t2 = c("browser_cdp_call", {"method": "Network.getResponseBody",
                                "params": {"requestId": rid}})[1]
    print("   内核返回: %s" % t2[:400])
    ok = "body" in t2
    print("   [%s] 真实(十六进制)id 内核**认**它 => 工具的'必须数字开头'守卫是错的"
          % ("PASS" if ok else "FAIL"))

print("\n== D) 对照: 走工具 browser_network_body ==")
if rid:
    e3, t3 = c("browser_network_body", {"request_id": rid})
    print("   isError=%s | %s" % (e3, t3[:300]))
    print("   [%s] 工具接受同一个 id" % ("PASS" if not e3 else "FAIL(被守卫拦下 = 真缺陷)"))
