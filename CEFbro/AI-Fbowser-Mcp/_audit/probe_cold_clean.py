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
time.sleep(3)
def c(n,a,t=40,tag=""):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:120]
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-30s %5.1fs %s"%(tag,time.time()-st,txt))
h=json.loads(urllib.request.urlopen(B+"/health",timeout=8).read())
print("全新实例: tools=%s cdp_ready=%s"%(h.get("tool_count"),h.get("cdp_ready")))
print("-- 冷启动（停在程序自带页）立即测 --")
c("browser_get_url",{},10,"get_url")
c("browser_status",{},10,"status")
c("browser_execute_js",{"code":"1+1","max_ms":6000},12,"execute_js")
c("browser_debugger_enable",{"max_ms":12000},20,"debugger_enable")
print("-- 导航到真实页面后再测 --")
c("browser_navigate",{"url":"https://example.com/?clean=1","wait_for_load":True,"max_ms":20000},30,"navigate")
c("browser_execute_js",{"code":"1+1","max_ms":6000},12,"execute_js")
c("browser_debugger_enable",{"max_ms":12000},20,"debugger_enable")
c("browser_reverse_search_script",{"action":"list"},25,"search_script list")
