# -*- coding: utf-8 -*-
"""判别实验: 暂停是"自己会消失", 还是"被 wait_paused 弄没的"?

两组对照, 只差"中间有没有调 wait_paused":
  A 组: stack(造暂停) → 等 3s → last_paused        (不碰 wait_paused)
  B 组: stack(造暂停) → wait_paused(2s) → 等 1s → last_paused
若 A 组 3s 后仍读得到暂停、而 B 组读不到, 则"消失"由 wait_paused 引起(而不是主循环节拍或超时清理)。
这是把上一轮的三种猜测(事件晚到/被清理/被自己 resume)收敛成一条的最小实验。
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
            time.sleep(4.5)
            return True
        except Exception:
            pass
    return False


def has_frame(t):
    return "call_frame_id" in t


print("== A 组: 造暂停后**不碰** wait_paused, 看暂停能活多久 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": "https://example.com/", "wait_for_load": True}, 40)
time.sleep(0.6)
e, t, _ = call("browser_debugger_stack", {})
print("  stack: %s" % ("ERR" if e else "OK"))
for wait in (0.0, 1.0, 2.0, 3.0, 5.0):
    if wait:
        time.sleep(wait)
    e, t, dt = call("browser_debugger_last_paused", {}, 25)
    print("   累计等待 %4.1fs 后 last_paused: %-4s 含暂停帧=%s%s"
          % (sum([0.0, 1.0, 2.0, 3.0, 5.0][:[0.0, 1.0, 2.0, 3.0, 5.0].index(wait) + 1]) if wait else 0.0,
             "ERR" if e else "OK", has_frame(t),
             "  (含 auto_prepared: 说明是它自己新造的)" if "auto_prepared" in t else ""))

print("\n== B 组: 造暂停后**调用** wait_paused, 再看暂停还在不在 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": "https://example.com/", "wait_for_load": True}, 40)
time.sleep(0.6)
e, t, _ = call("browser_debugger_stack", {})
print("  stack: %s" % ("ERR" if e else "OK"))
e, t, dt = call("browser_debugger_last_paused", {}, 25)
print("  wait_paused 之前 last_paused: %-4s 含暂停帧=%s" % ("ERR" if e else "OK", has_frame(t)))
e, t, dt = call("browser_debugger_wait_paused", {"max_ms": 2000}, 25)
print("  wait_paused: %-4s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:70]))
time.sleep(1.0)
e, t, dt = call("browser_debugger_last_paused", {}, 25)
print("  wait_paused 之后 last_paused: %-4s 含暂停帧=%s%s"
      % ("ERR" if e else "OK", has_frame(t),
         "  (含 auto_prepared: 它自己新造了一个)" if "auto_prepared" in t else ""))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
