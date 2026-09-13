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
    print("   %-52s %s"%(tag or n,txt[:150])); return txt
print("== 决定清单去留的两个真机测试 ==")
print("A) 触摸触发: 类库 高级_设置触发鼠标触摸事件 对应 CDP Emulation.setEmitTouchEventsForMouse")
raw("browser_cdp_call",{"method":"Emulation.setEmitTouchEventsForMouse","params":json.dumps({"enabled":True,"configuration":"mobile"})},20,"   setEmitTouchEventsForMouse(mobile)")
raw("browser_execute_js",{"code":"String(navigator.maxTouchPoints)+'/'+String('ontouchstart' in window)"},15,"   页面触摸能力(navigator.maxTouchPoints)")
raw("browser_cdp_call",{"method":"Emulation.setEmitTouchEventsForMouse","params":json.dumps({"enabled":False})},20,"   还原(enabled=false)")
print()
print("B) 细粒度存储清理: CDP Storage.clearDataForOrigin 是否可用")
raw("browser_cdp_call",{"method":"Storage.clearDataForOrigin","params":json.dumps({"origin":"https://example.com","storageTypes":"local_storage"})},20,"   clearDataForOrigin(local_storage)")
print()
print("C) 本轮已实测: 反应器是否真的触发")
raw("browser_get_title",{},15,"   当前标题(反应器规则已清)")
