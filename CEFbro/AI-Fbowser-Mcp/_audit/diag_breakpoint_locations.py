# -*- coding: utf-8 -*-
"""诊断: 为什么 setBreakpointByUrl 对已注入的内联脚本返回 locations 为空?

目的有二:
 (1) 为浏览器断点正对照找到**真正能命中**的构造方式(否则无法排除"我把成功路径改坏了");
 (2) 判断"0 locations"到底意味着"终局不可能命中"还是"脚本尚未注册, 稍后会命中" ——
     后者决定我那条"零命中快速失败"是否**过于激进**(可能把合法等待误判为失败)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(name, args, timeout=45):
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


def cdp(method, params):
    e, t = call("browser_cdp_call", {"method": method,
                                    "params": json.dumps(params, ensure_ascii=False)}, 30)
    return e, t


call("browser_navigate", {"url": "https://example.com/?bpdiag=1", "wait_for_load": True}, 45)
time.sleep(0.8)

print("== 0) 当前页面 URL(真值, 用于构造 urlRegex) ==")
e, t = call("browser_execute_js", {"code": "location.href"}, 30)
print("   %s" % t[:160])

print("\n== 1) 注入一个多行内联脚本 ==")
SRC = "\n".join([
    "window.diagTick=0;",
    "window.diagFn=function diagFn(){",
    "  window.diagTick=window.diagTick+1;",
    "};",
])
inj = ("(function(){var s=document.createElement('script');s.id='diagScript';"
       "s.textContent=%s;document.body.appendChild(s);"
       "window.diagTimer=setInterval(window.diagFn,400);return 'ok'})()" % json.dumps(SRC))
e, t = call("browser_execute_js", {"code": inj}, 30)
print("   注入: isError=%s %s" % (e, t[:90]))

print("\n== 2) 已注册脚本清单(V8 注册表) —— 内联脚本的 URL 是什么? ==")
e, t = call("browser_reverse_search_script", {"action": "list"}, 40)
print("   isError=%s" % e)
print("   %s" % t[:900])

print("\n== 3) Debugger.enable 后逐个变体试 setBreakpointByUrl, 看 locations ==")
e, t = cdp("Debugger.enable", {})
print("   enable: %s" % t[:160])
variants = [
    ("urlRegex=example, line=2", {"urlRegex": "example", "lineNumber": 2}),
    ("urlRegex=example, line=0", {"urlRegex": "example", "lineNumber": 0}),
    ("urlRegex='.*', line=2", {"urlRegex": ".*", "lineNumber": 2}),
    ("url='https://example.com/?bpdiag=1', line=2",
     {"url": "https://example.com/?bpdiag=1", "lineNumber": 2}),
]
for label, p in variants:
    e, t = cdp("Debugger.setBreakpointByUrl", p)
    print("   [%s] isError=%s" % (label, e))
    print("      %s" % t[:400])

print("\n== 4) 该内联脚本真正可下断的位置(对照 locations 为空是否正常) ==")
e, t = call("browser_reverse_search_script", {"action": "list"}, 40)
print("   %s" % t[:400])

# 清场
call("browser_execute_js", {"code": "(function(){if(window.diagTimer)clearInterval(window.diagTimer);"
                                   "window.diagFn=function(){};return 'clean'})()"}, 30)
cdp("Debugger.setBreakpointsActive", {"active": False})
print("\n(已清场: 停掉周期任务并关闭断点)")
