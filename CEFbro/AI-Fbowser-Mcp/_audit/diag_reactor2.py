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
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n"," ")[:130]
    except Exception as ex: return "EXC:%s"%ex
def arm(tag, rule_event, enable_family, code):
    raw("browser_kernel_reactor",{"action":"clear"})
    r=raw("browser_kernel_reactor",{"action":"add","event":rule_event,"code":code,"cooldown_ms":200})
    if enable_family: raw("browser_collect",{"action":enable_family})
    raw("browser_navigate",{"url":"https://example.com/?arm=%d"%int(time.time()*1000%1000000),"wait_for_load":True},30)
    time.sleep(1.2)
    t=raw("browser_get_title",{})
    print("   %-46s 规则=%s 记录族=%s -> 标题=%s"%(tag,rule_event,enable_family or "未开",t[:40]))
    return "MARK" in t
M1="MARK_WILD_%d"%int(time.time()%10000)
M2="MARK_LOAD_%d"%int(time.time()%10000)
print("== 四臂诊断: 反应器到底走哪条路 ==")
a=arm("A) 通配 * , 不开事件记录族","*",None,"document.title='%s'"%M1)
b=arm("B) load_end , 开 event_load 记录族","load_end","event_load_enable","document.title='%s'"%M2)
print()
print("   结论: A 触发=%s  B 触发=%s"%(a,b))
print("   A触发 -> 记录监控事件这条路径是通的, 问题只在事件名字符串")
print("   A不触发 -> 该路径根本没被调用(load_end 走的是别的函数)")
raw("browser_kernel_reactor",{"action":"clear"})
