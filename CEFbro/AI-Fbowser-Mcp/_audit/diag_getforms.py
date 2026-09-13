import json, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=__import__("importlib.util",fromlist=["x"]).spec_from_file_location("v4","verify_round4.py")
v4=__import__("importlib.util",fromlist=["x"]).module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/?q=%d"%int(time.time()),"wait_for_load":True}, 45)
time.sleep(0.4)
v4.call("browser_execute_js", {"code":"document.body.insertAdjacentHTML('beforeend','<form id=f1><input id=qq name=username type=text></form>');'ok'"}, 30)
time.sleep(0.3)
e,t,_ = v4.call("browser_get_forms", {}, 40)
print("err=%s" % e)
print("RAW   = %s" % t[:400])
try:
    j=json.loads(t)
    print("顶层键 = %s" % list(j.keys()))
    for k,v in j.items():
        print("  %-14s type=%-6s %s" % (k, type(v).__name__, str(v)[:120]))
except Exception as ex:
    print("json 解析失败: %s" % ex)
