import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=25,cut=700):
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:cut]
    except Exception as ex: return "EXC:%s"%ex
raw("browser_network",{"action":"clear"},20,60)
print("1) 开启网络详细:", raw("browser_network",{"action":"detail_enable"},20,140))
raw("browser_navigate",{"url":"https://example.com/?nd=%d"%int(time.time()),"wait_for_load":True},30,60)
time.sleep(0.8)
print("2) list:", raw("browser_network",{"action":"list"},20,500))
print("3) get :", raw("browser_network",{"action":"get"},20,500))
print("4) 用 event_type 查 network(看是否含详细信息):", raw("browser_event",{"event_type":"resource_response","limit":5},20,400))
