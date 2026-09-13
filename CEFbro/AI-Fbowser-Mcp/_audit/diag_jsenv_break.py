# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.2)

def state(tag):
    e1,t1,_ = v4.call("browser_dom_query", {"selector":"h1"}, 40)
    e2,t2,_ = v4.call("browser_execute_js", {"code":"document.querySelector('h1').textContent"}, 30)
    e3,t3,_ = v4.call("browser_get_text", {"selector":"h1"}, 40)
    print("  %-26s dom_query=%-14s execute_js=%-20s get_text=%s" % (
        tag, "OK" if "Example Domain" in t1 else t1.replace(chr(10)," ")[:14],
        "OK" if "Example Domain" in t2 else t2.replace(chr(10)," ")[:20],
        "OK" if "Example Domain" in t3 else t3.replace(chr(10)," ")[:20]))

state("初始")
print("  [动作] vip_enable_js_env {enable:true}")
v4.call("browser_vip_enable_js_env", {"enable":True}, 40)
time.sleep(1.5)
state("js_env 启用后")
print("  [动作] vip_enable_js_env {enable:false}")
v4.call("browser_vip_enable_js_env", {"enable":False}, 40)
time.sleep(1.5)
state("js_env 关闭后(能否恢复?)")
print("  [动作] vip_enable_js_env {enable:true} 再开")
v4.call("browser_vip_enable_js_env", {"enable":True}, 40)
time.sleep(1.5)
state("再次启用后")
