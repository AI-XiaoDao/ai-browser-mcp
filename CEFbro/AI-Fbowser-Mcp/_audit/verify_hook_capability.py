# -*- coding: utf-8 -*-
"""Hook 能力端到端验证（目标 ≤25 秒）。

做法: 在页面上注入一个**已知行为的测试函数**, 用 Hook 工具挂上, 再调用它,
然后查 Hook 日志 —— 形成"A 挂 Hook → B 调用 → C 日志里有记录"的闭环。
这比"工具返回了成功"强得多: 它验证 Hook **真的在页面里生效**。

覆盖: browser_reverse_hook(function_call) / browser_reverse_hook_multi /
      browser_reverse_hook_logs / browser_reverse_cdp_hook
"""
import json
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
RUN = str(int(time.time()))[-6:]
res = []
ENVELOPE_ONLY = {"id", "jsonrpc", "success", "data", "message", "result", "error",
                 "result_json", "poll_hint", "_hint", "needs_reload", "ok", "_async"}


def call(name, args, timeout=40):
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
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


def payload(t):
    def collect(n, out, d=0):
        if d > 6:
            return
        if isinstance(n, dict):
            out.append(n)
            for v in n.values():
                collect(v, out, d + 1)
        elif isinstance(n, str) and n.strip().startswith(("{", "[")):
            try:
                collect(json.loads(n), out, d + 1)
            except Exception:
                pass
    s = (t or "").strip()
    try:
        root = json.loads(s)
    except Exception:
        return s
    cands = []
    collect(root, cands)
    best, bs = (root if isinstance(root, dict) else s), -1
    for d in cands:
        sc = len([k for k in d if k not in ENVELOPE_ONLY])
        sc += sum(1 for k, v in d.items()
                  if isinstance(v, list) and v and k not in ENVELOPE_ONLY)
        if sc > bs:
            best, bs = d, sc
    return best


def js(code):
    e, t = call("browser_execute_js", {"code": code})
    if e:
        return None
    s = t.strip()
    try:
        j = json.loads(s)
        if isinstance(j, dict) and "message" in j:
            return str(j["message"])
    except Exception:
        pass
    return s.strip('"')


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-48s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:96]))


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s latency_max=%s" % (h.get("tool_count"), h.get("cdp_ready"),
                                                h.get("latency_max_ms")))
except Exception as ex:
    print("  !! 服务未就绪(%s)" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?hk=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.5)

F1, F2 = "mcpHookFnA" + RUN, "mcpHookFnB" + RUN
# 注入两个行为已知的测试函数(A: 两数相加; B: 字符串拼接)
js("window.%s=function(a,b){return a+b};"
   "window.%s=function(s){return 'X'+s};"
   "window.__hookCalls=0;'ok'" % (F1, F2))
time.sleep(0.3)
rec("测试函数已注入且初始可调用",
    js("String(window.%s(1,2))" % F1) == "3", "A(1,2)=%s" % js("String(window.%s(1,2))" % F1))

print("\n== 1) browser_reverse_hook 挂 function_call Hook ==")
e1, t1 = call("browser_reverse_hook",
              {"type": "function_call", "target": "window." + F1}, 40)
p1 = payload(t1)
print("     回复: %s" % json.dumps(p1, ensure_ascii=False)[:150])
rec("hook 调用提交成功", not e1, t1.replace("\n", " ")[:80])

print("\n== 2) 调用被 Hook 的函数(应仍返回正确值) ==")
time.sleep(0.8)
v = js("String(window.%s(1,2))" % F1)
rec("被 Hook 后函数语义不变(仍返回 3)", v == "3", "A(1,2)=%s" % v)

print("\n== 3) Hook 日志里应有本次调用记录 ==")
time.sleep(0.5)
e3, t3 = call("browser_reverse_hook_logs", {"action": "query"}, 40)
p3 = payload(t3)
blob = json.dumps(p3, ensure_ascii=False)
print("     日志: %s" % blob[:220])
rec("日志含被测函数名或参数", (F1 in blob) or ('"a":1' in blob.replace(" ", "")) or ("1,2" in blob),
    blob[:90])

print("\n== 4) browser_reverse_hook_multi 批量 Hook ==")
e4, t4 = call("browser_reverse_hook_multi",
              {"functions": json.dumps(["window." + F2])}, 40)
p4 = payload(t4)
print("     回复: %s" % json.dumps(p4, ensure_ascii=False)[:150])
rec("hook_multi 未报错", not e4, t4.replace("\n", " ")[:80])
time.sleep(0.8)
v2 = js("String(window.%s('Y'))" % F2)
rec("被 Hook 的函数语义不变(返回 XY)", v2 == "XY", "B('Y')=%s" % v2)

print("\n== 5) browser_reverse_cdp_hook(CDP 函数调用断点) ==")
e5, t5 = call("browser_reverse_cdp_hook", {"function_name": "window." + F1}, 40)
p5 = payload(t5)
print("     回复: %s" % json.dumps(p5, ensure_ascii=False)[:150])
rec("cdp_hook 有明确结果(成功或可行动错误)", not t5.startswith("EXC:"),
    t5.replace("\n", " ")[:80])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
