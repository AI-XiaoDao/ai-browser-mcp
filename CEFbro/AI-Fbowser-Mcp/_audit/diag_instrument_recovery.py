# -*- coding: utf-8 -*-
"""测量: 装了 browser_reverse_instrument_script 之后, 有没有**任何**能恢复 JS 通道的办法?

上一轮实测: 装上后 browser_execute_js 30s 超时, resume 与它自己的 suppress 都救不回来, 只有重启。
本轮先看清机理(读源码得到):
  自检探针(Reverse:969)用 `Runtime.evaluate` 去验证"新脚本执行前是否会暂停" —— 而此刻刚装上的
  **beforeScriptExecution 插装正是对"执行脚本"生效的**, 于是**探针自己触发插装**:
  页面暂停 -> 这个 evaluate 永不返回 -> 项目的单条 CDP 队列被这条永久 pending 的请求占住
  -> 之后所有走 CDP 的工具(S 含 resume/suppress)全部超时; browser_status 走原生故仍正常。
也就是说: 这不是"插装坏了", 而是"探测手段被自己的插装拦住"+"队列被占".

于是候选恢复路径依次是:
  A. resume(已在上一轮否掉)
  B. suppress = setSkipAllPauses {skip:true}(上一轮也超时 —— 因为它自己也要走被占住的队列)
  C. browser_debugger_disable(Debugger.disable: 会清掉插装, 但也会清掉用户断点)
  D. 清掉那条卡住的 CDP 映射/任务后再 suppress
本脚本逐条**实测**哪个真能恢复, 每测一条都从干净实例重来。
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
    """JS 通道是否可用: execute_js 走 CDP Runtime.evaluate。"""
    e, t, dt = call("browser_execute_js", {"code": "1+1"}, 35)
    return (not e) and dt < 10, "%.2fs %s" % (dt, t[:60].replace("\n", " "))


def arm():
    """装上插装(并等它返回)。

    ★ 必须显式传 confirm:true —— 上一轮我给 install 加了确认闸(见报告 §102), 第一版这里没传,
      于是 install 每次都被**拒绝**, 插装根本没装上, JS 通道自然一直是好的,
      结果被打成"三个候选都能恢复" —— 一个完全无判别力的结论。测试脚本必须跟着产品契约走。
    """
    e, t, dt = call("browser_reverse_instrument_script",
                    {"action": "install", "confirm": True}, 60)
    print("     install: isError=%s %.2fs %s" % (e, dt, t[:150].replace("\n", " ")))
    if e or ("需要显式确认" in t):
        print("     !! install 未成功装上, 本轮结论无效")
        return None
    return t


def trial(label, steps):
    print("\n== %s ==" % label)
    restart()
    call("browser_navigate", {"url": "https://example.com/?rec=1", "wait_for_load": True}, 45)
    time.sleep(0.6)
    ok0, d0 = js_alive()
    print("     装入前 JS=%s (%s)" % (ok0, d0))
    arm()
    ok1, d1 = js_alive()
    print("     装入后 JS=%s (%s)" % (ok1, d1))
    for name, args in steps:
        e, t, dt = call(name, args, 60)
        print("     [%s] isError=%s %.2fs %s" % (name, e, dt, t[:110].replace("\n", " ")))
        ok, d = js_alive()
        print("        -> JS 恢复? %s (%s)" % (ok, d))
        if ok:
            return True, name
    return False, None


results = []
for label, steps in (
    ("候选 A: resume", [("browser_debugger_resume", {})]),
    ("候选 B: suppress (setSkipAllPauses)", [("browser_reverse_instrument_script", {"action": "suppress"})]),
    ("候选 C: debugger_disable", [("browser_debugger_disable", {})]),
):
    ok, via = trial(label, steps)
    results.append((label, ok, via))

print("\n===== 汇总: 哪条路能恢复 JS 通道 =====")
for label, ok, via in results:
    print("  %-38s %s" % (label, ("能恢复(经由 %s)" % via) if ok else "不能恢复"))
# 收尾: 重启一次, 保证实例可用
restart()
print("\n(已重启, 实例可用)")
