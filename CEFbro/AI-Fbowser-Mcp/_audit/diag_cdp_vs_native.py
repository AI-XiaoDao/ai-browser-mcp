# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.0)

print("=== A) 同一段 full-text JS 走 browser_execute_js(原生JS链路) ===")
js = "(function(){var b=document.body;if(!b)return '__MCP_NO_BODY__';return '__MCP_TEXT__'+String(b.innerText||b.textContent||'')})()"
e,t,_ = v4.call("browser_execute_js", {"code":js}, 30)
print("   err=%s -> %r" % (e, t[:120]))

print("\n=== B) 同一段 h1 提取 JS 走 browser_execute_js ===")
js2 = "(function(){var e=document.querySelector('h1');if(!e)return '__MCP_NO_ELEM__';return '__MCP_TEXT__'+String(e.textContent)})()"
e,t,_ = v4.call("browser_execute_js", {"code":js2}, 30)
print("   err=%s -> %r" % (e, t[:120]))

print("\n=== C) 走 CDP 的工具(内部用 CDP执行JS并等待) ===")
for name,args in (("browser_dom_query",{"selector":"h1"}),
                  ("browser_dom_rect",{"selector":"h1"}),
                  ("browser_get_text",{"selector":"h1"}),
                  ("browser_get_text",{})):
    e,t,_ = v4.call(name,args,40)
    print("   %-22s %-18s err=%-5s %s" % (name, str(args)[:18], e, t.replace(chr(10)," ")[:110]))
    time.sleep(0.3)
