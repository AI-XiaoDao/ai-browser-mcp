# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

# 不做任何导航, 直接打 JS(模拟 AI 启动后第一件事)
for i in range(1, 7):
    t0=time.time()
    e,t,_ = v4.call("browser_execute_js", {"code":"1+1"}, 40)
    print("  第%d次 browser_execute_js 1+1 : %5.1fs err=%-5s %s" % (i, time.time()-t0, e, t.replace(chr(10)," ")[:80]))
    time.sleep(0.5)

print()
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.0)
for i in range(1, 4):
    t0=time.time()
    e,t,_ = v4.call("browser_dom_query", {"selector":"h1"}, 40)
    print("  导航后 第%d次 dom_query(h1): %5.1fs err=%-5s %s" % (i, time.time()-t0, e, t.replace(chr(10)," ")[:70]))
    time.sleep(0.5)
