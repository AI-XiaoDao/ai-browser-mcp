# -*- coding: utf-8 -*-
"""诊断: 用**正确的参数值**重跑本轮三条验收, 并顺带核对一个可疑提示。

发现: kernel trace 的拒绝文案让调用方"查询状态请显式传 action:status" ——
      只读复核曾说该分支**根本不存在**。若真不存在, 这就是"失败不可行动/误导"的缺陷, 一并核实。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(name, args, timeout=60):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    return bool(rr.get("isError")), "".join(
        i.get("text") or "" for i in (rr.get("content") or [])
        if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)


def full(name, args, tries=10):
    e, t = call(name, args)
    print("   [回执] isError=%s %s" % (e, t[:300]))
    m = re.search(r'(task_[0-9_]+)', t) or re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
    if not m:
        print("   (无 task_id, 不轮询)")
        return e, t
    tid = m.group(1)
    print("   [轮询] task_id=%s" % tid)
    last = (e, t)
    for i in range(tries):
        e2, t2 = call("mcp_result", {"request_id": tid, "consume": True}, 30)
        print("     [%d] isError=%s %s" % (i, e2, t2[:400]))
        last = (e2, t2)
        if t2 and ("pending" not in t2.lower()) and t2.strip() not in ("", "{}"):
            break
        time.sleep(0.5)
    return last


call("browser_navigate", {"url": "https://example.com/?diag2=1", "wait_for_load": True})
time.sleep(0.6)

print("== A 勾 Array.prototype.push (type=function_call) 的**完整**回执与最终结果 ==")
full("browser_reverse_hook", {"target": "Array.prototype.push", "type": "function_call"})

print("\n== B 勾 eval_dynamic(正确 type 名) ==")
call("browser_navigate", {"url": "https://example.com/?diag2=2", "wait_for_load": True})
time.sleep(0.5)
full("browser_reverse_hook", {"target": "eval", "type": "eval_dynamic"})

print("\n== C trace 传 action=start + 目标含 push ==")
call("browser_navigate", {"url": "https://example.com/?diag2=3", "wait_for_load": True})
time.sleep(0.5)
full("browser_kernel_reverse_trace",
     {"action": "start", "targets": json.dumps(["Array.prototype.push", "parseInt"])})

print("\n== D 核对: trace 的 action=status 分支到底存不存在(提示让传 status) ==")
e, t = call("browser_kernel_reverse_trace", {"action": "status"})
print("   isError=%s %s" % (e, t[:400]))

print("\n== E 现在读 hook_logs ==")
e, t = call("browser_reverse_hook_logs", {})
print("   isError=%s %s" % (e, t[:500]))

print("\n== F trace 的实际记录 ==")
e, t = call("browser_execute_js",
            {"code": "JSON.stringify({T:typeof window.__MCP_TRACE__,"
                     "calls:window.__MCP_TRACE__?window.__MCP_TRACE__.calls.length:-1,"
                     "errs:window.__MCP_TRACE__?window.__MCP_TRACE__.errors:-1})"})
print("   %s" % t[:300])
