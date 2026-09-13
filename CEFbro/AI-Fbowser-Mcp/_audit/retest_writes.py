# -*- coding: utf-8 -*-
import json,sys,time
sys.path.insert(0,'.')
import importlib.util
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
spec=importlib.util.spec_from_file_location("pw","probe_writes.py")
pw=importlib.util.module_from_spec(spec); spec.loader.exec_module(pw)
# 干净页面重来
pw.call("browser_navigate", {"url": pw.URL, "wait_for_load": True}, 60); time.sleep(1.0)
pw.oracle(pw.SETUP); time.sleep(0.4)
print("== 复测 3 个被预言机超时污染的用例(放宽 oracle 重试) ==")
def oracle2(expr, tries=3):
    for i in range(tries):
        v = pw.oracle(expr)
        if not v.startswith("<ORACLE-ERR"):
            return v
        time.sleep(2.0)
    return v
# dom_set_value
e,t = pw.resolve("browser_dom_set_value", {"selector":"#inp","value":"dom-val"})
got = oracle2("document.querySelector('#inp').value")
print("  dom_set_value: err=%s oracle=%r resp=%s" % (e, got, t[:90]))
# dom_select
e,t = pw.resolve("browser_dom_select", {"selector":"#sel","index":0})
got = oracle2("String(document.querySelector('#sel').selectedIndex)")
print("  dom_select    : err=%s oracle=%r resp=%s" % (e, got, t[:90]))
# dom_click
e,t = pw.resolve("browser_dom_click", {"selector":"#btn"})
got = oracle2("String(window.__clicks)")
print("  dom_click     : err=%s oracle=%r resp=%s" % (e, got, t[:90]))
print("== 另 2 个 fill 工具的反例(未命中) ==")
for tool,args in [("browser_fill_scroll",{"selector":"#nonexistent-xyz"}),
                  ("browser_fill_select",{"selector":"#nonexistent-xyz","value":"a"})]:
    e,t = pw.resolve(tool,args)
    print("  %-22s err=%s resp=%s" % (tool, e, t[:120]))
