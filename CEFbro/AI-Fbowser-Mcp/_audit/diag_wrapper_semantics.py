# -*- coding: utf-8 -*-
"""微探针: Reflect 方式包装 push/call 之后, 语义还在不在?

(a) 直接 Reflect.apply 调原生 push
(b) 用 Reflect 包装 Array.prototype.push 后, a.push(1,2,3) 是否仍正确
(c) 用 Reflect 包装 Function.prototype.call 后, Array.prototype.slice.call(a,1) 是否仍正确
若 (b)/(c) 都不能保语义 -> "包装这些内建"本身在本环境不可行, 应改为**不包装它们**并如实报告跳过;
若都能保语义 -> 问题在我的模板别处, 可继续修。
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
    req = urllib.request.Request(BASE + "/mcp",
                                 data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    rr = resp.get("result") or {}
    return bool(rr.get("isError")), "".join(
        i.get("text") or "" for i in (rr.get("content") or [])
        if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)


def probe(tag, code, expect):
    e, t = call("browser_execute_js", {"code": code}, 30)
    good = (not e) and (expect in t)
    print("  [%s] %-34s %s" % ("PASS" if good else "FAIL", tag, t[:180]))
    return good


call("browser_navigate", {"url": "https://example.com/?micro=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== (a) 直接 Reflect.apply 调原生 push ==")
probe("(a) Reflect.apply push", "(function(){var a=[1,2];Reflect.apply(Array.prototype.push,a,[3]);"
                               "return a.length})()", '"message":"3"')

print("\n== (b) 用 Reflect 包装 push, 再看 a.push 是否仍正确 ==")
probe("(b) 包装 push 后语义", "(function(){var o=Array.prototype.push;"
                              "Array.prototype.push=function(){return Reflect.apply(o,this,arguments)};"
                              "var a=[];var r=a.push(1,2,3);"
                              "return JSON.stringify({len:a.length,ret:r})})()",
      '"len":3')

print("\n== (c) 用 Reflect 包装 call, 再看 slice.call 是否仍正确 ==")
call("browser_navigate", {"url": "https://example.com/?micro=2", "wait_for_load": True}, 45)
time.sleep(0.5)
probe("(c) 包装 call 后语义", "(function(){var o=Function.prototype.call;"
                              "Function.prototype.call=function(){return Reflect.apply(o,this,arguments)};"
                              "var a=[1,2,3];return JSON.stringify(Array.prototype.slice.call(a,1))})()",
      '[2,3]')

print("\n== (d) 包装 apply 后, f.apply 是否仍正确 ==")
call("browser_navigate", {"url": "https://example.com/?micro=3", "wait_for_load": True}, 45)
time.sleep(0.5)
probe("(d) 包装 apply 后语义", "(function(){var o=Function.prototype.apply;"
                               "Function.prototype.apply=function(){return Reflect.apply(o,this,arguments)};"
                               "var f=function(x){return x+1};return f.apply(null,[41])})()",
      '"message":"42"')

call("browser_navigate", {"url": "https://example.com/?cleaned=1", "wait_for_load": True}, 45)
print("\n(已清场)")
