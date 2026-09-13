# -*- coding: utf-8 -*-
"""验收"仅回执工具改同步"(1 个 Core 白名单 + 8 个逆向调用点)。

判据是**区分性**的:
  · 之前: 一律回 {"_async":true,"message":"CDP已提交:<方法>"} —— 既无数据也无提示
  · 之后: (a) 内核有返回值时必须带回(identifier / breakpointId / cdp_result)
          (b) **参数错误必须显式报错**(这是"不静默假成功"的关键臂: 之前同样报"已提交")

对照臂: browser_cdp_call 本来就在白名单里(一直能拿结果) —— 用它验证 browser_cdp 现在与之一致。
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

R = []


def c(n, a, to=70):
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


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:300])


def no_receipt(t):
    return 'CDP已提交' not in t


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
c("browser_navigate", {"url": "https://example.com/?receipt=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

print("== 1) browser_cdp 现在应与 browser_cdp_call 一致(带回结果) ==")
e1, t1 = c("browser_cdp", {"method": "Runtime.evaluate",
                           "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"})
print("   browser_cdp      -> isError=%s | %s" % (e1, t1[:260]))
e2, t2 = c("browser_cdp_call", {"method": "Runtime.evaluate",
                                "params": {"expression": "1+1", "returnByValue": True}})
print("   browser_cdp_call -> isError=%s | %s" % (e2, t2[:200]))
arm("browser_cdp 带回真实结果(不再是已提交回执)",
    (not e1) and no_receipt(t1) and ('"value":2' in t1 or '"value": 2' in t1),
    "isError=%s | %s" % (e1, t1))
arm("browser_cdp 与 browser_cdp_call 行为一致(两者都含求值结果)",
    ('"value":2' in t1 or '"value": 2' in t1) and ('"value":2' in t2 or '"value": 2' in t2),
    "cdp=%s || call=%s" % (t1[:90], t2[:90]))

print("\n== 2) browser_cdp 逃生门 async_only=true 仍应走异步 ==")
e3, t3 = c("browser_cdp", {"method": "Runtime.evaluate",
                           "params": "{\"expression\":\"1+1\"}", "async_only": True})
print("   -> isError=%s | %s" % (e3, t3[:200]))
arm("async_only=true 回异步回执(逃生门有效)",
    ('_async' in t3) or ('CDP已提交' in t3), "isError=%s | %s" % (e3, t3))

print("\n== 3) browser_cdp 方法名错误应显式报错 ==")
e4, t4 = c("browser_cdp", {"method": "NoSuchDomain.noSuchMethod", "params": "{}"})
print("   -> isError=%s | %s" % (e4, t4[:240]))
arm("无效 CDP 方法名报错(不再假成功)", e4 and no_receipt(t4), "isError=%s | %s" % (e4, t4))

print("\n== 4) 逆向各工具: 正常路径有返回值 / 或诚实成功 ==")
e, t = c("browser_reverse_preload", {"code": "void 0"})
print("   preload        -> isError=%s | %s" % (e, t[:220]))
arm("preload 带回 identifier(内核真实返回值)",
    (not e) and no_receipt(t) and ('"identifier"' in t), "isError=%s | %s" % (e, t))

e, t = c("browser_reverse_cdp_hook", {"function_name": "parseInt"})
print("   cdp_hook       -> isError=%s | %s" % (e, t[:220]))
arm("cdp_hook 带回 breakpointId",
    (not e) and no_receipt(t) and ('"breakpointId"' in t), "isError=%s | %s" % (e, t))

e, t = c("browser_reverse_dom_breakpoint", {"type": "xhr", "url": "*api*"})
print("   dom_breakpoint -> isError=%s | %s" % (e, t[:220]))
arm("dom_breakpoint 诚实成功(无已提交回执)", (not e) and no_receipt(t),
    "isError=%s | %s" % (e, t))

e, t = c("browser_reverse_websocket", {"action": "enable"})
print("   websocket en   -> isError=%s | %s" % (e, t[:220]))
arm("websocket enable 诚实成功(无已提交回执)", (not e) and no_receipt(t),
    "isError=%s | %s" % (e, t))

e, t = c("browser_reverse_heap", {"action": "start_sampling"})
print("   heap sampling  -> isError=%s | %s" % (e, t[:220]))
arm("heap start_sampling 诚实成功(无已提交回执)", (not e) and no_receipt(t),
    "isError=%s | %s" % (e, t))

print("\n== 5) ★关键臂: 参数错误必须显式暴露(之前一律假成功) ==")
e, t = c("browser_reverse_cdp_hook", {"function_name": "definitelyNotAFunc_zz9"})
print("   cdp_hook(不存在的函数) -> isError=%s | %s" % (e, t[:260]))
arm("cdp_hook 对不存在的函数报错(不再假成功)", e and no_receipt(t),
    "isError=%s | %s" % (e, t))

e, t = c("browser_reverse_dom_breakpoint", {"type": "bogus_type_zz9"})
print("   dom_breakpoint(非法type) -> isError=%s | %s" % (e, t[:260]))
arm("dom_breakpoint 对非法 type 报错(不再假成功)", e and no_receipt(t),
    "isError=%s | %s" % (e, t))

e, t = c("browser_reverse_heap", {"action": "get_object", "object_id": "zz9"})
print("   heap get_object(坏 id) -> isError=%s | %s" % (e, t[:260]))
arm("heap get_object 对坏 id 报错(不再假成功)", e and no_receipt(t),
    "isError=%s | %s" % (e, t))

print("\n== 收尾: 清函数断点 + 存活检查 ==")
c("browser_cdp_call", {"method": "Debugger.setSkipAllPauses", "params": {"skip": True}})
c("browser_debugger_enable", {"action": "disable"})
e, t = c("browser_evaluate", {"code": "'alive:'+document.title"}, 20)
print("   %s" % t[:120])

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    if not v:
        print("   未通过: %s" % label)
