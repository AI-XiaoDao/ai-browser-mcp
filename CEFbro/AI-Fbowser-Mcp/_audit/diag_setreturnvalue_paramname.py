# -*- coding: utf-8 -*-
"""验证参数名假设: 本机 Debugger.setReturnValue 要的是 `newValue`(旧协议名), 不是 `result`。

上一测的原始 CDP 回包给出了决定性线索:
    {"code":-32602,"message":"Invalid parameters",
     "data":"Failed to deserialize params.newValue - BINDINGS: mandatory field missing at position 31"}
即内核绑定**要求 newValue 字段**。这与项目自己在注释里记过的同类差异一致
(`setInstrumentationBreakpoint` 本机要 `instrumentation` 而非新版 `eventName`)。
本项目 `MCP_Server_Reverse.wsv:1239` 发的是 `{"result":{"value":…}}` -> 于是恒定失败。

本脚本在同一暂停帧上依次试三种形状, 用**原始 CDP** 判定哪种被接受:
  ① {"newValue": {"value": true}}
  ② {"newValue": true}
  ③ {"result": {"value": true}}   (现实现, 预期失败——作为对照)
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
INJ = ("(function(){if(window.mcpBpTimer){try{clearInterval(window.mcpBpTimer)}catch(e){}}"
       "var s=document.createElement('script');s.textContent=%s;"
       "document.body.appendChild(s);return 'installed'})()" % json.dumps("\n".join(LINES)))


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


def pause():
    c("browser_debugger_enable", {})
    c("browser_execute_js", {"code": INJ})
    time.sleep(0.8)
    e, t = c("browser_debugger_flow", {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                                       "resume": False, "max_ms": 8000})
    return not e


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

variants = [
    ("① newValue: {value: true}", {"newValue": {"value": True}}),
    ("② newValue: true", {"newValue": True}),
    ("③ result: {value: true} (现实现)", {"result": {"value": True}}),
]
for label, params in variants:
    c("browser_navigate", {"url": "https://example.com/?rv=2", "wait_for_load": True})
    time.sleep(0.6)
    if not pause():
        print("%-34s 前置未停住, 跳过" % label)
        continue
    e, t = c("browser_cdp_call", {"method": "Debugger.setReturnValue",
                                  "params": json.dumps(params)})
    print("%-34s isError=%-5s -> %s" % (label, e, unesc(t)[:220].replace("\n", " ")))
    c("browser_debugger_resume", {})
    time.sleep(0.3)
