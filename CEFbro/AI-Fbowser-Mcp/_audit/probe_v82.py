import json,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=30):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:330]
print("A) dom_resolve 原始回复:"); print("  ",raw("browser_reverse_dom_resolve",{"expression":"window"}))
print("B) compile_script 原始回复:"); print("  ",raw("browser_reverse_compile_script",{"source":"var a=1;"}))
print("C) await_promise 原始回复:"); print("  ",raw("browser_reverse_await_promise",{"expression":"Promise.resolve(7)"}))
print("D) listeners 原始回复:"); print("  ",raw("browser_reverse_listeners",{"selector":"document"}))
print("E) 裸CDP Runtime.evaluate(returnByValue:false) 拿objectId:")
print("  ",raw("browser_cdp_call",{"method":"Runtime.evaluate","params":json.dumps({"expression":"window","returnByValue":False})}))
print("F) 裸CDP Runtime.compileScript:")
print("  ",raw("browser_cdp_call",{"method":"Runtime.compileScript","params":json.dumps({"expression":"var a=1;","sourceURL":"mcp://t"})}))
print("G) 裸CDP Debugger.searchInContent(看是否 not enabled):")
print("  ",raw("browser_cdp_call",{"method":"Debugger.searchInContent","params":json.dumps({"scriptId":"1","query":"a"})}))
