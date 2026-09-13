# -*- coding: utf-8 -*-
"""决定性测量: install 的**自检探针**是不是"卡死会话"的唯一触发者?

机理(§108.1): 探针用 Runtime.evaluate 去验证"新脚本是否会暂停", 而这正是刚装上的
beforeScriptExecution 插装所拦截的行为 -> 探针自己触发插装 -> 该 evaluate 永不返回 ->
单条 CDP 队列被占 -> 之后所有 CDP 工具超时。

若成立, 则 **verify:false**(不做探针) 的 install 应当**不会**把会话搞死 ——
那样就能把"默认就卡死"改成"默认可安全使用, 需要自检再显式开"。
若仍卡死, 说明卡死是"装上插装后任何 evaluate 都会被拦"的必然结果, install 无法做到安全。

两臂各自从干净实例开始, 每臂都测: 装入后 JS 是否可用; 再手动跑一次 JS 看是否被拦。
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


def js_alive():
    e, t, dt = call("browser_execute_js", {"code": "1+1"}, 30)
    return (not e) and dt < 8, "%.2fs %s" % (dt, t[:50].replace("\n", " "))


def arm(label, args):
    print("\n== %s ==" % label)
    restart()
    call("browser_navigate", {"url": "https://example.com/?probe=1", "wait_for_load": True}, 45)
    time.sleep(0.6)
    ok0, d0 = js_alive()
    print("   装入前 JS=%s (%s)" % (ok0, d0))
    e, t, dt = call("browser_reverse_instrument_script", args, 60)
    print("   install: isError=%s %.2fs" % (e, dt))
    print("     %s" % t[:260].replace("\n", " "))
    ok1, d1 = js_alive()
    print("   装入后 JS=%s (%s)" % (ok1, d1))
    return ok0, ok1, t


a0, a1, ta = arm("臂① verify=true(默认, 带自检探针)", {"action": "install", "confirm": True})
b0, b1, tb = arm("臂② verify=false(不做探针)", {"action": "install", "confirm": True, "verify": False})

print("\n===== 结论 =====")
print("  臂①(带探针):  装入前 JS=%s -> 装入后 JS=%s" % (a0, a1))
print("  臂②(不带探针): 装入前 JS=%s -> 装入后 JS=%s" % (b0, b1))
if b1 and not a1:
    print("  => **探针就是卡死的触发者**: 不做自检的 install 不会搞死会话。")
    print("     可据此把默认改成 verify=false(需要自检再显式开), 让 install 默认可安全使用。")
elif not b1:
    print("  => 不带探针**同样**卡死 -> 卡死是'装上插装后任何 evaluate 都被拦'的必然结果,")
    print("     install 无法做到默认安全; 只能保持确认闸 + 如实说明后果。")
else:
    print("  => 两臂都正常, 与 §108 的实测矛盾, 需重测。")
restart()
print("\n(已重启)")
