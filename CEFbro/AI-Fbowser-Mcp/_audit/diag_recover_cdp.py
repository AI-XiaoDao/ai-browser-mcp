# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

def raw(name, args):
    e,t,_ = v4.call(name, args, 40)
    return e, t.replace(chr(10)," ")

print("=== 当前状态(CDP 已在前一次测试中被破坏) ===")
e,t = raw("browser_execute_js", {"code":"document.querySelector('h1').textContent"})
print("  browser_execute_js(原生异步+外部等待): err=%s -> %s" % (e, t[:90]))
e,t = raw("browser_dom_query", {"selector":"h1"})
print("  browser_dom_query(CDP优先):            err=%s -> %s" % (e, t[:90]))

print("\n=== 尝试强制重注册 CDP: 先注销再注册 ===")
e,t = raw("browser_vip_enable_inspector", {"enable":False})
print("  注销: err=%s -> %s" % (e, t[:80]))
time.sleep(2)
e,t = raw("browser_vip_enable_inspector", {"enable":True})
print("  注册: err=%s -> %s" % (e, t[:80]))
time.sleep(3)
e,t = raw("browser_dom_query", {"selector":"h1"})
print("  重注册后 dom_query: err=%s -> %s" % (e, t[:90]))

print("\n=== 再试: 重新导航 + 等待 ===")
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60)
time.sleep(2)
e,t = raw("browser_dom_query", {"selector":"h1"})
print("  导航后 dom_query: err=%s -> %s" % (e, t[:90]))
