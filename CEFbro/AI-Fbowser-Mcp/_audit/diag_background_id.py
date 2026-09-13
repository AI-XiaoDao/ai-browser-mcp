# -*- coding: utf-8 -*-
"""定位: 后台浏览器建出来了(browser_list 有它), 但按 browser_id 取不到 —— 卡在哪一步?
一次把 browser_list 的**完整原文**打出来(含每个浏览器的全部字段), 再逐个探测按 id 的读取路径。
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


def call(name, args, timeout=45):
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
    print("  %-34s %-4s %5.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:230]))


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

print("== 创建后台浏览器 ==")
show("create background:true", *call("browser_create",
                                    {"url": "https://example.com/?bg2=1",
                                     "background": True}, 60))
time.sleep(1.0)

print("\n== browser_list 完整原文(看它从哪来的、字段有哪些) ==")
show("browser_list", *call("browser_list", {}))

print("\n== 按 id 的读取路径逐个探 ==")
show("browser_status {browser_id:2}", *call("browser_status", {"browser_id": 2}, 30))
show("browser_get_url {browser_id:2}", *call("browser_get_url", {"browser_id": 2}, 30))
show("browser_execute_js {browser_id:2}", *call("browser_execute_js",
                                               {"code": "document.title", "browser_id": 2}, 30))
show("browser_status(不传 id, 主浏览器)", *call("browser_status", {}, 30))

print("\n== 再等 2 秒重试(排除'刚建好还没登记'的时序因素) ==")
time.sleep(2.0)
show("browser_execute_js {browser_id:2} 重试", *call("browser_execute_js",
                                                    {"code": "document.title", "browser_id": 2}, 30))

print("\n== 收尾 ==")
show("close browser_id:2", *call("browser_close", {"browser_id": 2}, 30))
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("  已关闭")
