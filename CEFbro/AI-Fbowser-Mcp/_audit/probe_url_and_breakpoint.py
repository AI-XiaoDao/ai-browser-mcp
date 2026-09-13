# -*- coding: utf-8 -*-
"""两件事一起量:
① `browser_navigate` 到底支不支持 data: URL? (工具描述明写"仅支持 http/https/about/data/ftp",
   但实测 data: 被拒且报 error=unsafe_url —— 描述与行为可能不一致, 必须逐种 URL 实测);
② 用**不依赖外网**的方式测断点全链路: about:blank + document.write 注入内联脚本,
   再让断点命中 —— 这样才有"会执行 JS 的页面"可用于测 debugger_flow / wait_paused。

为什么值得花这个时间: 上一轮 3 个调试工具"超时"的真实原因就是**测试用页面没有可命中的脚本**
(example.com 文档里 0 个 <script>)。若不能构造出可命中场景, 这三个工具就永远只能记"超时",
等于没测。本脚本的目标就是把它们变成**可测**。
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


if not restart():
    print("启动失败"); sys.exit(2)

print("== ① 各类 URL 的导航行为(逐种实测, 不靠描述) ==")
URLS = [
    ("about:blank", "about:blank"),
    ("data:text/plain,hi", "data:text/plain,hi"),
    ("data:text/html,<b>hi</b>", "data:text/html,<b>hi</b>"),
    ("data:text/html;base64,PGI+aGk8L2I+", "data:text/html;base64,PGI+aGk8L2I+"),
    ("https://example.com/", "https://example.com/"),
]
for label, u in URLS:
    e, t, dt = call("browser_navigate", {"url": u, "wait_for_load": True}, 40)
    print("  %-40s %-5s %.2fs  %s" % (label, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:88]))

print("\n== ② 不依赖外网的断点全链路(about:blank + document.write 内联脚本) ==")
call("browser_navigate", {"url": "about:blank", "wait_for_load": True}, 30)
time.sleep(0.5)
e, t, _ = call("browser_debugger_enable", {})
print("  debugger_enable: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:70]))

e, t, _ = call("browser_debugger_set_breakpoint", {"url": ".*", "line": 0})
print("  set_breakpoint(url='.*', line=0): %s %s"
      % ("ERR" if e else "OK", t.replace("\n", " ")[:90]))

# document.write 注入的 <script> **会执行**; 且它是当前文档的一份内联脚本 -> 断点可命中
WRITE = ("document.write('<html><body><script>function mcpT(a){var b=a+1;return b}"
         "window.__mcpW=mcpT(41);<\\/script></body></html>');document.close();'wrote'")
e, t, dt = call("browser_execute_js", {"code": WRITE}, 30)
print("  document.write 注入内联脚本: %s %.2fs %s"
      % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:80]))

e, t, dt = call("browser_debugger_wait_paused", {"max_ms": 8000}, 30)
print("  wait_paused(期望命中): %s %.1fs %s"
      % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:110]))

e, t, dt = call("browser_debugger_stack", {}, 30)
print("  stack: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:110]))

e, t, dt = call("browser_debugger_resume", {}, 30)
print("  resume: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:70]))

e, t, dt = call("browser_execute_js", {"code": "String(window.__mcpW)"}, 30)
print("  注入脚本确实执行过: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:70]))

print("\n== 收尾: 冷重启 ==")
restart()
print("  完成")
