# -*- coding: utf-8 -*-
"""实验: 给注入的脚本加 `//# sourceURL=...`, 它能不能被 **urlRegex 断点**匹配到?

背景(报告 §95/§96 实测): 本页所有已注册脚本的 url 都是空串, 于是 setBreakpointByUrl 无论给什么
urlRegex 都得到 `"locations":[]` -> browser_debugger_auto / flow 的"按 URL 下断"路径在本机无法命中,
它们只能记成"目标未命中"; browser_reverse_return_value / set_variable 也因为拿不到断点帧而无法验证。

若能通过 `//# sourceURL` 让脚本带上真实 URL, 这 4 个工具就能被**真正测到** —— 这是本实验要回答的唯一问题。

判据:
 ① 注入带 sourceURL 的脚本后, browser_reverse_search_script action=list 里**出现该 URL**
    (对比: 之前的注入脚本 url 都是空串)
 ② 若能出现, 用 browser_debugger_auto {breakpoint:<该 URL 的正则>, line:<目标行>} 应能**真的命中**
    (对比实验: 用同一个 line 但一个不存在的 urlRegex -> 必 0 命中, 证明命中来自 URL 匹配)
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
PROBE_URL = "https://example.com/mcp-breakpoint-probe.js"

# 脚本内容: 一个每 300ms 调一次的函数, 目标行就是函数体里那行(便于下断)
LINES = [
    "window.mcpBpTick=0;",
    "window.mcpBpFn=function mcpBpFn(){",
    "  window.mcpBpTick=window.mcpBpTick+1;",
    "};",
    "window.mcpBpTimer=setInterval(window.mcpBpFn,300);",
    "//# sourceURL=" + PROBE_URL,
]
SRC = "\n".join(LINES)
TARGET_LINE = 2  # 0起算: "  window.mcpBpTick=...;" 那一行


def call(name, args, timeout=60):
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
call("browser_navigate", {"url": "https://example.com/?bp=1", "wait_for_load": True}, 45)
time.sleep(0.6)

# ★ 必须**先启用调试器域**, 否则注入的脚本不会被 Debugger.scriptParsed 上报 ->
#   注册表 count:0(第一版就是漏了这一步, 工具自己的 hint 已经写明"先 browser_debugger_enable")。
e, t, _ = call("browser_debugger_enable", {}, 45)
print("== 先启用调试器域 ==")
print("   isError=%s %s" % (e, t[:160]))

print("== 注入带 //# sourceURL 的脚本 ==")
inj = ("(function(){var s=document.createElement('script');s.textContent=%s;"
       "document.body.appendChild(s);return 'ok'})()" % json.dumps(SRC))
e, t, _ = call("browser_execute_js", {"code": inj}, 30)
print("   isError=%s %s" % (e, t[:120]))

print("\n== ① 已注册脚本里有没有带上那个 URL ==")
e, t, _ = call("browser_reverse_search_script", {"action": "list"}, 45)
u = unesc(t)
print("   isError=%s" % e)
print("   %s" % u[:700])
has_url = "mcp-breakpoint-probe.js" in u
print("   含 probe URL: %s" % has_url)

print("\n== ② 若带上 URL, 用 urlRegex 下断能否真的命中 ==")
if has_url:
    e, t, dt = call("browser_debugger_auto",
                    {"breakpoint": "mcp-breakpoint-probe", "line": TARGET_LINE,
                     "max_ms": 8000, "max_hits": 2}, 60)
    print("   命中实验: isError=%s %.2fs" % (e, dt))
    print("   %s" % unesc(t)[:400])
    print("\n   对照: 同一个 line 但换成不存在的 urlRegex")
    e2, t2, dt2 = call("browser_debugger_auto",
                       {"breakpoint": "mcp-no-such-script-zzz", "line": TARGET_LINE,
                        "max_ms": 3000}, 60)
    print("   对照: isError=%s %.2fs" % (e2, dt2))
    print("   %s" % unesc(t2)[:300])
else:
    print("   (URL 未出现 -> 该路径在本机不可用; 需要另找让脚本带 URL 的办法)")

# 清场
call("browser_execute_js",
     {"code": "(function(){if(window.mcpBpTimer)clearInterval(window.mcpBpTimer);"
              "window.mcpBpFn=function(){};return 'clean'})()"}, 30)
call("browser_cdp_call", {"method": "Debugger.setBreakpointsActive",
                          "params": "{\"active\":false}"}, 30)
print("\n(已清场)")
