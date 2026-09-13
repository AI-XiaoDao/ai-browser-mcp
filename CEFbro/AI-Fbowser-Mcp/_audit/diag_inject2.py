# -*- coding: utf-8 -*-
import json, time, sys
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
def js(x): return val(v4.call("browser_execute_js", {"code":x}, 30)[1])

RUN=str(int(time.time()))[-6:]
INP,BTN,BOX,CB,SEL,PP = ("i"+RUN,"b"+RUN,"x"+RUN,"c"+RUN,"s"+RUN,"p"+RUN)
v4.call("browser_navigate", {"url":"https://example.com/?g=%s"%RUN,"wait_for_load":True}, 45)
time.sleep(0.8)
inj = ("document.body.insertAdjacentHTML('beforeend',"
       "'<input id=\"%s\" value=\"OLD\"><button id=\"%s\">go</button>"
       "<div id=\"%s\">box</div><input type=checkbox id=\"%s\" checked>"
       "<select id=\"%s\"><option>a</option><option selected>b</option></select>"
       "<p id=\"%s\">hello-mcp</p>');"
       "window.__c=0;document.getElementById('%s').addEventListener('click',"
       "function(){window.__c++;});'ok'" % (INP, BTN, BOX, CB, SEL, PP, BTN))
print("INP=%s" % INP)
print("注入返回 = %r" % js(inj))
print("读回 value = %r" % js("document.querySelector('#%s').value" % INP))
print("所有 id = %r" % js("Array.prototype.map.call(document.querySelectorAll('input,button,div,select,p'),function(e){return e.id}).join(',')"))
