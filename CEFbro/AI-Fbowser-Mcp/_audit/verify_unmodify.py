# -*- coding: utf-8 -*-
"""验收 browser_intercept 新增的 unmodify / unreplace（行为级回读，不听自报）。

无"列出规则"的 action，故用**行为**做回读:
  A 基线        导航 -> 正常页面
  B 加 block    导航 -> 应被拦截(页面内容变化)
  C unmodify    导航 -> 应恢复正常, 且回包须报"撤销 1 条"
  D 再 unmodify 撤销不存在 -> 幂等成功, 报 0 条(不报失败, 避免 AI 反复重试)
  E unreplace   无 replace_file 规则 -> 幂等成功, 报 0 条
  F 口径核对    规则URL 用短串("urltest"), 用**完整请求URL**去撤 -> 应能撤掉(与命中同口径: 包含即算)
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
URL = "https://example.com/?urltest=1"
R = []


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


def title():
    e, t = call("browser_get_title", {}, 40)
    m = t.strip()
    return m[:80]


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:260])


def nav():
    call("browser_navigate", {"url": URL, "wait_for_load": True}, 90)
    time.sleep(0.4)
    return title()


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

print("== A) 基线: 先清空规则, 导航应正常 ==")
print("   clear -> %s" % call("browser_intercept", {"action": "clear"})[1][:120])
base_title = nav()
print("   基线标题: %r" % base_title)

print("\n== B) 加 block 规则后导航(应被拦截) ==")
e, t = call("browser_intercept", {"action": "block", "url": URL})
print("   block -> isError=%s %s" % (e, t[:160]))
blocked_title = nav()
print("   拦截后标题: %r" % blocked_title)
arm("block 规则确实生效(页面内容与基线不同)",
    blocked_title != base_title, "基线=%r 拦截后=%r" % (base_title, blocked_title))

print("\n== C) unmodify 撤销 -> 应恢复且报撤销条数 ==")
e, t = call("browser_intercept", {"action": "unmodify", "url": URL})
print("   unmodify -> isError=%s %s" % (e, t[:260]))
after_title = nav()
print("   撤销后标题: %r" % after_title)
arm("unmodify 回包报出撤销条数(非 0)",
    ("撤销" in t) and (" 0 条" not in t), t[:160])
arm("unmodify 后页面恢复(规则真的被删掉)",
    after_title == base_title, "基线=%r 撤销后=%r" % (base_title, after_title))

print("\n== D) 再 unmodify 同一 URL(规则已不存在) ==")
e, t = call("browser_intercept", {"action": "unmodify", "url": URL})
print("   -> isError=%s %s" % (e, t[:220]))
arm("撤销不存在 = 幂等成功且如实报 0 条(不报失败)",
    (not e) and (" 0 条" in t), "isError=%s | %s" % (e, t[:160]))

print("\n== E) unreplace(无 replace_file 规则) ==")
e, t = call("browser_intercept", {"action": "unreplace", "url": URL})
print("   -> isError=%s %s" % (e, t[:220]))
arm("unreplace 幂等成功且报 0 条", (not e) and (" 0 条" in t),
    "isError=%s | %s" % (e, t[:160]))

print("\n== F) 口径核对: 规则URL 用短串, 用完整请求URL撤销 ==")
call("browser_intercept", {"action": "block", "url": "urltest"})
t2 = nav()
print("   加短串规则后标题: %r (应被拦截)" % t2)
e, t = call("browser_intercept", {"action": "unmodify", "url": URL})
print("   unmodify(完整URL) -> isError=%s %s" % (e, t[:220]))
t3 = nav()
print("   撤销后标题: %r" % t3)
arm("短串规则也能被完整URL撤销(与命中同口径)",
    (not e) and (" 0 条" not in t) and (t3 == base_title),
    "拦截=%r 撤销回包=%s 撤销后=%r" % (t2, t[:110], t3))

call("browser_intercept", {"action": "clear"})
ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
