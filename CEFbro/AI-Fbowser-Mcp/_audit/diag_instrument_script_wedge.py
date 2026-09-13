# -*- coding: utf-8 -*-
"""测量: browser_reverse_instrument_script(默认 action=install)会把实例**永久卡死**, 还是只是留下一个可恢复的暂停?

台账把它记成 fail(wedge) 并冷重启了。但"台账认为死了"不等于"真死了" ——
台账的活性探针有自己的超时, 而本工具的设计意图就是"命中后暂停, 让调用方去分析"。
所以必须区分:
  (甲) 硬卡死: 连 browser_debugger_resume 都救不回来 -> 真缺陷, 必须修
  (乙) 软暂停: resume 一下就恢复 -> 属**文档化的设计行为**, 但默认动作就能让"后续所有工具超时",
       对 AI 调用方仍不友好, 至少要把后果说清楚 / 或给出更安全的默认

测法: 装 -> 看是否 paused -> 尝试 resume(计时) -> 再测 browser_status 与 execute_js 是否恢复。
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


def call(name, args, timeout=30):
    t0 = time.time()
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def show(tag, name, args, timeout=30):
    e, t, dt = call(name, args, timeout)
    print("   [%-26s] isError=%-5s %5.2fs  %s" % (tag, e, dt, t[:150].replace("\n", " ")))
    return e, t, dt


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

call("browser_navigate", {"url": "https://example.com/?wedge=1", "wait_for_load": True}, 45)
time.sleep(0.6)
print("== 0 基线(确认实例健康) ==")
show("baseline status", "browser_status", {})
show("baseline execute_js", "browser_execute_js", {"code": "1+1"})

print("\n== 1 装插装(默认 action=install) ==")
show("install", "browser_reverse_instrument_script", {"action": "install"}, 45)

print("\n== 2 装完之后: 立刻看实例是否还活(与基线对比) ==")
show("status after", "browser_status", {})
show("execute_js after", "browser_execute_js", {"code": "1+1"})

print("\n== 3 是否处于暂停态?(看事件日志) ==")
show("last_paused", "browser_debugger_last_paused", {})

print("\n== 4 尝试恢复(这是关键: 硬卡死 vs 软暂停) ==")
e, t, dt = show("resume", "browser_debugger_resume", {}, 45)

print("\n== 5 resume 之后是否恢复 ==")
show("status after resume", "browser_status", {})
show("execute_js after resume", "browser_execute_js", {"code": "1+1"})

print("\n== 6 若仍未恢复, 试 suppress(工具自己提供的'止血') ==")
show("suppress", "browser_reverse_instrument_script", {"action": "suppress"}, 45)
show("status after suppress", "browser_status", {})
show("execute_js after suppress", "browser_execute_js", {"code": "1+1"})
