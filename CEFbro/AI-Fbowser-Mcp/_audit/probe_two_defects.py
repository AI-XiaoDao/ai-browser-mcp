import json,time,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def c(n,a,t=45,tag=""):
    st=time.time()
    try:
        r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
        d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
        rr=d.get("result") or {}
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:150]
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-34s %6.2fs %s"%(tag or n,time.time()-st,txt))
c("browser_navigate",{"url":"https://example.com/?p=1","wait_for_load":True},30,"navigate(基线)")
c("browser_get_text",{},40,"get_text 全文")
c("browser_get_text",{},40,"get_text 全文(第2次)")
c("browser_get_text",{"selector":"h1"},20,"get_text 指定元素")
c("browser_execute_js",{"code":"document.body.innerText.length"},15,"execute_js(对照)")
c("browser_mouse_click",{"x":10,"y":10},25,"mouse_click(默认)")
c("browser_mouse_move",{"x":20,"y":20},25,"mouse_move(默认)")
