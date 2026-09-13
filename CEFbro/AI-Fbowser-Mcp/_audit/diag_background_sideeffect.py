# -*- coding: utf-8 -*-
"""定位: "用过后台浏览器之后, 主浏览器的同步调用会卡 ~35 秒" —— 是后台特有, 还是多浏览器通用?

时序判据(只做后台相关操作, 不创建可见窗口):
  T1 主浏览器 execute_js  → 基线, 应很快
  T2 创建后台浏览器 + 在它上面 execute_js + 关闭
  T3 主浏览器 execute_js  → 若变慢, 就是后台那几步造成的
  T4 主浏览器 execute_js 第二次 → 看是否一次性(恢复)还是持续
  T5 后台浏览器上再执行一次(不关闭) → 看是否是"后台浏览器的原生JS路径"本身留下了未回收的请求槽
另外打印 /health 与浏览器数量, 便于判断是否留下了残留实例。
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


def step(tag, name, args, timeout=60):
    e, t, dt = call(name, args, timeout)
    print("  %-46s %-4s %6.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:95]))
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

print("== T1 基线(主浏览器) ==")
step("T1 主浏览器 execute_js", "browser_execute_js", {"code": "1+1"})
step("T1b 主浏览器 get_text", "browser_get_text", {"selector": "h1"})

print("\n== T2 后台浏览器: 创建 → 使用 → 关闭 ==")
step("T2a create background:true", "browser_create",
     {"url": "https://example.com/?isolation=1", "background": True}, 60)
step("T2b 后台浏览器 execute_js", "browser_execute_js",
     {"code": "document.title", "browser_id": 2}, 60)
step("T2c 关闭后台浏览器", "browser_close", {"browser_id": 2}, 60)

print("\n== T3 之后主浏览器是否变慢 ==")
step("T3a 主浏览器 execute_js(第1次)", "browser_execute_js", {"code": "1+1"}, 60)
step("T3b 主浏览器 execute_js(第2次, 看是否恢复)", "browser_execute_js", {"code": "1+1"}, 60)
step("T3c 主浏览器 get_text", "browser_get_text", {"selector": "h1"}, 60)

print("\n== T4 health 与实例数 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read().decode())
    print("  health: %s" % json.dumps(h, ensure_ascii=False)[:220])
except Exception as ex:
    print("  health 读取失败: %s" % ex)
step("T4 browser_list", "browser_list", {})

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
