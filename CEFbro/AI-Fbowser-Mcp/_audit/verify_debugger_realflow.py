# -*- coding: utf-8 -*-
"""测"用户真正会用的调试流程"是否可用(而不是我上一轮的人工前置用法)。

## 为什么换测法
上一轮我用"先自动暂停, 再 wait_paused"去测 wait_paused —— 那是**人工构造**的用法, 而且实测失败。
但 wait_paused 的**本来语义**是"等一个断点命中", 正常链路是:
     debugger_enable → set_breakpoint(URL+行) → navigate(触发脚本) → wait_paused
所以真正该问的是: **这条链路走得通吗?** 本脚本就测它, 以及一键版 debugger_flow。

## 为什么需要"有 JS 的页面"
example.com 的文档里**没有任何 <script>**, 断点必然打不中(上一轮 3 个工具超时的真实原因之一)。
故这里用 data: URL 内联脚本 —— 它必有脚本、URL 稳定、且不依赖外网。
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
res = []

# 内联脚本页: 有一个函数与一句可断点的语句
PAGE = ("data:text/html,<html><body><h1>mcp</h1><script>"
        "function mcpTarget(a){var b=a+1;return b}"
        "window.__mcpT=mcpTarget(1);</script></body></html>")


def call(name, args, timeout=40):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-54s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:92]))


def restart():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            time.sleep(3.5)
            return True
        except Exception:
            pass
    return False


print("== 用例 A: 手动链路 set_breakpoint → navigate → wait_paused ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": PAGE, "wait_for_load": True}, 40)
time.sleep(0.6)
e, t, _ = call("browser_debugger_enable", {})
rec("debugger_enable", not e, t.replace("\n", " ")[:80])
e, t, _ = call("browser_debugger_set_breakpoint", {"url": ".*", "line": 0})
rec("set_breakpoint(url='.*', line=0)", not e, t.replace("\n", " ")[:80])
e, t, dt = call("browser_debugger_wait_paused", {"max_ms": 8000, "fresh": True}, 30)
rec("wait_paused 拿到断点命中", not e, "%.1fs | %s" % (dt, t.replace("\n", " ")[:80]))
if not e:
    e2, t2, _ = call("browser_debugger_stack", {})
    rec("命中后 stack 可用", not e2, t2.replace("\n", " ")[:70])
    call("browser_debugger_resume", {})
# 触发一次导航以命中断点(等待可能已超时, 故补一次导航再等)
e, t, dt = call("browser_navigate", {"url": PAGE, "wait_for_load": True}, 40)
rec("再次导航后 wait_paused 拿到命中", not e,
    "%.1fs | %s" % (dt, t.replace("\n", " ")[:80]))
call("browser_debugger_resume", {})

print("\n== 用例 B: 一键版 debugger_flow ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": PAGE, "wait_for_load": True}, 40)
time.sleep(0.5)
e, t, dt = call("browser_debugger_flow",
                {"url": PAGE, "breakpoint": ".*", "line": 0,
                 "expressions": "[\"document.title\"]", "resume": True}, 60)
rec("debugger_flow 一键流程成功", not e, "%.1fs | %s" % (dt, t.replace("\n", " ")[:88]))

print("\n== 用例 C: 流程结束后 CDP 通道必须健康 ==")
e, t, dt = call("browser_execute_js", {"code": "document.title"}, 30)
rec("execute_js 仍很快(未被冻结)", (not e) and dt < 3.0, "%.2fs | %s" % (dt, t.replace("\n", " ")[:60]))
e, t, dt = call("browser_get_text", {"selector": "h1"}, 30)
rec("get_text 正常", (not e) and dt < 5.0, "%.2fs" % dt)

print("\n== 收尾: 冷重启 ==")
restart()
e, t, dt = call("browser_execute_js", {"code": "1+1"})
rec("收尾重启后可用", not e, "%.2fs" % dt)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
