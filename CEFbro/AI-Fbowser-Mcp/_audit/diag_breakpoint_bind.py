# -*- coding: utf-8 -*-
"""把"断点设了却不命中"这件事查清: 用项目自带的工具看**脚本真实 URL**与**该行是否可断**。

实测背景: about:blank 上 `document.write` 注入内联脚本(已验证执行成功, window.__mcpW=42),
并且 `browser_debugger_set_breakpoint {url:'.*', line:0}` 返回了 breakpointId,
但 `browser_debugger_wait_paused` 8 秒没等到暂停。三种可能:
  A. 断点没绑上(脚本 URL 不匹配正则, 或 line 0 无有效位置);
  B. 绑上了但注入脚本的解析/执行不被该断点覆盖;
  C. 暂停发生了但事件没进缓存。
判据: 先看脚本列表(URL 是什么) → 看可断点(该行有没有有效位置) → 看断点列表是否 bound。
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


def call(name, args, timeout=30):
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


def show(tag, e, t, dt):
    print("  %-40s %-4s %5.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:120]))


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
        break
    except Exception:
        pass

print("== 1) 造一个必然有脚本的页面(about:blank + document.write) ==")
call("browser_navigate", {"url": "about:blank", "wait_for_load": True}, 30)
time.sleep(0.4)
call("browser_debugger_enable", {})
WRITE = ("document.write('<html><body><script>function mcpT(a){var b=a+1;return b}"
         "window.__mcpW=mcpT(41);<\\/script></body></html>');document.close();'wrote'")
show("document.write 注入", *call("browser_execute_js", {"code": WRITE}, 30))

print("\n== 2) 脚本注册表: 注入的脚本 URL 到底是什么 ==")
show("search_script list", *call("browser_reverse_search_script", {"action": "list"}, 30))

print("\n== 3) 可断点位置: 第 0 行到底能不能下断 ==")
show("get_possible_breakpoints(line=0)", *call(
    "browser_reverse_get_possible_breakpoints", {"line": 0, "end_line": 3}, 30))

print("\n== 4) 断点列表: 之前设的断点是否 bound ==")
e, t, dt = call("browser_debugger_set_breakpoint", {"url": ".*", "line": 0}, 30)
show("set_breakpoint(url='.*', line=0)", e, t, dt)
show("debugger_get_breakpoints/list(若有)", *call("browser_debugger_breakpoints", {}, 20))
show("browser_debugger_list_breakpoints(若有)", *call("browser_debugger_list_breakpoints", {}, 20))

print("\n== 5) 再触发一次脚本执行(此时断点已在), 看是否暂停 ==")
show("再注入一次脚本", *call("browser_execute_js", {"code": WRITE}, 30))
show("wait_paused(max_ms=5000)", *call("browser_debugger_wait_paused", {"max_ms": 5000}, 25))
show("last_paused", *call("browser_debugger_last_paused", {}))
call("browser_debugger_resume", {})

print("\n== 收尾 ==")
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("  已关闭")
