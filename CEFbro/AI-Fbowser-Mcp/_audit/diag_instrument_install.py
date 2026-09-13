# -*- coding: utf-8 -*-
"""诊断: 新版插装到底装上没有? (臂B"不崩"必须先排除"其实什么都没装")

思路: 把**新版模板**（与源码里逐字一致, 只把 targets 固定成默认 6 项）直接在页面上求值,
     看它自己的返回值/异常 —— 这比通过工具的异步通道猜测要直接。
      返回 {installed:true,...} -> 模板 OK, 问题在"工具怎么提交/何时生效";
      返回 JS 异常            -> 我的模板本身有错(最可能)。
再顺手用 mcp_result 轮询工具的真实安装结果, 两边对照。
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

TARGETS = ("['Function.prototype.apply','Function.prototype.call','Array.prototype.push',"
           "'Array.prototype.pop','String.prototype.indexOf','String.prototype.charAt']")

# 与 src/MCP_Server_Core.wsv 中新模板逐字一致(仅 targets 固定)
NEW_JS = (
    "(function(){var __targets=" + TARGETS + ";var __ts=Function.prototype.toString,"
    "__callOrig=Function.prototype.call,__applyOrig=Function.prototype.apply;"
    "var __split=String.prototype.split,__sub=String.prototype.substring;"
    "var __count=0;var __max=500;var __results=[];"
    "var __log=function(__t,__args){if(__count>=__max)return;var __s='',__n=__args.length,__li;"
    "for(__li=0;__li<__n;__li++){var __v=__args[__li];"
    "__s+=(__li?',':'')+((typeof __v==='string')?__callOrig(__sub,__v,0,200):typeof __v)}"
    "__results[__results.length]={target:__t,args:__s,ts:Date.now()};__count++};"
    "for(var __ti=0;__ti<__targets.length;__ti++){var __t=__targets[__ti];"
    "var __parts=__callOrig(__split,__t,'.');var __obj=window;var __ok=1;"
    "for(var __pi=0;__pi<__parts.length-1;__pi++){__obj=__obj[__parts[__pi]];if(!__obj){__ok=0;break}}"
    "if(!__ok)continue;var __method=__parts[__parts.length-1];var __orig=__obj[__method];"
    "if(typeof __orig!=='function')continue;"
    "var __wrapper=function(){__log(__t,arguments);"
    "return __callOrig(__applyOrig,__orig,this,arguments)};"
    "__wrapper.__mcp_orig=__orig;"
    "__wrapper.toString=function(){return __callOrig(__ts,__orig)};"
    "__obj[__method]=__wrapper}"
    "window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};"
    "return JSON.stringify({installed:true,targets:__targets.length})})()")


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


call("browser_navigate", {"url": "https://example.com/?diaginst=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== 1) 直接把新版模板在页面上求值(最直接) ==")
e, t = call("browser_execute_js", {"code": NEW_JS}, 30)
print("   isError=%s" % e)
print("   %s" % t[:400])

print("\n== 2) 装完之后: 全局/原函数是否都在 ==")
e, t = call("browser_execute_js",
            {"code": "JSON.stringify({g:typeof window.__mcp_instrument_results,"
                     "i:window.__mcp_instrument_results?window.__mcp_instrument_results.instrumented:-1,"
                     "rs:window.__mcp_instrument_results?window.__mcp_instrument_results.results.length:-1,"
                     "orig:typeof Array.prototype.push.__mcp_orig,"
                     "callorig:typeof Function.prototype.call.__mcp_orig})"}, 30)
print("   %s" % t[:400])

print("\n== 3) 真正跑一遍会走包装器的 JS, 看记录是否增长 ==")
e, t = call("browser_execute_js",
            {"code": "(function(){var a=[];a.push(1,2,3);var r=Array.prototype.slice.call(a,1);"
                     "return JSON.stringify({len:a.length,r:r,"
                     "calls:window.__mcp_instrument_results?window.__mcp_instrument_results.calls:-1,"
                     "rs:window.__mcp_instrument_results?window.__mcp_instrument_results.results.length:-1})})()"}, 30)
print("   %s" % t[:400])

print("\n== 4) 对照: 工具自己的异步安装结果(轮询 mcp_result) ==")
call("browser_navigate", {"url": "https://example.com/?diaginst=2", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t = call("browser_reverse_instrument", {}, 45)
print("   提交回执: %s" % t[:250])
m = re.search(r'(task_[0-9_]+)', t)
if not m:
    m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
print("   取到 task_id = %s" % (m.group(1) if m else None))
if m:
    tid = m.group(1)
    for i in range(6):
        e2, t2 = call("mcp_result", {"request_id": tid}, 30)
        print("   [%d] isError=%s %s" % (i, e2, t2[:300]))
        if t2 and ("pending" not in t2.lower()):
            break
        time.sleep(0.6)
    e3, t3 = call("browser_execute_js",
                  {"code": "typeof window.__mcp_instrument_results"}, 30)
    print("   装完后 g = %s" % t3[:150])

call("browser_navigate", {"url": "https://example.com/?cleaned=1", "wait_for_load": True}, 45)
print("\n(已清场)")
