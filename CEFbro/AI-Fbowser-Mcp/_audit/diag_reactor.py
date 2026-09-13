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
    print("   %-38s %s"%(tag or n,txt[:160])); return txt
MARK="MCP_REACTOR_OK_%d"%int(time.time()%100000)
print("== 反应器: 效果能否被观测到 ==")
raw("browser_kernel_reactor",{"action":"add","event":"load_end","code":"document.title='%s'"%MARK},20,"1) 注册规则(load_end 时改标题)")
raw("browser_navigate",{"url":"https://example.com/?rx=%d"%int(time.time()),"wait_for_load":True},30,"2) 导航触发 load_end")
time.sleep(1.5)
t=raw("browser_get_title",{},15,"3) 标题是否被改成标记")
print("   >>> 反应器生效 =", MARK in t)
raw("browser_kernel_reactor",{"action":"clear"},15,"4) 清场")
print()
print("== 定时监视: 结果是否有读取途径 ==")
raw("browser_kernel_watch",{"action":"start","expression":"document.title","key":"probe"},20,"5) 启动监视")
time.sleep(1.2)
for act in ["list","get","query"]:
    raw("browser_kernel_watch",{"action":act},15,"6) 尝试读取 action=%s"%act)
raw("browser_kernel_watch",{"action":"clear"},15,"7) 清场")
