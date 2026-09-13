# -*- coding: utf-8 -*-
"""观察者修复是否也覆盖**可见**第二浏览器? (上一轮观察到可见窗口也扰动实例)

判据: 创建可见第二浏览器 → 用 browser_id 在它上面执行 JS → 再测主浏览器的 get_text/execute_js。
若主浏览器仍为 0.0x 秒, 说明"CDP 观察者被来回切换"这个根因对可见/后台两种浏览器是**同一个**,
修复是通用的; 若仍退化, 则另有独立原因, 需如实保留警示。
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


def call(name, args, timeout=60):
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


def probe(tag):
    e, t, dt = call("browser_get_text", {"selector": "h1"}, 60)
    print("    %-28s %-4s %6.2fs  %s" % (tag + " get_text", "ERR" if e else "OK", dt,
                                        t.replace("\n", " ")[:50]))
    e2, t2, dt2 = call("browser_execute_js", {"code": "1+1"}, 60)
    print("    %-28s %-4s %6.2fs  %s" % (tag + " execute_js", "ERR" if e2 else "OK", dt2,
                                        t2.replace("\n", " ")[:50]))
    return dt, dt2


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

call("browser_navigate", {"url": "https://example.com/?vis=1", "wait_for_load": True}, 45)
time.sleep(0.5)
print("== 创建**可见**第二浏览器之前 ==")
before = probe("V1")

print("\n== 创建可见第二浏览器(background 省略) ==")
e, t, dt = call("browser_create", {"url": "https://example.com/?vis=2"}, 60)
print("    create visible  %-4s %6.2fs %s" % ("ERR" if e else "OK", dt,
                                              t.replace("\n", " ")[:60]))
e, t, _ = call("browser_list", {})
ids = [int(x) for x in re.findall(r'"id"\s*:\s*(\d+)', t)]
bid = max(ids) if ids else 2
print("    当前浏览器 id: %s (将对 id=%d 执行 JS)" % (ids, bid))

print("\n== 在可见第二浏览器上执行 JS ==")
e, t, dt = call("browser_execute_js", {"code": "document.title", "browser_id": bid}, 60)
print("    exec#%d          %-4s %6.2fs %s" % (bid, "ERR" if e else "OK", dt,
                                               t.replace("\n", " ")[:60]))

print("\n== 之后主浏览器是否仍健康 ==")
after = probe("V2")

print("\n== 汇总 ==")
print("  主浏览器 get_text : %.2fs -> %.2fs" % (before[0], after[0]))
print("  主浏览器 execute_js: %.2fs -> %.2fs" % (before[1], after[1]))
ok = after[0] < 3.0 and after[1] < 5.0
print("  结论: %s" % ("修复对可见第二浏览器同样有效(主浏览器不受影响)" if ok
                      else "可见第二浏览器仍会扰动主浏览器 —— 需另查原因"))

call("browser_close", {"browser_id": bid}, 40)
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("  已关闭")
