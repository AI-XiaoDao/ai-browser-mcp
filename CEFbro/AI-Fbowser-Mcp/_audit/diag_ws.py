import json, sys, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
def call(name,args,timeout=30):
    req=urllib.request.Request("http://127.0.0.1:9222/mcp",
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
                         "params":{"name":name,"arguments":args}},ensure_ascii=False).encode(),
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        resp=json.loads(r.read().decode())
    rr=resp.get("result") or {}
    txt="".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type")=="text")
    return bool(rr.get("isError")), txt

print("=== browser_vip_websocket_intercept 三种输入 ===")
for label,args in (("空 {} (未传 enable)", {}),
                   ("enable:true (真布尔)", {"enable": True}),
                   ("enable:'true' (字符串, 测类型容错)", {"enable": "true"}),
                   ("enable:false (显式关)", {"enable": False})):
    e,t = call("browser_vip_websocket_intercept", args)
    print("  %-34s err=%-5s %s" % (label, e, t.replace(chr(10)," ")[:104]))
