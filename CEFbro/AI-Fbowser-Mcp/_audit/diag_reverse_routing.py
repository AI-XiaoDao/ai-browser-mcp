# -*- coding: utf-8 -*-
import json, time, urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
BASE="http://127.0.0.1:9222"
def raw(name,args):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
                     "params":{"name":name,"arguments":args}},ensure_ascii=False).encode()
    req=urllib.request.Request(BASE+"/mcp",data=body,
        headers={"Content-Type":"application/json"})
    t0=time.time()
    try:
        with urllib.request.urlopen(req,timeout=40) as r:
            txt=r.read().decode("utf-8")
    except Exception as ex:
        return "EXC:%s"%ex, time.time()-t0
    return txt, time.time()-t0

print("=== 只敢在干净实例上测; 先确认服务在 ===")
try:
    h=json.loads(urllib.request.urlopen(BASE+"/health",timeout=5).read())
    print("  tools=%s" % h.get("tool_count"))
except Exception as ex:
    print("  !! 服务未就绪: %s" % ex); raise SystemExit(2)

# 只在 Core 有分支 -> 路由到 Reverse 后应无匹配
CASES = [
  ("browser_reverse_hook",        {"type":"function_call","target":"window.fetch"}),
  ("browser_reverse_instrument",  {"targets":"[\"window.fetch\"]"}),
  ("browser_reverse_extract",     {}),
  ("browser_reverse_strings",     {}),
  ("browser_reverse_env",         {}),
]
print("\n=== 只在 Core 有分支的 5 个工具(预期: 空响应/异常) ===")
for name,args in CASES:
    t,dt = raw(name,args)
    print("  %-30s %5.1fs  原始响应=%r" % (name, dt, t[:150]))

print("\n=== 对照: 在 Reverse 里有分支的工具(预期正常) ===")
for name,args in (("browser_reverse_hook_logs",{"action":"query"}),
                  ("browser_reverse_hook_multi",{"functions":"[\"window.fetch\"]"}),
                  ("browser_reverse_stack_trace",{})):
    t,dt = raw(name,args)
    print("  %-30s %5.1fs  原始响应=%r" % (name, dt, t[:150]))
    time.sleep(0.3)
