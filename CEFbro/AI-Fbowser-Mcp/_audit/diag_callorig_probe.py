# -*- coding: utf-8 -*-
"""最小化探针: 为什么模板里 __callOrig 在安装期就 "is not a function"?

逐步缩小: 先确认页面基础环境, 再单目标安装, 再复现"捕获 call"这一步。
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


def probe(tag, code):
    e, t = call("browser_execute_js", {"code": code}, 30)
    print("  [%s] isError=%s  %s" % ("ERR" if e else " ok", e, t[:230]))
    return e, t


call("browser_navigate", {"url": "https://example.com/?probe=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== P0 页面基础环境 ==")
probe("基础", "JSON.stringify({c:typeof Function.prototype.call,a:typeof Function.prototype.apply,"
             "t:typeof Function.prototype.toString,s:typeof String.prototype.split,"
             "u:typeof String.prototype.substring,"
             "cw:typeof Function.prototype.call.__mcp_orig})")

print("\n== P1 只捕获, 不使用 ==")
probe("捕获", "(function(){var c=Function.prototype.call;return typeof c})()")

print("\n== P2 捕获后立刻用它 split(与模板同一写法) ==")
probe("捕获+用", "(function(){var __callOrig=Function.prototype.call,"
                "__split=String.prototype.split;var p=__callOrig(__split,'a.b.c','.');"
                "return JSON.stringify(p)})()")

print("\n== P3 只装 1 个目标(Function.prototype.apply), 用捕获的 call/split ==")
probe("单目标", "(function(){var __callOrig=Function.prototype.call;var __split=String.prototype.split;"
               "var __t='Function.prototype.apply';var __parts=__callOrig(__split,__t,'.');"
               "var __obj=window;for(var i=0;i<__parts.length-1;i++){__obj=__obj[__parts[i]]}"
               "var __m=__parts[__parts.length-1];var __orig=__obj[__m];"
               "var __w=function(){return __callOrig(Function.prototype.apply,__orig,this,arguments)};"
               "__obj[__m]=__w;return 'installed:'+__t+' origType='+typeof __orig})()")

print("\n== P4 关键怀疑点: 先包装 Function.prototype.apply 后, 再捕获 call 会拿到什么? ==")
probe("包装后再取", "(function(){var __AP=Function.prototype;var __origApply=__AP.apply;"
                  "__AP.apply=function(){return __origApply.apply(this,arguments)};"
                  "var c=__AP.call;return JSON.stringify({callType:typeof c,"
                  "callIsSame:c===__origApply,applyType:typeof __AP.apply})})()")

print("\n== P5 上一个探针把 apply 包装了 -> 立刻重载清场, 复验基础环境 ==")
call("browser_navigate", {"url": "https://example.com/?probe=2", "wait_for_load": True}, 45)
time.sleep(0.5)
probe("清场后", "JSON.stringify({c:typeof Function.prototype.call,a:typeof Function.prototype.apply})")
