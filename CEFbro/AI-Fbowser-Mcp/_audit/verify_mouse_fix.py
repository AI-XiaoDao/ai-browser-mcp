import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a,t=30,tag=""):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:150]
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-26s %6.2fs %s"%(tag or n,time.time()-st,txt))
c("browser_navigate",{"url":"https://example.com/?m=1","wait_for_load":True},30,"navigate")
c("browser_mouse_click",{"x":10,"y":10},20,"mouse_click")
c("browser_mouse_move",{"x":20,"y":20},20,"mouse_move")
c("browser_mouse_wheel",{"x":20,"y":20,"delta_y":100},20,"mouse_wheel")
print("   -- 关键: 鼠标操作后 CDP 通道是否仍可用 --")
c("browser_execute_js",{"code":"1+1","max_ms":5000},12,"execute_js 之后")
c("browser_get_text",{},20,"get_text 之后")
