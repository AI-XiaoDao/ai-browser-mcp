# -*- coding: utf-8 -*-
"""把 browser_debugger_wait_paused 的异常钉死: "事件明明在, 它却报超时"。

判据(交替读, 排除"事件只是晚到"的解释):
  last_paused(读到暂停) → wait_paused(短超时) → last_paused(又读到) → wait_paused(再短超时)
若每次 wait_paused 都超时而夹在中间的 last_paused 都能读到同一暂停, 就不能再用"事件晚到"解释,
只能说明 wait_paused 自己的读取路径有问题(它走 等待CDP事件 → 取CDP事件数据JSON, 与 last_paused 同源,
差别在 等待CDP事件 内部会 解锁/加锁 MCP执行锁 并 延时(100) 轮询)。
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

print("== 制造一个真实暂停(用零前置自动暂停, 最省事) ==")
e, t, dt = call("browser_debugger_stack", {})
print("  stack: %s %.2fs" % ("ERR" if e else "OK", dt))

print("\n== 交替读: last_paused / wait_paused × 3 轮 ==")
for i in (1, 2, 3):
    e1, t1, d1 = call("browser_debugger_last_paused", {}, 30)
    has = "call_frame_id" in t1
    print("  第%d轮 last_paused : %-4s %.2fs 含暂停帧=%s" % (i, "ERR" if e1 else "OK", d1, has))
    e2, t2, d2 = call("browser_debugger_wait_paused", {"max_ms": 2000}, 30)
    print("  第%d轮 wait_paused : %-4s %.2fs %s" % (i, "ERR" if e2 else "OK", d2,
                                                   t2.replace("\n", " ")[:80]))

print("\n== 对照: last_paused 也是靠 ensure 自造暂停才成功吗? ==")
e, t, dt = call("browser_debugger_last_paused", {}, 30)
print("  last_paused: %s %.2fs auto_prepared=%s"
      % ("ERR" if e else "OK", dt, "auto_prepared" in t))
print("  (若带 auto_prepared, 说明读到的是它自己刚造的暂停, 而非等待中的那个)")

call("browser_debugger_resume", {})
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
