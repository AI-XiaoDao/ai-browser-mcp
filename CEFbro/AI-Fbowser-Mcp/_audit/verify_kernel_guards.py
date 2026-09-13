# -*- coding: utf-8 -*-
r"""验证第128轮: ①幽灵工具 browser_debugger_pause 已可被发现且拒绝可行动;
             ②browser_kernel_scheme register 不再"空内容也回 success"; ③IPC 队列 action 语义不再静默退化。

要点:
  · 方案注册用**本机临时文件**当预言机(存在/不存在两种), 并在结束时 unregister 复原;
  · IPC: 验证 `browser_kernel_ipc_clear {}`(=不给 action)真的走 clear(而不是静默变成读取队列),
    以及未知 action 被明确拒绝 —— 这两条正是"假成功"的修复点。

用法: py -3 _audit\verify_kernel_guards.py
"""
import json
import os
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


T = {t["name"]: t for t in json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())["tools"]}

print('== ① 幽灵工具 browser_debugger_pause: 可发现 + 拒绝可行动 ==')
rec("已出现在 tools/list(不再是看不见的守卫)", "browser_debugger_pause" in T,
    "工具总数=%d" % len(T))
d = T.get("browser_debugger_pause", {}).get("description", "")
rec("描述写明'已禁用'并给出替代流程",
    ("已禁用" in d) and ("browser_debugger_flow" in d) and ("browser_debugger_wait_paused" in d), d[:90])
e1, t1 = call("browser_debugger_pause", {})
rec("调用它仍按设计拒绝(未变成可用能力)", e1, t1[:70])
rec("拒绝文案给出替代流程", ("debugger_flow" in t1) and ("wait_paused" in t1), t1[:110])

print('\n== ② browser_kernel_scheme register: 空内容/文件不存在不再假成功 ==')
e2, t2 = call("browser_kernel_scheme", {"action": "register", "domain": "kg1"})
rec("data/file 都不给 → 明确拒绝(不注册空方案)", e2 and ("必须提供 data" in t2), t2[:100])
e3, t3 = call("browser_kernel_scheme", {"action": "register", "domain": "kg2",
                                       "file": "C:\\no-such-file-kg.bin"})
rec("file 不存在 → 明确拒绝(不再被静默忽略)", e3 and ("file 不存在" in t3), t3[:110])
fp = os.path.join(tempfile.gettempdir(), "mcp_scheme_probe.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write("<html><body><h1>KGOK</h1></body></html>")
e4, t4 = call("browser_kernel_scheme", {"action": "register", "domain": "kg3", "file": fp})
rec("file 存在 → 注册成功(回归)", (not e4) and ("已注册" in t4), t4[:90])
e5, t5 = call("browser_kernel_scheme", {"action": "register", "domain": "kg4", "data": "<h1>D</h1>"})
rec("data 直接给内容 → 注册成功(回归)", (not e5) and ("已注册" in t5), t5[:80])
for dom in ("kg3", "kg4"):
    call("browser_kernel_scheme", {"action": "unregister", "domain": dom})

print('\n== ③ IPC 队列: action 语义不再静默退化 ==')
e6, t6 = call("browser_kernel_ipc_clear", {})
rec("ipc_clear 不给 action 仍按 clear 执行(不变成读取)",
    (not e6) and ("已清空" in t6), t6[:90])
e7, t7 = call("browser_kernel_ipc_queue", {"action": "cleer"})
rec("未知 action 被明确拒绝(此前会静默退化为读取并回 success)",
    e7 and ("未知 action" in t7) and ("cleer" in t7), t7[:110])
e8, t8 = call("browser_kernel_ipc_queue", {"action": "queue"})
rec("action=queue 仍能读取队列(回归)", not e8, t8[:80])
e9, t9 = call("browser_kernel_ipc_queue", {})
rec("ipc_queue 不给 action 时仍按读取(缺省行为)", not e9, t9[:80])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
