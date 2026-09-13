import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=12):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    except Exception as ex:
        return "EXC:%s"%ex, time.time()-st
    rr=d.get("result") or {}
    return ("isError=%s "%rr.get("isError"))+"".join(i.get("text") or "" for i in (rr.get("content") or [])), time.time()-st
for name,args in [("browser_reverse_blackbox",{"patterns":["test"]}),
                  ("browser_reverse_skip_pauses",{}),
                  ("browser_reverse_search_script",{"query":"a"}),
                  ("browser_reverse_precise_coverage",{"action":"start"})]:
    txt,el=raw(name,args)
    print("%-34s %.1fs  %s"%(name.replace("browser_reverse_",""),el,str(txt)[:170].replace("\n"," ")))
print("\n-- 调用后健康检查(确认没把服务器搞挂) --")
h=json.loads(urllib.request.urlopen(B+"/health",timeout=8).read())
print("cdp_ready=%s latency_max=%s tools=%s"%(h.get("cdp_ready"),h.get("latency_max_ms"),h.get("tool_count")))
