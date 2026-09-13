import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=25,cut=1500):
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:cut]
    except Exception as ex: return "EXC:%s"%ex
raw("browser_navigate",{"url":"https://example.com/?we=%d"%int(time.time()),"wait_for_load":True},30,60)
raw("browser_kernel_watch",{"action":"clear"},20,60)
print("1) start Date.now() ->", raw("browser_kernel_watch",{"action":"start","expression":"String(Date.now())","key":"ts","interval_ms":500},20,120))
time.sleep(4.0)
print("2) event_type=watch_changed ->", raw("browser_event",{"event_type":"watch_changed","limit":50},25))
print("3) 时间线(全部类型, 搜 watch_changed) ->", ("watch_changed" in raw("browser_event",{"limit":300},25,9000)))
raw("browser_kernel_watch",{"action":"clear"},20,60)
