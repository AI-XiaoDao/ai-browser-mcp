# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.5)

def row(tag):
    out=[]
    for name,args,want in (("browser_dom_query",{"selector":"h1"},"Example Domain"),
                           ("browser_get_text",{"selector":"h1"},"Example Domain"),
                           ("browser_execute_js",{"code":"document.querySelector('h1').textContent"},"Example Domain")):
        e,t,_ = v4.call(name,args,40)
        out.append("%s=%s" % (name.replace("browser_",""), "OK" if want in t else "FAIL"))
    print("  %-24s %s" % (tag, "  ".join(out)))

row("初始")
print("  [动作] vip_enable_js_env {enable:true}  (应被拒绝)")
e,t,_ = v4.call("browser_vip_enable_js_env", {"enable":True}, 40)
print("     err=%s -> %s" % (e, t.replace(chr(10)," ")[:150]))
time.sleep(1.5)
row("拒绝之后(应仍正常)")
print("\n  [正对照] 显式 confirm:true 应放行")
e,t,_ = v4.call("browser_vip_enable_js_env", {"enable":True,"confirm":True}, 40)
print("     err=%s -> %s" % (e, t.replace(chr(10)," ")[:130]))
