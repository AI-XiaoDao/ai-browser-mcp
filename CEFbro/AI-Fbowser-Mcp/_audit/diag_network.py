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
    print("   %-36s %s"%(tag or n,txt[:200])); return txt
print("== 网络抓包是否真的抓到请求(Network域) ==")
raw("browser_collect",{"action":"network_enable"},20,"1) 开启网络记录")
raw("browser_collect",{"action":"clear"},15,"2) 清空旧日志")
raw("browser_navigate",{"url":"https://example.com/?net=%d"%int(time.time()),"wait_for_load":True},30,"3) 导航(全新URL)")
time.sleep(0.8)
t=raw("browser_network",{"action":"list"},20,"4) 网络日志 list")
print("   >>> 抓到的条目数(粗判):", t.count('"url"'))
print()
print("== 对照: 若为空, 看是否因 Network 域未启用 ==")
raw("browser_network",{"action":"enable"},20,"5) browser_network enable")
raw("browser_collect",{"action":"clear"},15,"6) 再清空")
raw("browser_navigate",{"url":"https://example.com/?net2=%d"%int(time.time()),"wait_for_load":True},30,"7) 再导航")
time.sleep(0.8)
t2=raw("browser_network",{"action":"list"},20,"8) 网络日志 list(续)")
print("   >>> 抓到的条目数(粗判):", t2.count('"url"'))
