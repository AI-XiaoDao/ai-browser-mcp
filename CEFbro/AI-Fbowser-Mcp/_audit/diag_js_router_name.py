# -*- coding: utf-8 -*-
"""关键诊断: CEF 的 message router 到底给页面注入了哪个 JS 函数名? 何时注入?

线索: 类库自带例子里 **先 FBrowser_JS交互_注册(...) 再 FBrowser_创建浏览器(...)**
(main3.wsv:45-46 注册, :113 创建浏览器) —— 说明 router 配置疑似在**浏览器创建时**生效,
运行期新注册的名字不会注入到已存在的浏览器(本轮实测 window.mcpQuery 刷新后仍不存在)。
本脚本: 直接查页面上已存在的候选函数名(默认 cefQuery 等), 用**真值**判断, 不猜。
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

PROBE = ("JSON.stringify(['cefQuery','cefQueryCancel','cefQuerytest','cefQueryCanceltest',"
         "'mcpQuery','_cefQuery'].map(function(n){"
         "return n+':'+(typeof window[n])}))")


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

print("== A) 未注册任何名字时, 页面上有哪些候选函数? ==")
call("browser_navigate", {"url": "https://example.com/?probe=1", "wait_for_load": True}, 90)
print("   %s" % call("browser_execute_js", {"code": PROBE}, 40)[1][:400])

print("\n== B) 以默认名 cefQuery 注册一个处理器, 再查(不刷新) ==")
e, t = call("browser_js_query", {"action": "register", "name": "cefQuery"})
print("   register -> isError=%s %s" % (e, t[:180]))
print("   不刷新: %s" % call("browser_execute_js", {"code": PROBE}, 40)[1][:400])

print("\n== C) 刷新后再查 ==")
call("browser_reload", {}, 90)
time.sleep(0.8)
print("   刷新后: %s" % call("browser_execute_js", {"code": PROBE}, 40)[1][:400])

print("\n== D) 若 cefQuery 存在, 直接往返一次 ==")
js = ("window.__r='';window.__e='';"
      "if(typeof window.cefQuery==='function'){"
      "window.cefQuery({request:'probe-hello',onSuccess:function(r){window.__r=String(r)},"
      "onFailure:function(c,m){window.__e=c+':'+m}});'sent'}"
      "else{'nofunc'}")
e, t = call("browser_execute_js", {"code": js}, 40)
print("   调用: %s" % t[:200])
time.sleep(1.2)
print("   页面侧: %s" % call("browser_execute_js",
                            {"code": "JSON.stringify({r:window.__r,e:window.__e})"}, 40)[1][:240])
print("   宿主日志: %s" % call("browser_js_query", {"action": "log", "limit": 3}, 40)[1][:300])
