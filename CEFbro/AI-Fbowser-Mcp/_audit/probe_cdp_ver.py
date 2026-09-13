import json,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def cdp(m,p):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"browser_cdp_call","arguments":{"method":m,"params":json.dumps(p)}}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=30).read().decode())
    rr=d.get("result") or {}
    t="".join(i.get("text") or "" for i in (rr.get("content") or []))
    return t.replace("\n"," ")[:230]
tests=[
 ("instrumentation 参数名(旧版)", "Debugger.setInstrumentationBreakpoint", {"instrumentation":"beforeScriptExecution"}),
 ("eventName 参数名(新版)",      "Debugger.setInstrumentationBreakpoint", {"eventName":"beforeScriptExecution"}),
 ("两者都给",                    "Debugger.setInstrumentationBreakpoint", {"instrumentation":"beforeScriptExecution","eventName":"beforeScriptExecution"}),
 ("remove(不存在?)",             "Debugger.removeInstrumentationBreakpoint", {"instrumentation":"beforeScriptExecution"}),
 ("setPauseOnExceptions",        "Debugger.setPauseOnExceptions", {"state":"caught"}),
 ("searchInContent 可用",        "Debugger.searchInContent", {"scriptId":"1","query":"x"}),
]
for tag,m,p in tests:
    print("%-30s -> %s"%(tag,cdp(m,p)))
