# -*- coding: utf-8 -*-
"""验收非 CDP 的 JS↔宿主查询通道（browser_js_query）。

要证明的是**完整往返**: 页面调用 -> 宿主收到 -> 宿主应答 -> 页面 onSuccess 拿到应答文本。
判据:
  · 页面侧 window.__qReply 应等于 "mcp-echo:hello-page"(证明应答真的回到了页面)
  · 宿主侧 action=log 应出现 "hello-page"(证明页面请求真的到达了宿主)
  · unregister 后同一调用应走 onFailure(证明注销真的生效)
只在**页面已刷新**(JS 函数注入新文档)后测, 否则会误判成"通道不通"。
"""
import json
import os
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
NAME = "mcpQuery"
R = []


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:300])


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
call("browser_navigate", {"url": "https://example.com/?jsq=1", "wait_for_load": True}, 90)

print("== 1) list(未注册时应为空且不报错) ==")
e, t = call("browser_js_query", {"action": "list"})
print("   -> isError=%s %s" % (e, t[:260]))
arm("未注册时 list 正常返回且注册名为空", (not e) and ('"registered_names":""' in t), t[:220])

print("\n== 2) register ==")
e, t = call("browser_js_query", {"action": "register", "name": NAME})
print("   -> isError=%s %s" % (e, t[:300]))
arm("register 成功", (not e) and ('"success":true' in t), t[:240])

print("\n== 3) 刷新页面(JS 函数在新文档注入) ==")
call("browser_reload", {}, 90)
time.sleep(1.0)

print("\n== 4) 页面发起查询(完整往返) ==")
js = ("window.__qReply='';window.__qErr='';"
      "try{window.%s({request:'hello-page',"
      "onSuccess:function(r){window.__qReply=String(r)},"
      "onFailure:function(c,m){window.__qErr=c+':'+m}});'sent'}"
      "catch(e){'callerr:'+e.message}" % NAME)
e, t = call("browser_execute_js", {"code": js}, 40)
print("   调用: isError=%s %s" % (e, t[:200]))
time.sleep(1.2)
e2, t2 = call("browser_execute_js",
              {"code": "JSON.stringify({r:window.__qReply,e:window.__qErr})"}, 40)
print("   页面侧结果: %s" % t2[:260])
arm("★页面 onSuccess 拿到宿主应答(完整往返成功)",
    'mcp-echo:hello-page' in t2, t2[:240])

print("\n== 5) 宿主侧日志(证明请求真的到达宿主) ==")
e, t = call("browser_js_query", {"action": "log", "limit": 5})
print("   -> isError=%s %s" % (e, t[:400]))
arm("★宿主日志出现页面请求原文", (not e) and ('hello-page' in t), t[:300])

print("\n== 6) unregister 后同一调用应走 onFailure ==")
e, t = call("browser_js_query", {"action": "unregister", "name": NAME})
print("   unregister -> isError=%s %s" % (e, t[:200]))
call("browser_reload", {}, 90)
time.sleep(0.8)
js2 = ("window.__qReply2='';window.__qErr2='';"
       "try{window.%s({request:'after-unregister',"
       "onSuccess:function(r){window.__qReply2=String(r)},"
       "onFailure:function(c,m){window.__qErr2=c+':'+m}});'sent'}"
       "catch(e){window.__qErr2='callerr:'+e.message;'callerr'}" % NAME)
call("browser_execute_js", {"code": js2}, 40)
time.sleep(1.0)
e, t = call("browser_execute_js",
            {"code": "JSON.stringify({r:window.__qReply2,e:window.__qErr2})"}, 40)
print("   页面侧结果: %s" % t[:260])
arm("注销后不再被宿主应答(应答为空/报错)",
    'after-unregister' not in t or 'mcp-echo' not in t, t[:240])

e, t = call("browser_js_query", {"action": "list"})
print("   list -> %s" % t[:220])
arm("注销后名单已清空(不留幽灵注册)", '"registered_names":""' in t, t[:200])

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
