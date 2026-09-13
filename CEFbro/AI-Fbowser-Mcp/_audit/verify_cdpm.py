import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def raw(n,a,t=30,tag=""):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-34s %5.2fs %s"%(tag or n,time.time()-st,txt[:190]))
    return txt
print("== CDP监控 端到端: 订阅 -> 事件 -> 读取 ==")
raw("browser_kernel_cdp_monitor",{"action":"list"},15,"0) 订阅前 list")
raw("browser_kernel_cdp_monitor",{"action":"add","methods":"Network.*"},15,"1) 订阅 Network.*")
raw("browser_navigate",{"url":"https://example.com/?cm=1","wait_for_load":True},30,"2) 导航(产生Network事件)")
time.sleep(0.8)
t=raw("browser_kernel_cdp_monitor",{"action":"list"},15,"3) 订阅后 list(看 events_json)")
print()
print("   events_json 非空 =", ('"events_json":"[{' in t) or ('"events_json": "[{' in t))
raw("browser_kernel_cdp_monitor",{"action":"disable"},15,"4) 关闭订阅(清场)")
raw("browser_kernel_cdp_monitor",{"action":"clear"},15,"5) 清空规则")
