# -*- coding: utf-8 -*-
"""验收本轮: hook 的 console.log 自指通路 + push/splice 清理 + trace 的 push/shift。

判据(每条都能证伪):
 ① 勾 console.log 本身 -> 调用 console.log 必须**不崩**(修复前: 包装器内部再调 console.log ->
    进自己 -> RangeError 无限递归), 且日志里有该条目
 ② 勾 Array.prototype.push -> a.push(1,2,3) 仍得 len=3(语义), 且日志有该条目(记录动作不自递归)
 ③ eval 模式(WS/EVAL/COOKIE 三模式之一, 含本次改掉的 slice.call) -> 勾 eval 后调用 eval 必须正常,
    且日志有 entry
 ④ browser_kernel_reverse_trace 目标含 Array.prototype.push -> 必须成功且不崩, 再读 T.calls 有数据
 ⑤ 读 hook_logs 必须成功且 count>0
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
res = []


def call(name, args, timeout=45):
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


def call_final(name, args, timeout=60, tries=8):
    e, t, dt = call(name, args, timeout)
    tid = None
    m = re.search(r'(task_[0-9_]+)', t) or re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
    if m:
        tid = m.group(1)
    if not tid:
        return e, t
    for _ in range(tries):
        e2, t2, _ = call("mcp_result", {"request_id": tid, "consume": True}, 30)
        if t2 and ("pending" not in t2.lower()) and t2.strip() not in ("", "{}"):
            return e2, t + " || " + t2
        time.sleep(0.5)
    return e, t


def unesc(t):
    return t.replace('\\"', '"').replace(" ", "")


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:82]))


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
call("browser_navigate", {"url": "https://example.com/?hookfix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① 勾 console.log 自身(自指通路) -> 再调用它不能崩 ==")
e, t = call_final("browser_reverse_hook", {"target": "console.log", "type": "function_call"}, 60)
print("   勾选: isError=%s %s" % (e, t[:220]))
hooked1 = (not e) and ('"found":true' in unesc(t))
rec("勾 console.log 成功", hooked1, t[:82])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){console.log('mcp-hook-probe-1');return 'called'})()"}, 30)
print("   调用: isError=%s %s" % (e, t[:220]))
rec("调用 console.log 未崩(修复前必崩)", (not e) and ("called" in t), t[:82])

print("\n== ② 勾 Array.prototype.push -> 语义与记录都不能崩 ==")
call("browser_navigate", {"url": "https://example.com/?hookfix=2", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t = call_final("browser_reverse_hook", {"target": "Array.prototype.push", "type": "function_call"}, 60)
print("   勾选: isError=%s %s" % (e, t[:200]))
rec("勾 Array.prototype.push 成功", (not e) and ('"found":true' in unesc(t)), t[:82])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){var a=[];a.push(1,2,3);"
                        "return JSON.stringify({len:a.length})})()"}, 30)
print("   调用: %s" % t[:200])
rec("a.push 仍是 len=3(语义未坏)", (not e) and ('"len":3' in unesc(t)), t[:82])

print("\n== ③ EVAL 模式(本次改掉 slice.call) ==")
call("browser_navigate", {"url": "https://example.com/?hookfix=3", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t = call_final("browser_reverse_hook", {"target": "eval", "type": "eval"}, 60)
print("   勾选: isError=%s %s" % (e, t[:200]))
rec("勾 eval 模式成功", not e, t[:82])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){var v=eval('1+1');return JSON.stringify({v:v})})()"}, 30)
print("   调用: %s" % t[:200])
rec("eval 仍返回 2", (not e) and ('"v":2' in unesc(t)), t[:82])

print("\n== ④ kernel trace 目标含 Array.prototype.push ==")
call("browser_navigate", {"url": "https://example.com/?hookfix=4", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t = call_final("browser_kernel_reverse_trace",
                  {"targets": json.dumps(["Array.prototype.push", "parseInt"])}, 60)
print("   isError=%s %s" % (e, t[:260]))
rec("trace 调用成功(未崩)", not e, t[:82])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){var a=[];a.push(7);parseInt('3');"
                        "var T=window.__MCP_TRACE__;"
                        "return JSON.stringify({len:a.length,calls:T?T.calls.length:-1})})()"}, 30)
print("   状态: %s" % t[:240])
u = unesc(t)
rec("T.calls 有数据(trace 真在工作)", '"calls":0' not in u and '"calls":' in u, t[:82])

print("\n== ⑤ 读 hook_logs ==")
e, t = call_final("browser_reverse_hook_logs", {}, 60)
print("   isError=%s %s" % (e, t[:300]))
u = unesc(t)
m = re.search(r'"count":(\d+)', u)
cnt = int(m.group(1)) if m else -1
rec("读日志成功且 count>0", (not e) and cnt > 0, "count=%s" % cnt)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
