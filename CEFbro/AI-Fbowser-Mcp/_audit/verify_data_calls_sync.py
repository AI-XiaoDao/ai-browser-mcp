# -*- coding: utf-8 -*-
"""验收"取数据调用改同步"(7 处)。

判据是**区分性**的: 修复前这 7 条一律只回 `"CDP已提交:<方法>"` 且丢掉数据;
修复后必须 (a) 不再出现"已提交"回执, 且 (b) 要么带回**真实数据**, 要么给出**可行动的诚实报错**。

对照证据(台账原文, 修复前):
  browser_reverse_runtime {action:evaluate, expression:1+1}
    -> {"success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.evaluate"}
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


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


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
c("browser_navigate", {"url": "https://example.com/?datafix=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

RESULTS = []


def arm(label, ok, detail):
    RESULTS.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:260])


print("== 1) runtime evaluate: 1+1 必须带回 2 (修复前只回'CDP已提交') ==")
e, t = c("browser_reverse_runtime", {"action": "evaluate", "expression": "1+1"})
arm("evaluate 带回真实值(不再是已提交回执)",
    (not e) and ("CDP已提交" not in t) and ('"value":2' in t or '"value": 2' in t),
    "isError=%s | %s" % (e, t))

print("\n== 2) runtime evaluate(return_by_value=false) 必须给 objectId ==")
e, t = c("browser_reverse_runtime", {"action": "evaluate",
                                     "expression": "({a:1,b:'two'})",
                                     "return_by_value": False})
m = re.search(r'"objectId":"([^"]+)"', t)
obj_id = m.group(1) if m else ""
arm("拿到 objectId(供下一步下钻)", bool(obj_id) and "CDP已提交" not in t,
    "object_id=%s | %s" % (obj_id, t))

print("\n== 3) runtime properties: 必须带回属性列表 ==")
if obj_id:
    e, t = c("browser_reverse_runtime", {"action": "properties", "object_id": obj_id})
    arm("properties 带回真实属性(a/b)",
        (not e) and ("CDP已提交" not in t) and ("a" in t and "two" in t),
        "isError=%s | %s" % (e, t))
else:
    arm("properties 带回真实属性(a/b)", False, "上一步没拿到 objectId, 本臂无法判读")

print("\n== 4) runtime global: 必须带回 names ==")
e, t = c("browser_reverse_runtime", {"action": "global"})
arm("global 带回 names 列表",
    (not e) and ("CDP已提交" not in t) and ("names" in t),
    "isError=%s | %s" % (e, t))

print("\n== 5) call_fn: 必须带回函数返回值 ==")
# 参数名必须用 arguments(JSON数组); args 是"单文本参数"(会被再包一层单元素数组),
# 传 args='["42"]' 会变成 parseInt('["42"]') -> NaN —— 第一版探针就踩了这个坑。
e, t = c("browser_reverse_call_fn", {"function_name": "parseInt", "arguments": '["42"]'})
arm("call_fn 带回返回值 42",
    (not e) and ("CDP已提交" not in t) and ("42" in t),
    "isError=%s | %s" % (e, t))

print("\n== 6) websocket query: 无效应给**诚实报错**而不是假成功 ==")
e, t = c("browser_reverse_websocket", {"action": "query", "request_id": "1.1"})
arm("query 诚实报错/或带数据(不再假成功)",
    ("CDP已提交" not in t) and (e or "error" in t.lower() or "body" in t.lower()),
    "isError=%s | %s" % (e, t))

print("\n== 7) heap stop_sampling(未先 start): 应诚实报错 ==")
e, t = c("browser_reverse_heap", {"action": "stop_sampling"})
arm("stop_sampling 诚实报错(不再假成功)",
    ("CDP已提交" not in t) and (e or "error" in t.lower() or "profile" in t.lower()),
    "isError=%s | %s" % (e, t))

print("\n== 8) heap get_object: 应给出数据或诚实报错 ==")
e, t = c("browser_reverse_heap", {"action": "get_object", "object_id": "1"})
arm("get_object 数据/诚实报错(不再假成功)",
    ("CDP已提交" not in t) and (e or "object" in t.lower() or "error" in t.lower()),
    "isError=%s | %s" % (e, t))

ok = sum(1 for _, v in RESULTS if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(RESULTS)))
for label, v in RESULTS:
    if not v:
        print("   未通过: %s" % label)
