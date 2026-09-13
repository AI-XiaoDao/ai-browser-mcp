import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=30,tag=""):
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-40s %s"%(tag or n,txt[:170])); return txt
print("A) 导航到一个全新URL(避免同URL空操作):")
raw("browser_navigate",{"url":"https://example.com/?probe=%d"%int(time.time()),"wait_for_load":True},30,"navigate(全新URL)")
time.sleep(0.6)
print("B) Network 事件是否真的到达服务端(不启用域的话不会到达):")
raw("browser_cdp_event",{"event_name":"Network.requestWillBeSent"},15,"cdp_event Network.requestWillBeSent")
print("C) 对照: 一个不需要 enable 的事件是否到达:")
raw("browser_cdp_event",{"event_name":"Page.frameNavigated"},15,"cdp_event Page.frameNavigated")
print("D) 若B为空, 手工 Network.enable 再看:")
raw("browser_cdp_call",{"method":"Network.enable","params":"{}"},20,"Network.enable")
raw("browser_navigate",{"url":"https://example.com/?probe2=%d"%int(time.time()),"wait_for_load":True},30,"navigate(再)")
time.sleep(0.6)
raw("browser_cdp_event",{"event_name":"Network.requestWillBeSent"},15,"cdp_event Network.requestWillBeSent(续)")
