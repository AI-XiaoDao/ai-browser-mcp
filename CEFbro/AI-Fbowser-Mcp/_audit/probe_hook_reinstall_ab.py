# -*- coding: utf-8 -*-
"""browser_reverse_cdp_hook 的 "already exists" 是不是**重复安装**造成的(而非真缺陷)?

A 臂: 全新进程, 第一次装 -> 应成功
B 臂: 同一进程再装同一个函数 -> 看内核原话
若 B 是 "Breakpoint at specified location already exists", 则说明目标状态**已达成**,
按项目既有惯例(browser_debugger_resume 的幂等成功)应视为幂等成功, 而不是失败 ——
否则 AI 会为"已经达成"的状态反复重试/换方法, 正是本目标要消灭的形态。
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
c("browser_navigate", {"url": "https://example.com/?hookab=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

print("== A 臂: 全新进程第一次安装 ==")
e, t = c("browser_reverse_cdp_hook", {"function_name": "parseInt"})
print("   isError=%s | %s" % (e, t[:300]))

print("\n== B 臂: 同进程重复安装同一函数 ==")
e2, t2 = c("browser_reverse_cdp_hook", {"function_name": "parseInt"})
print("   isError=%s | %s" % (e2, t2[:300]))

print("\n== 结论 ==")
print("   A 成功 = %s" % (not e))
print("   B 报 'already exists' = %s" % ('already exists' in t2.lower()))
