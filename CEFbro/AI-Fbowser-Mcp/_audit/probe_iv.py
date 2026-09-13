import json,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def call(n,a,t=30):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or []))
print("A) install 原始回复:")
print("  ",call("browser_reverse_instrument_script",{"action":"install"})[:400])
print("\nB) 直接对比: 裸CDP Debugger.setBlackboxPatterns(同路径应成功):")
print("  ",call("browser_reverse_blackbox",{"patterns":"[]"})[:260])
print("\nC) remove 原始回复:")
print("  ",call("browser_reverse_instrument_script",{"action":"remove"})[:400])
