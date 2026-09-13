import json,urllib.request,time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=30).read().decode())
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:220]
def cdp(m,p): return c("browser_cdp_call",{"method":m,"params":json.dumps(p)})
print("1) Debugger.disable 是否能清掉插装:")
print("   ",cdp("Debugger.disable",{}))
time.sleep(0.4)
print("2) disable 后重新安装(若成功=已被清掉;若报already enabled=没清掉):")
print("   ",cdp("Debugger.setInstrumentationBreakpoint",{"instrumentation":"beforeScriptExecution"}))
time.sleep(0.3)
print("3) 再次 disable 清场, 并跳过一次暂停确保可用:")
print("   ",cdp("Debugger.disable",{}))
print("4) 确认页面仍可正常执行JS:")
print("   ",c("browser_execute_js",{"code":"1+1"})[:120])
print("5) 健康检查:")
h=json.loads(urllib.request.urlopen(B+"/health",timeout=8).read())
print("   cdp_ready=%s latency_max=%s"%(h.get("cdp_ready"),h.get("latency_max_ms")))
