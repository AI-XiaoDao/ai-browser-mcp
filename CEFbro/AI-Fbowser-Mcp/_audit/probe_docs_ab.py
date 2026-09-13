import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a,t=45,tag=""):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:130]
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-26s %5.1fs %s"%(tag,time.time()-st,txt))
c("browser_execute_js",{"code":"1+1","max_ms":6000},12,"A) docs页 execute_js")
c("browser_navigate",{"url":"https://example.com/?ab=1","wait_for_load":True,"max_ms":20000},30,"B) 导航 example.com")
c("browser_execute_js",{"code":"1+1","max_ms":6000},12,"C) 导航后 execute_js")
c("browser_debugger_enable",{"max_ms":15000},25,"D) 导航后 debugger_enable")
c("browser_navigate",{"url":"http://127.0.0.1:9222/docs/","wait_for_load":True,"max_ms":15000},25,"E) 回到 docs 页")
c("browser_execute_js",{"code":"1+1","max_ms":6000},12,"F) docs页 execute_js(再)")
c("browser_status",{},10,"G) status(is_loading?)")
