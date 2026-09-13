# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.2)

def cdp_ok(tag):
    e1,t1,_ = v4.call("browser_dom_query", {"selector":"h1"}, 40)
    e2,t2,_ = v4.call("browser_dom_rect", {"selector":"h1"}, 40)
    ok1 = "Example Domain" in t1
    ok2 = '"width"' in t2
    print("  %-34s dom_query=%-16s dom_rect=%s" % (tag, "OK" if ok1 else t1.replace(chr(10)," ")[:16], "OK" if ok2 else t2.replace(chr(10)," ")[:24]))
    return ok1 and ok2

print("=== CDP 路径在各操作前后的可用性 ===")
cdp_ok("初始")
print("   [动作] browser_network {action:'enable'}")
v4.call("browser_network", {"action":"enable"}, 40)
time.sleep(1.5)
cdp_ok("enable 网络日志之后")
print("   [动作] browser_network {action:'disable'}")
e,t,_ = v4.call("browser_network", {"action":"disable"}, 40)
print("      disable 回复: %s" % t.replace(chr(10)," ")[:90])
time.sleep(1.5)
cdp_ok("disable 之后")
print("   [动作] browser_vip_enable_js_env {enable:true}")
v4.call("browser_vip_enable_js_env", {"enable":True}, 40)
time.sleep(1.5)
cdp_ok("enable_js_env 之后")
print("   [动作] browser_vip_enable_inspector {enable:true}")
v4.call("browser_vip_enable_inspector", {"enable":True}, 40)
time.sleep(2.0)
cdp_ok("重新注册观察者之后")
