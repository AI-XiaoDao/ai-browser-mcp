# -*- coding: utf-8 -*-
"""验收(修正版): hook 的 console.log 自指通路 + push/splice 清理 + trace + 提示文案。

★ 上一版验收的两类自伤(都已修正, 记下来):
  (a) 参数值写错: hook 的 type 应为 `eval_dynamic`(不是 eval); kernel trace 必须显式传 action。
  (b) **在挂钩与触发之间重载了页面** -> Hook 被清掉, 于是"读日志 count=0"被误判成失败。
      正确顺序: 勾上 -> **同页**触发 -> 再读日志。
判据:
 ① 勾 console.log 自身 -> 同页调用 console.log 不崩(修复前: 包装器内再引用 console.log -> 进自己 -> 崩)
 ② 同页再勾 Array.prototype.push -> a.push 仍 len=3(语义), 且记录动作不自递归
 ③ 勾 eval_dynamic -> 同页 eval('1+1') 仍得 2
 ④ 读 hook_logs 必须 count>0, 且能看到 ①② 的目标(证明记录真的落盘)
 ⑤ kernel trace action=start 目标含 push -> 同页触发后 T.calls>0
 ⑥ 提示文案: 省略 action 时的拒绝文案必须指向**真实存在**的 action(修复前它说 action:status,
    而合法值只有 start/get/clear/stop -> 照做会二次失败)
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


def call(name, args, timeout=60):
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


def hook(name, args, tries=10):
    """挂钩类工具是异步的: 回执带 task_id, 必须轮询到最终结果才算数。"""
    e, t, _ = call(name, args)
    m = re.search(r'(task_[0-9_]+)', t) or re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
    if not m:
        return e, t
    tid = m.group(1)
    last = (e, t)
    for _ in range(tries):
        e2, t2, _ = call("mcp_result", {"request_id": tid, "consume": True}, 30)
        if t2 and ("未找到任务结果" not in t2) and ("pending" not in t2.lower()):
            return e2, t2
        last = (e2, t2)
        time.sleep(0.5)
    return last


def unesc(t):
    return t.replace('\\"', '"').replace(" ", "")


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:84]))


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
# 只重载这一次; 之后**不再重载**(重载会清掉 Hook)
call("browser_navigate", {"url": "https://example.com/?acc=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① 勾 console.log 自身, 同页调用它 ==")
e, t = hook("browser_reverse_hook", {"target": "console.log", "type": "function_call"})
print("   勾选: isError=%s %s" % (e, t[:230]))
rec("勾 console.log 成功", (not e) and ('"found":true' in unesc(t)), t[:84])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){console.log('mcp-acc-1');return 'called'})()"}, 30)
print("   调用: isError=%s %s" % (e, t[:200]))
rec("调用 console.log 未崩(修复前必崩)", (not e) and ("called" in t), t[:84])

print("\n== ② 同页再勾 Array.prototype.push ==")
e, t = hook("browser_reverse_hook", {"target": "Array.prototype.push", "type": "function_call"})
print("   勾选: isError=%s %s" % (e, t[:230]))
rec("勾 Array.prototype.push 成功", (not e) and ('"found":true' in unesc(t)), t[:84])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){var a=[];a.push(1,2,3);"
                        "return JSON.stringify({len:a.length})})()"}, 30)
print("   调用: %s" % t[:160])
rec("a.push 仍 len=3(语义未坏)", (not e) and ('"len":3' in unesc(t)), t[:84])

print("\n== ③ 勾 eval_dynamic, 同页调 eval ==")
e, t = hook("browser_reverse_hook", {"target": "eval", "type": "eval_dynamic"})
print("   勾选: isError=%s %s" % (e, t[:230]))
rec("勾 eval_dynamic 成功", not e, t[:84])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){var v=eval('1+1');return JSON.stringify({v:v})})()"}, 30)
print("   调用: %s" % t[:160])
rec("eval 仍得 2", (not e) and ('"v":2' in unesc(t)), t[:84])

print("\n== ④ 读 hook_logs(此时 Hook 仍在页面上) ==")
e, t, _ = call("browser_reverse_hook_logs", {}, 60)
print("   isError=%s %s" % (e, t[:420]))
u = unesc(t)
m = re.search(r'"count":(\d+)', u)
cnt = int(m.group(1)) if m else -1
rec("count>0(记录真的落盘)", (not e) and cnt > 0, "count=%s" % cnt)
rec("日志里能看到 console.log 目标", "console.log" in u, t[:84])
rec("日志里能看到 Array.prototype.push 目标", "Array.prototype.push" in u, t[:84])

print("\n== ⑤ kernel trace action=start, 同页触发 ==")
e, t, _ = call("browser_kernel_reverse_trace",
               {"action": "start", "targets": json.dumps(["parseInt"])}, 60)
print("   启动: isError=%s %s" % (e, t[:200]))
rec("trace 启动成功", not e, t[:84])
e, t, _ = call("browser_execute_js",
               {"code": "(function(){parseInt('7');var T=window.__MCP_TRACE__;"
                        "return JSON.stringify({calls:T?T.calls.length:-1,errs:T?T.errors:-1})})()"}, 30)
print("   记录: %s" % t[:220])
u = unesc(t)
rec("T.calls>0(trace 真在工作)", '"calls":0' not in u and '"calls":' in u, t[:84])

print("\n== ⑥ 提示文案必须指向真实存在的 action ==")
e, t, _ = call("browser_kernel_reverse_trace", {}, 30)
print("   %s" % t[:300])
bad_status = "action:status" in t
rec("不再让调用方去传不存在的 action:status", not bad_status, t[:84])
rec("改为指向真实 action(get)", "action:get" in t, t[:84])
e2, t2, _ = call("browser_kernel_reverse_trace", {"action": "get"}, 30)
rec("照提示传 action:get 确实可用", not e2, t2[:84])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
