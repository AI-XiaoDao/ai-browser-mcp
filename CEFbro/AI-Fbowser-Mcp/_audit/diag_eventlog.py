import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=30):
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:200]
    except Exception as ex: return "EXC:%s"%ex
print("1) 开资源事件族 :",raw("browser_collect",{"action":"event_resource_enable"}))
raw("browser_collect",{"action":"clear"})
print("2) 导航         :",raw("browser_navigate",{"url":"https://example.com/?lg=%d"%int(time.time()),"wait_for_load":True},30))
time.sleep(1.2)
print("3) 事件日志 resource_response :",raw("browser_event",{"event":"resource_response"},20))
print("4) 事件日志 resource_request  :",raw("browser_event",{"event":"resource_request"},20))
print("5) 事件时间线(全部)           :",raw("browser_event",{},20)[:240])
