import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a,t=40):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    except Exception as ex: return "EXC:%s"%ex, time.time()-st
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:170], time.time()-st
h=json.loads(urllib.request.urlopen(B+"/health",timeout=8).read())
print("健康: tools=%s cdp_ready=%s latency_max=%s"%(h.get("tool_count"),h.get("cdp_ready"),h.get("latency_max_ms")))
t,el=c("browser_get_url",{}); print("1) 当前页面      %5.2fs %s"%(el,t))
t,el=c("browser_status",{}); print("2) status        %5.2fs %s"%(el,t[:150]))
t,el=c("browser_execute_js",{"code":"1+1","max_ms":5000},12); print("3) execute_js    %5.2fs %s"%(el,t[:120]))
t,el=c("browser_cdp_call",{"method":"Debugger.enable","params":"{}"},30); print("4) 裸CDP Debugger.enable %5.2fs %s"%(el,t[:170]))
