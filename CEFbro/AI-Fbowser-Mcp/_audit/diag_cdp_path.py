# -*- coding: utf-8 -*-
import importlib.util, sys, time, json, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60)
time.sleep(1.0)

def probe(tag):
    print("  --- %s ---" % tag)
    for name,args in (("browser_dom_query",{"selector":"h1"}),
                      ("browser_dom_inner_html",{"selector":"h1"}),
                      ("browser_dom_rect",{"selector":"h1"}),
                      ("browser_execute_js",{"code":"document.querySelector('h1').textContent"})):
        e,t,_ = v4.call(name,args,40)
        print("    %-24s err=%-5s %s" % (name, e, t.replace(chr(10)," ")[:110]))
        time.sleep(0.3)

probe("修复前(当前状态)")

print("\n=== 尝试重新注册 CDP 观察者: browser_vip_enable_inspector {enable:true} ===")
e,t,_ = v4.call("browser_vip_enable_inspector", {"enable": True}, 40)
print("  err=%s %s" % (e, t.replace(chr(10)," ")[:200]))
time.sleep(3)
probe("重新注册观察者之后")

print("\n=== health ===")
h=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/health",timeout=10).read())
print("  cdp_ready=%s" % h.get("cdp_ready"))
