# -*- coding: utf-8 -*-
"""干净环境下的端到端复现: 注入探针 -> 确认在跑 -> auto 用 urlRegex 下断。

前两次复测都无效, 原因都是**我又污染了前置条件**:
  · 第一次: 我在上一个诊断脚本的结尾调了 `Debugger.setBreakpointsActive {false}` 清场 ->
            断点全局失效, 于是"任意行号都 0 命中";
  · 第二次: 我在**已被台账导航过**的页面上直接下断 -> 当前文档里根本没有探针脚本。
本脚本从重启开始, 严格按 导航 -> 启用调试器 -> 注入 -> 确认 tick 在涨 -> 下断 的顺序走。
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

LINES = [
    "window.mcpBpTick=0;",
    "window.mcpBpFn=function mcpBpFn(){",
    "  var v=1;",
    "  return v;",
    "};",
    "window.mcpBpTimer=setInterval(window.mcpBpFn,300);",
    "//# sourceURL=https://example.com/mcp-breakpoint-probe.js",
]
SRC = "\n".join(LINES)
INJ = ("(function(){if(window.mcpBpTimer)return 'exists';"
       "var s=document.createElement('script');s.textContent=%s;"
       "document.body.appendChild(s);return 'made'})()" % json.dumps(SRC))


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or "" for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def unesc(t):
    return t.replace('\\"', '"')


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

c("browser_navigate", {"url": "https://example.com/?e2e=1", "wait_for_load": True})
time.sleep(0.6)
print("1) enable:", c("browser_debugger_enable", {})[1][:80])
print("2) inject:", c("browser_execute_js", {"code": INJ})[1][:80])
time.sleep(1.0)
e, t = c("browser_execute_js",
         {"code": "JSON.stringify({tick:window.mcpBpTick,timer:typeof window.mcpBpTimer})"})
print("3) 探针状态:", t[:140])
e, t = c("browser_reverse_search_script", {"action": "list"})
print("4) 注册表里有 probe URL:", "mcp-breakpoint-probe" in t)

for ln in (3, 2, 1):
    e, t = c("browser_debugger_auto", {"breakpoint": "mcp-breakpoint-probe",
                                       "line": ln, "max_ms": 5000, "max_hits": 1})
    print("5) line=%s isError=%s -> %s" % (ln, e, unesc(t)[:200].replace("\n", " ")))
    c("browser_debugger_resume", {})

print("\n(收尾只 resume, 不再调 setBreakpointsActive —— 上一次就是它把断点弄失效的)")
