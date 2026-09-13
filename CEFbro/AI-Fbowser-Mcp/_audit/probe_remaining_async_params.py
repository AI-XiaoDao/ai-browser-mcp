# -*- coding: utf-8 -*-
"""把**仍然走异步入口**的 8 个调用点的参数形状逐个交给内核判定。

异步入口不等响应 => 参数错了也报 success。没法改同步的(或按语义该保留异步的)那些点,
至少要证明"内核确实接受这套参数", 否则就是又一个静默失效。
本脚本逐个发原始 CDP, 读内核原话, 并在最后逐条回收副作用。
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


def c(n, a, to=50):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])
                   if i.get("type") == "text").replace('\\"', '"')


def cdp(m, p=None):
    t = c("browser_cdp_call", {"method": m, "params": p or {}})
    low = t.lower()
    if t.strip().startswith('{}'):
        verdict = "接受"
    elif "invalid parameters" in low or "wasn't found" in low:
        verdict = "拒绝"
    else:
        verdict = "返回数据"
    return verdict, t[:220]


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
c("browser_navigate", {"url": "https://example.com/?asyncparams=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

ROWS = []


def probe(label, method, params):
    v, raw = cdp(method, params)
    ROWS.append((label, method, v, raw))
    print("   [%-4s] %-46s %s" % (v, method, raw[:150]))


print("== 仍走异步入口的 8 个调用点: 参数形状逐个实测 ==")
probe("websocket enable", "Network.enable", {"maxPostDataSize": 65536})
probe("dom_breakpoint xhr", "DOMDebugger.setXHRBreakpoint", {"url": "*api*"})
probe("dom_breakpoint(事件)", "DOMDebugger.setEventListenerBreakpoint", {"eventName": "click"})
probe("dom_breakpoint timer", "DOMDebugger.setInstrumentationBreakpoint", {"eventName": "setTimeout"})
probe("preload", "Page.addScriptToEvaluateOnNewDocument",
      {"source": "void 0", "runImmediately": True})
probe("heap snapshot", "HeapProfiler.takeHeapSnapshot", {"reportProgress": False})
probe("heap start_sampling", "HeapProfiler.startSampling", {"samplingInterval": 32768})

# setBreakpointOnFunctionCall 需要真实 objectId: 先取一个函数句柄
t = c("browser_cdp_call", {"method": "Runtime.evaluate",
                           "params": {"expression": "parseInt", "returnByValue": False}})
m = re.search(r'"objectId":"([^"]+)"', t.replace('\\"', '"'))
if m:
    probe("cdp_hook(函数断点)", "Debugger.setBreakpointOnFunctionCall", {"objectId": m.group(1)})
else:
    print("   [跳过] setBreakpointOnFunctionCall: 没取到 objectId")
    ROWS.append(("cdp_hook(函数断点)", "Debugger.setBreakpointOnFunctionCall", "跳过", "未取到 objectId"))

print("\n== 副作用回收 ==")
for m, p in [("DOMDebugger.removeXHRBreakpoint", {"url": "*api*"}),
             ("DOMDebugger.removeEventListenerBreakpoint", {"eventName": "click"}),
             ("DOMDebugger.removeInstrumentationBreakpoint", {"eventName": "setTimeout"}),
             ("HeapProfiler.stopSampling", {})]:
    v, raw = cdp(m, p)
    print("   [%-4s] %s" % (v, m))

print("\n== 汇总 ==")
bad = [r for r in ROWS if r[2] == "拒绝"]
print("   实测 %d 项, 被内核拒绝 %d 项" % (len(ROWS), len(bad)))
for label, method, v, raw in ROWS:
    print("   %-4s %-44s %s" % (v, method, label))
if bad:
    print("\n   !! 被拒绝的项 => 走异步入口时会被静默吞掉:")
    for label, method, v, raw in bad:
        print("      %s (%s): %s" % (method, label, raw))
