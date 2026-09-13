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
        txt="".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:200]
    except Exception as ex: txt="EXC:%s"%ex
    print("   %-40s %6.2fs %s"%(tag or n,time.time()-st,txt))
print("== 多浏览器 browser_id 是否对所有工具生效 ==")
c("browser_list",{},15,"1) 列出现有浏览器")
c("browser_navigate",{"url":"https://example.com/?b1=1","wait_for_load":True},30,"2) 浏览器1 导航")
c("browser_create",{},20,"3) 创建第二个浏览器")
c("browser_list",{},15,"4) 再次列出(看ID)")
c("browser_navigate",{"url":"https://example.com/?b2=1","wait_for_load":True,"browser_id":2},30,"5) 用 browser_id=2 导航")
c("browser_get_url",{"browser_id":2},15,"6) browser_id=2 的URL")
c("browser_get_url",{"browser_id":1},15,"7) browser_id=1 的URL(应为b1)")
c("browser_get_url",{},15,"8) 不带 browser_id(默认)")
