import json, time, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
BASE="http://127.0.0.1:9222"
def call(name,args,timeout=40):
    t0=time.time()
    req=urllib.request.Request(BASE+"/mcp",
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
                         "params":{"name":name,"arguments":args}},ensure_ascii=False).encode(),
        headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            resp=json.loads(r.read().decode())
    except Exception as ex:
        return True,"EXC:%s"%ex,time.time()-t0
    rr=resp.get("result") or {}
    txt="".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type")=="text")
    return bool(rr.get("isError")), txt, time.time()-t0

h=json.loads(urllib.request.urlopen(BASE+"/health",timeout=8).read())
print("health: cdp=%s active=%s async=%s db=%s latency_max=%s" % (
    h.get("cdp_ready"), h.get("active_requests"), h.get("async_tasks"),
    h.get("db_async_results"), h.get("latency_max_ms")))
print()
for name,args in (("browser_get_url",{}),
                  ("browser_execute_js",{"code":"1+1"}),
                  ("browser_dom_query",{"selector":"h1"}),
                  ("browser_get_text",{"selector":"h1"})):
    e,t,dt = call(name,args,40)
    print("  %-22s %6.1fs err=%-5s %s" % (name, dt, e, t.replace(chr(10)," ")[:80]))
    time.sleep(0.3)
