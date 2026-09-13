import json,subprocess,time,urllib.request,os
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
EXE=r"_int\AI-Fbowser-Mcp\debug\x64\linker\AI-Fbowser-Mcp.exe"
B="http://127.0.0.1:9222"
subprocess.run(["taskkill","/F","/IM","AI-Fbowser-Mcp.exe"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE],cwd=os.path.dirname(EXE),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for i in range(60):
    time.sleep(1)
    try:
        h=json.loads(urllib.request.urlopen(B+"/health",timeout=3).read())
        if h.get("tool_count"): break
    except Exception: pass
time.sleep(2.5)
def c(n,a,t=40,tag=""):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:130]
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-30s %6.2fs %s"%(tag or n,time.time()-st,txt))
print("-- 干净实例基线 --")
c("browser_navigate",{"url":"https://example.com/?gt=1","wait_for_load":True},30,"navigate")
c("browser_execute_js",{"code":"1+1","max_ms":5000},12,"execute_js 基线")
print("-- 触发: 全文取文本 --")
c("browser_get_text",{},35,"get_text 全文(1)")
print("-- 之后: 通道是否还活着 --")
c("browser_execute_js",{"code":"1+1","max_ms":5000},12,"execute_js 之后")
c("browser_dom_query",{"selector":"h1"},15,"dom_query 之后")
c("browser_execute_js",{"code":"2+2","max_ms":5000},12,"execute_js 再试")
