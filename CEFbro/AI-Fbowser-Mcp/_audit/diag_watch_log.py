import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=25,cut=1200):
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:cut]
    except Exception as ex: return "EXC:%s"%ex
raw("browser_navigate",{"url":"https://example.com/?wl=%d"%int(time.time()),"wait_for_load":True},30,60)
raw("browser_kernel_watch",{"action":"clear"},20,60)
raw("browser_kernel_watch",{"action":"start","expression":"String(Date.now())","key":"ts","interval_ms":500},20,80)
time.sleep(4.0)
print("A) browser_event 按 event=watch_changed 查:", raw("browser_event",{"event":"watch_changed"},25))
print("B) browser_event 不带参(时间线)      :", raw("browser_event",{},25,900))
raw("browser_kernel_watch",{"action":"clear"},20,60)
