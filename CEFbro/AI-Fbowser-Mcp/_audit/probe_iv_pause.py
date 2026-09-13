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
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:150], time.time()-st
c("browser_debugger_enable",{})
c("browser_reverse_skip_pauses",{"skip":False}); time.sleep(0.2)
print("1) 基线 execute_js 1+1        :", c("browser_execute_js",{"code":"1+1"})[0])
print("2) install 插装               :", c("browser_reverse_instrument_script",{"action":"install"})[0])
print("3) 注入新脚本(可能挂住)        :", c("browser_execute_js",{"code":"var s=document.createElement('script');s.textContent='window.__ZZ=1';document.head.appendChild(s);'inj'","max_ms":2500},12))
print("4) 注入后页面是否卡住(=已暂停):", c("browser_execute_js",{"code":"1+1","max_ms":2500},12))
print("5) 读缓存事件 Debugger.paused :", c("browser_cdp_event",{"event_name":"Debugger.paused"},12)[0])
print("6) skip_pauses=true 后能否恢复 :", c("browser_reverse_skip_pauses",{"skip":True})[0][:60], "->", c("browser_execute_js",{"code":"1+1","max_ms":2500},12)[0])
print("7) 清场 Debugger.disable     :", c("browser_cdp_call",{"method":"Debugger.disable","params":"{}"},20)[0][:80])
