# -*- coding: utf-8 -*-
"""先内联验证"新版模板(改用 Reflect.apply)"能否真正装上并记录, 再决定是否写回源码。

背景(实测二分):
  · `var a=Function.prototype.call; ...; a(fn,null,'V')` -> "a is not a function"(连普通函数也不行)
  · `Reflect.apply(fn, thisArg, args)` -> 正常
故模板不再"捕获 call/apply 再调用", 一律改用 Reflect.apply。
另修一个静态确定的次生缺陷: 原来 `calls:__count` 是**安装瞬间的快照**, 恒为 0 -> 改成 getter 实时读。

本脚本把候选新模板**内联执行**, 断言: ①装得上 ②不崩 ③记录真的增长 ④__mcp_orig 在 ⑤calls 实时。
只有全部通过才写回源码。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"

TARGETS = ("['Function.prototype.apply','Function.prototype.call','Array.prototype.push',"
           "'Array.prototype.pop','String.prototype.indexOf','String.prototype.charAt']")

CANDIDATE = (
    "(function(){var __targets=" + TARGETS + ";"
    "var __ts=Function.prototype.toString,__split=String.prototype.split,__sub=String.prototype.substring;"
    "var __count=0;var __max=500;var __results=[];"
    "var __log=function(__t,__args){if(__count>=__max)return;var __s='',__n=__args.length,__li;"
    "for(__li=0;__li<__n;__li++){var __v=__args[__li];"
    "__s+=(__li?',':'')+((typeof __v==='string')?Reflect.apply(__sub,__v,[0,200]):typeof __v)}"
    "__results[__results.length]={target:__t,args:__s,ts:Date.now()};__count++};"
    "for(var __ti=0;__ti<__targets.length;__ti++){var __t=__targets[__ti];"
    "var __parts=Reflect.apply(__split,__t,['.']);var __obj=window;var __ok=1;"
    "for(var __pi=0;__pi<__parts.length-1;__pi++){__obj=__obj[__parts[__pi]];if(!__obj){__ok=0;break}}"
    "if(!__ok)continue;var __method=__parts[__parts.length-1];var __orig=__obj[__method];"
    "if(typeof __orig!=='function')continue;"
    "var __wrapper=function(){__log(__t,arguments);return Reflect.apply(__orig,this,arguments)};"
    "__wrapper.__mcp_orig=__orig;"
    "__wrapper.toString=function(){return Reflect.apply(__ts,__orig,[])};"
    "__obj[__method]=__wrapper}"
    "var __pub={instrumented:__targets.length,results:__results};"
    "Object.defineProperty(__pub,'calls',{get:function(){return __count},enumerable:true});"
    "window.__mcp_instrument_results=__pub;"
    "return JSON.stringify({installed:true,targets:__targets.length})})()")

PROBE = ("(function(){var a=[];a.push(1,2,3);var r=Array.prototype.slice.call(a,1);"
         "var f=function(x){return x+1};var y=f.apply(null,[41]);"
         "return JSON.stringify({len:a.length,r:r,y:y})})()")


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


def unesc(t):
    return t.replace('\\"', '"').replace(" ", "")


res = []


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:88]))


call("browser_navigate", {"url": "https://example.com/?cand=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== 前置探针: Reflect.apply 能转发 arguments 吗(模板第3处要用) ==")
e, t = call("browser_execute_js",
            {"code": "(function(){var f=function(a,b){return a+b};"
                     "var w=function(){return Reflect.apply(f,this,arguments)};return w(2,3)})()"}, 30)
print("   %s" % t[:160])
rec("Reflect.apply 可转发 arguments", (not e) and ("5" in t), t[:88])

print("\n== ① 安装候选模板 ==")
e, t = call("browser_execute_js", {"code": CANDIDATE}, 30)
print("   isError=%s %s" % (e, t[:220]))
rec("模板装得上(不再抛错)", (not e) and ("installed" in unesc(t)), t[:88])

print("\n== ② 装上后跑会走包装器的 JS: 不崩且结果正确 ==")
e, t = call("browser_execute_js", {"code": PROBE}, 30)
print("   %s" % t[:240])
ok2 = (not e) and ('"len":3' in unesc(t)) and ('"y":42' in unesc(t))
rec("不崩且 len=3,r=[2,3],y=42", ok2, t[:88])

print("\n== ③ 记录真的在增长(calls 实时 + results 非空) ==")
e, t = call("browser_execute_js",
            {"code": "JSON.stringify({i:window.__mcp_instrument_results.instrumented,"
                     "c:window.__mcp_instrument_results.calls,"
                     "rs:window.__mcp_instrument_results.results.length,"
                     "orig:typeof Array.prototype.push.__mcp_orig,"
                     "tos:Array.prototype.push.toString().indexOf('native code')>=0})"}, 30)
print("   状态: %s" % t[:260])
u = unesc(t)
rec("instrumented=6", '"i":6' in u, t[:88])
rec("calls>0(已修为实时计数)", '"c":0' not in u and '"c":' in u, t[:88])
rec("results 非空", '"rs":0' not in u and '"rs":' in u, t[:88])
rec("__mcp_orig 已挂(卸载入口前提)", '"orig":"function"' in u, t[:88])
rec("toString 仍是原生(不暴露插装)", '"tos":true' in u, t[:88])

call("browser_navigate", {"url": "https://example.com/?cleaned=1", "wait_for_load": True}, 45)
bad = [x for x in res if not x[1]]
print("\n== 候选模板结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
