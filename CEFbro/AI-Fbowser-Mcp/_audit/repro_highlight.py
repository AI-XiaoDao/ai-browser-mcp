import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a,t=20):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        return time.time()-st, "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:90]
    except Exception as ex: return time.time()-st,"EXC:%s"%ex
c("browser_navigate",{"url":"https://example.com/?hl=%d"%int(time.time()),"wait_for_load":True})
ok=0
for i in range(5):
    c("browser_highlight",{"selector":"h1","color":"#ff3344","duration_ms":3000})
    el,txt=c("browser_highlight",{"selector":"h1","duration_ms":0})
    good = "超时" not in txt and "EXC" not in txt
    ok += 1 if good else 0
    print("   第%d次 clear: %5.2fs %s   %s"%(i+1,el,"OK" if good else "★超时",txt[:70]))
print("   成功 %d/5"%ok)
