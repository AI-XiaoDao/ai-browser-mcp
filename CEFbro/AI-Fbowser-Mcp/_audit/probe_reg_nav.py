import json,time,urllib.request
B="http://127.0.0.1:9222"
def p(n,a,t=40):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or []))
def cnt():
    t=p("browser_reverse_search_script",{"action":"list"})
    try:
        j=json.loads(t); s=json.loads(j["data"]["scripts_json"]) if "data" in j else None
    except Exception: s=None
    if s is None:
        import re; m=re.search(r'"count":(\d+)',t); return int(m.group(1)) if m else -1
    return len(s)
def ids():
    t=p("browser_reverse_search_script",{"action":"list"})
    import re
    return re.findall(r'"scriptId":"(\d+)"',t)
p("browser_debugger_enable",{}); time.sleep(0.5)
print("1) enable 后注册表:",cnt(),ids()[:12])
st=p("browser_reverse_search_script",{"query":"example"})
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
print("   搜索 stale/matched:",re.findall(r'"(stale_scripts|matched_scripts|scanned_scripts)":(\d+)',st))
p("browser_navigate",{"url":"https://example.com/?nav%d"%int(time.time()),"wait_for_load":True},45); time.sleep(0.8)
print("2) 导航后注册表(未处理):",cnt(),ids()[:14])
st=p("browser_reverse_search_script",{"query":"example"})
print("   搜索:",re.findall(r'"(stale_scripts|matched_scripts|scanned_scripts)":(\d+)',st))
p("browser_cdp_call",{"method":"Debugger.enable","params":"{}"}); time.sleep(1.2)
print("3) 重新 Debugger.enable 后:",cnt(),ids()[:14])
st=p("browser_reverse_search_script",{"query":"example"})
print("   搜索:",re.findall(r'"(stale_scripts|matched_scripts|scanned_scripts)":(\d+)',st))
