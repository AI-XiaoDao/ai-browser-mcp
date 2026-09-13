import json,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
h=json.loads(urllib.request.urlopen(B+"/health",timeout=8).read())
print("健康: tools=%s cdp_ready=%s latency_max=%s"%(h.get("tool_count"),h.get("cdp_ready"),h.get("latency_max_ms")))
r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/list"}).encode(),headers={"Content-Type":"application/json"})
tools=[t["name"] for t in json.loads(urllib.request.urlopen(r,timeout=20).read().decode())["result"]["tools"]]
print("tools/list 数量 =",len(tools))
new=[t for t in tools if t.startswith("browser_reverse_") and t.replace("browser_reverse_","") in
     ("instrument_script","blackbox","async_stack","breakpoints_active","skip_pauses","precise_coverage",
      "pause_on_exceptions","patch","return_value","set_variable","search_script")]
print("本轮新增工具全部在清单中 =",len(new),"个:")
for t in sorted(new): print("   ",t)
def c(n,a,t=20):
    rq=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(rq,timeout=t).read().decode())
    return "".join(i.get("text") or "" for i in (d.get("result") or {}).get("content") or []).replace("\n"," ")[:90]
print("页面可正常执行JS:",c("browser_execute_js",{"code":"'clean-'+ (1+1)"}))
print("Hook日志工具可用  :",c("browser_reverse_hook_logs",{"action":"query"}))
