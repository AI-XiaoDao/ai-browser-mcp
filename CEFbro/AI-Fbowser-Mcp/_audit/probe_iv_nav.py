import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a,t=30):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    except Exception as ex: return "EXC:%s"%ex, time.time()-st
    rr=d.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:130], time.time()-st
c("browser_debugger_enable",{})
c("browser_reverse_skip_pauses",{"skip":False}); time.sleep(0.2)
print("1) install beforeScriptExecution:", c("browser_reverse_instrument_script",{"action":"install"})[0][:110])
t,el = c("browser_navigate",{"url":"https://example.com/?ivnav=%d"%int(time.time()),"wait_for_load":True,"max_ms":6000},25)
print("2) 导航到新页面(短超时)        : %.1fs %s"%(el,t[:110]))
t,el = c("browser_execute_js",{"code":"1+1","max_ms":2500},12)
print("3) 导航后页面是否被暂停        : %.1fs %s"%(el,t[:100]))
t,el = c("browser_cdp_event",{"event_name":"Debugger.paused"},12)
print("4) Debugger.paused 事件        :", t[:120])
print("5) 用另一种脚本执行路径(eval)  :", c("browser_execute_js",{"code":"eval('1+2')","max_ms":2500},12)[0][:90])
t,el = c("browser_cdp_event",{"event_name":"Debugger.paused"},12)
print("6) eval 后 paused 事件         :", t[:120])
print("7) 清场 skip+disable          :", c("browser_reverse_skip_pauses",{"skip":True})[0][:40], c("browser_cdp_call",{"method":"Debugger.disable","params":"{}"},20)[0][:40])
