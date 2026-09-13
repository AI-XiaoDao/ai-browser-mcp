# -*- coding: utf-8 -*-
"""第二个浏览器上执行 JS 的 ~30 秒到底花在哪? 用不同 max_ms 探边界。

判据(一次调用能分辨三种情况):
  · 传 max_ms=3000 后**仍然**耗时约 30s  -> 30 秒不在"同步等待"上(是原生 JS 调用自身的超时/回调延迟)
  · 传 max_ms=3000 后耗时约 3s 且**结果正确** -> 结果其实早就回来了, 只是默认等待过长(可调)
  · 传 max_ms=3000 后耗时约 3s 但结果是空/哨兵 -> 回调确实晚到, 需要改的是回调/通知链路

同时测主浏览器作对照(它走 CDP, 应当 0.0x 秒), 以确认差异只在第二个浏览器。
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


def call(name, args, timeout=90):
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
    print("  %-46s %-4s %6.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:80]))


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

call("browser_navigate", {"url": "https://example.com/?mm=1", "wait_for_load": True}, 45)
time.sleep(0.5)
print("== 对照: 主浏览器(走 CDP) ==")
show("main execute_js (无 max_ms)", *call("browser_execute_js", {"code": "document.title"}))
show("main execute_js (max_ms=3000)", *call("browser_execute_js",
                                           {"code": "document.title", "max_ms": 3000}))

print("\n== 创建后台浏览器 ==")
show("create background", *call("browser_create",
                                {"url": "https://example.com/?mm=2", "background": True}, 60))
time.sleep(0.8)

print("\n== 第二个浏览器: 不同 max_ms 的耗时与结果 ==")
show("browser_id=2 execute_js (无 max_ms)", *call("browser_execute_js",
                                                 {"code": "document.title", "browser_id": 2}, 90))
show("browser_id=2 execute_js (max_ms=3000)", *call("browser_execute_js",
                                                   {"code": "document.title", "browser_id": 2,
                                                    "max_ms": 3000}, 90))
show("browser_id=2 execute_js (max_ms=1000)", *call("browser_execute_js",
                                                   {"code": "document.title", "browser_id": 2,
                                                    "max_ms": 1000}, 90))
show("browser_id=2 get_text (对照: 另一个工具)", *call("browser_get_text",
                                                     {"selector": "h1", "browser_id": 2}, 90))

print("\n== 事后主浏览器仍应健康(上一轮已修) ==")
show("main get_text", *call("browser_get_text", {"selector": "h1"}))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
