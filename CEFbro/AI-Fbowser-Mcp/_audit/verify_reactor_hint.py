import json,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=25):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:300]
print("   add ->", raw("browser_kernel_reactor",{"action":"add","event":"resource_response","code":"1","cooldown_ms":100}))
raw("browser_kernel_reactor",{"action":"clear"})
