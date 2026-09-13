# -*- coding: utf-8 -*-
import importlib.util, sys, time, json, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

h=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/health",timeout=10).read())
print("health: cdp_ready=%s browsers=%s" % (h.get("cdp_ready"), h.get("browsers")))

print("\n=== 1) CDP 是否可用(browser_execute_js) ===")
for i in range(3):
    e,t,_ = v4.call("browser_execute_js", {"code":"1+1"}, 30)
    print("  第%d次: err=%s -> %s" % (i+1, e, t.replace(chr(10)," ")[:120]))
    time.sleep(0.5)

print("\n=== 2) 当前页面 ===")
e,t,_ = v4.call("browser_get_url", {}, 30)
print("  get_url: %s" % t.replace(chr(10)," ")[:140])

print("\n=== 3) 逐个复现'看起来是旧行为'的工具 ===")
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60)
time.sleep(1.0)
for name,args in (("browser_get_text",{}),
                  ("browser_get_text",{"selector":"h1"}),
                  ("browser_dom_rect",{"selector":"h1"}),
                  ("browser_dom_checked",{"selector":"h1"}),
                  ("browser_dom_selected",{"selector":"h1"}),
                  ("browser_fill_set_value",{"selector":"#nonexistent-xyz","value":"x"})):
    e,t,_ = v4.call(name,args,40)
    print("  %-24s %-28s err=%-5s %s" % (name, json.dumps(args,ensure_ascii=False), e, t.replace(chr(10)," ")[:150]))
    time.sleep(0.4)
