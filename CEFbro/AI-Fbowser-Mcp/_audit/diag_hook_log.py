import json,urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
B="http://127.0.0.1:9222"
def call(n,a,t=40):
    r=urllib.request.Request(B+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}},ensure_ascii=False).encode(),headers={"Content-Type":"application/json"})
    d=json.loads(urllib.request.urlopen(r,timeout=t).read().decode())
    rr=d.get("result") or {}
    return bool(rr.get("isError")),"".join(i.get("text") or "" for i in (rr.get("content") or []))
def js(c):
    e,t=call("browser_execute_js",{"code":c})
    if e: return "ERR:"+t
    try:
        j=json.loads(t)
        if isinstance(j,dict): return str(j.get("message"))
    except Exception: pass
    return t.strip().strip('"')
print("A) 被测函数是否真的挂上了 __mcp_hooked 标记:")
print("   typeof mcpHookFnA231723 =", js("typeof window.mcpHookFnA231723"))
print("   .__mcp_hooked =", js("String(window.mcpHookFnA231723 && window.mcpHookFnA231723.__mcp_hooked)"))
print("B) 页面里 __MCP_HOOK_LOG__ 的实际内容:")
print("   len =", js("String((window.__MCP_HOOK_LOG__||[]).length)"))
print("   json =", js("JSON.stringify(window.__MCP_HOOK_LOG__||'undefined')")[:400])
print("C) 其它日志键是否存在:")
for k in ["__MCP_EVAL_LOG__","__MCP_WS_LOG__","__MCP_COOKIE_LOG__"]:
    print("   %-22s len=%s"%(k,js("String((window.%s||[]).length)"%k)))
print("D) 同名无后缀函数(旧实例遗留)是否存在:")
print("   typeof mcpHookFnA =", js("typeof window.mcpHookFnA"))
