# -*- coding: utf-8 -*-
import importlib.util, sys, time, json, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

h=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/health",timeout=10).read())
print("health: cdp_ready=%s active_requests=%s async_tasks=%s db=%s" % (
    h.get("cdp_ready"), h.get("active_requests"), h.get("async_tasks"), h.get("db_async_results")))

print("\n=== 当前(疑似退化)状态下各通道 ===")
tests = [("browser_execute_js", {"code":"1+1"}, "2"),
         ("browser_execute_js", {"code":"document.title"}, "Example"),
         ("browser_dom_query", {"selector":"h1"}, "Example Domain"),
         ("browser_get_url", {}, "example.com")]
for name,args,want in tests:
    t0=time.time()
    e,t,_ = v4.call(name,args,40)
    print("  %-22s %-26s %5.1fs err=%-5s %s" % (name, str(args)[:26], time.time()-t0, e, t.replace(chr(10)," ")[:80]))
    time.sleep(0.5)

print("\n=== 当前页面 ===")
e,t,_ = v4.call("browser_get_url", {}, 30)
print("  url=%s" % t.replace(chr(10)," ")[:100])
