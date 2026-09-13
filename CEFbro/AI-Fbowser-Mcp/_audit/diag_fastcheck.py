# -*- coding: utf-8 -*-
import json, re, sys, time, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=__import__("importlib.util",fromlist=["x"]).spec_from_file_location("v4","verify_round4.py")
v4=__import__("importlib.util",fromlist=["x"]).module_from_spec(spec); spec.loader.exec_module(v4)

def val(t):
    s=(t or "").strip()
    try:
        j=json.loads(s)
        if isinstance(j,dict) and "message" in j: return str(j["message"])
    except Exception: pass
    return s.strip('"')

RUN=str(int(time.time()))[-6:]
e,t,_ = v4.call("browser_navigate", {"url":"https://example.com/?f=%s"%RUN,"wait_for_load":True}, 45)
print("navigate: err=%s %s" % (e, t[:80]))
time.sleep(0.8)
inj = ("document.body.insertAdjacentHTML('beforeend','<input id=\"i%s\" value=\"OLD\">');'ok'" % RUN)
e,t,_ = v4.call("browser_execute_js", {"code":inj}, 30)
print("注入: err=%s 原样=%s 解包=%r" % (e, t[:120], val(t)))
e,t,_ = v4.call("browser_execute_js", {"code":"document.querySelector('#i%s').value"%RUN}, 30)
print("读值: err=%s 解包=%r" % (e, val(t)))
e,t,_ = v4.call("browser_execute_js", {"code":"document.querySelectorAll('input').length"}, 30)
print("input 个数: %r" % val(t))
print("body 前 200 字: %r" % val(v4.call("browser_execute_js",{"code":"document.body.innerHTML.slice(0,200)"},30)[1])[:220])
