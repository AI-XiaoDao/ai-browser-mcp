# -*- coding: utf-8 -*-
"""browser_reverse_network_intercept 修复验收(行为级, 不靠工具自报)。

三臂:
  A 守卫臂   enable 不传 url_pattern -> 必须**明确失败**(修复前是 _async 假成功)
  B 非匹配臂 enable *example.org* 后导航 example.com -> 必须照常成功
             (证明命令真的被内核接受: 既没有被拒, 也没有误伤流量)
  C 匹配臂   enable *example.com* 后导航新 URL -> 必须**卡住**(location.href 停在旧地址)
             -> 证明拦截真的生效(区分"命令被接受"与"拦截真的在工作")
  D 复位臂   disable -> 挂起的请求恢复, 导航/回读恢复正常

关键判据是 location.href: 被拦的导航不会提交, 所以 href 停在旧值。
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
TOOL = "browser_reverse_network_intercept"


def c(n, a, to=70):
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


def href():
    e, t = c("browser_evaluate", {"code": "location.href"}, 25)
    m = re.search(r'"(https?://[^"]*)"', t)
    return m.group(1) if m else ("?:" + t[:120])


def nav(url, wait=True):
    e, t = c("browser_navigate", {"url": url, "wait_for_load": wait}, 90)
    flag = "OK" if not e else "ERR"
    low = t.lower()
    for k in ("timeout", "超时", "not load", "失败", "error"):
        if k in low:
            flag = "TIMEOUT/ERR"
            break
    return flag, t[:150]


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

print("== 准备: 基线页面 ==")
print("   navigate -> %s" % (nav("https://example.com/?base=1")[0],))
time.sleep(0.5)
base_href = href()
print("   基线 href = %s" % base_href)

print("\n== A 守卫臂: enable 不传 url_pattern (应明确失败) ==")
e, t = c(TOOL, {"action": "enable"})
print("   isError=%s -> %s" % (e, t[:300]))
print("   [%s] A 明确报错而不是假成功" % ("PASS" if (e or "url_pattern" in t) else "FAIL"))

print("\n== B 非匹配臂: enable *example.org* 后导航 example.com (应照常成功) ==")
e, t = c(TOOL, {"action": "enable", "url_pattern": "*example.org*"})
print("   enable isError=%s -> %s" % (e, t[:220]))
flag, body = nav("https://example.com/?nomatch=1")
time.sleep(0.5)
h_b = href()
print("   navigate -> %s | href = %s" % (flag, h_b))
print("   [%s] B 命令被内核接受且未误伤流量" % ("PASS" if h_b.endswith("?nomatch=1") else "FAIL"))

print("\n== C 匹配臂: enable *example.com* 后导航新 URL (应被拦, href 停在旧值) ==")
e, t = c(TOOL, {"action": "enable", "url_pattern": "*example.com*"})
print("   enable isError=%s -> %s" % (e, t[:220]))
flag, body = nav("https://example.com/?blocked=1")
time.sleep(0.8)
h_c = href()
print("   navigate -> %s | href = %s" % (flag, h_c))
print("   navigate 回包: %s" % body)
intercepted = not h_c.endswith("?blocked=1")
print("   [%s] C 拦截真的生效(href 未提交到 blocked=1)" % ("PASS" if intercepted else "FAIL"))

print("\n== D 复位臂: disable 后应恢复 ==")
e, t = c(TOOL, {"action": "disable"})
print("   disable isError=%s -> %s" % (e, t[:200]))
time.sleep(2.0)
flag, body = nav("https://example.com/?after=1")
time.sleep(0.5)
h_d = href()
print("   navigate -> %s | href = %s" % (flag, h_d))
print("   [%s] D 解除拦截后恢复正常" % ("PASS" if h_d.endswith("?after=1") else "FAIL"))

e, t = c("browser_evaluate", {"code": "'alive:'+document.title"}, 20)
print("\n   终态存活检查: %s" % t[:120])
