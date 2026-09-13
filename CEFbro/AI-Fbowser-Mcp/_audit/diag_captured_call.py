# -*- coding: utf-8 -*-
"""把 P2 的最小复现继续二分: 是"名字带 __"的问题, 还是"用捕获的 call 去调用"这个模式本身不成立?

P6: 与 P2 同形, 但用单字母变量名 + 分开的 var 语句
P7: 用捕获的 call 去调用 split(单字母名)
P8: Reflect.apply 是否可用(这是审计建议的替代调用方式)
P9: 用捕获的 call 去调用一个普通函数
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


def probe(tag, code):
    e, t = call("browser_execute_js", {"code": code}, 30)
    print("  [%s] %-22s %s" % ("ERR" if e else " ok", tag, t[:210]))
    return e, t


call("browser_navigate", {"url": "https://example.com/?p6=1", "wait_for_load": True}, 45)
time.sleep(0.6)

probe("P6 单字母+分开声明",
      "(function(){var a=Function.prototype.call;var s=String.prototype.split;"
      "return a+'|'+s})()")
probe("P7 捕获call去调split",
      "(function(){var a=Function.prototype.call;var s=String.prototype.split;"
      "var p=a(s,'a.b.c','.');return JSON.stringify(p)})()")
probe("P9 捕获call去调普通函数",
      "(function(){var a=Function.prototype.call;var f=function(x){return 'got:'+x};"
      "return a(f,null,'V')})()")
probe("P8 Reflect.apply 可用?",
      "(function(){return JSON.stringify({r:typeof Reflect,ra:typeof Reflect.apply})})()")
probe("P8b 用 Reflect.apply 调 split",
      "(function(){var s=String.prototype.split;"
      "return JSON.stringify(Reflect.apply(s,'a.b.c',['.']))})()")
probe("P10 __ 前缀名字 + 分开声明",
      "(function(){var __a=Function.prototype.call;var __s=String.prototype.split;"
      "return typeof __a})()")
probe("P11 __ 前缀 + 调用",
      "(function(){var __a=Function.prototype.call;var __s=String.prototype.split;"
      "var p=__a(__s,'a.b','.');return JSON.stringify(p)})()")

call("browser_navigate", {"url": "https://example.com/?cleaned=1", "wait_for_load": True}, 45)
print("\n(已清场)")
