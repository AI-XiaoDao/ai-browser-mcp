# -*- coding: utf-8 -*-
"""验证 hook 对原生内置函数(fetch/XHR)是否可用 —— 实战最常见的 Hook 目标。
覆盖: browser_reverse_hook_multi(["window.fetch"]) / type=function_call(fetch) /
      type=xhr_fetch(真实发起一次 fetch, 看是否抓到请求与响应)
"""
import json
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
RUN = str(int(time.time()))[-6:]
res = []


def call(n, a, t=40):
    try:
        r = urllib.request.Request(BASE + "/mcp",
                                   data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                    "params": {"name": n, "arguments": a}},
                                                   ensure_ascii=False).encode(),
                                   headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=t).read().decode())
    except Exception as ex:
        return True, "EXC:%s" % ex
    rr = d.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or "" for i in (rr.get("content") or []))


def js(c):
    e, t = call("browser_execute_js", {"code": c})
    if e:
        return "ERR:" + t
    try:
        j = json.loads(t)
        if isinstance(j, dict):
            return str(j.get("message"))
    except Exception:
        pass
    return t.strip().strip('"')


def rec(tag, ok, d=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(d)[:100]))


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s latency_max=%s" % (h.get("tool_count"), h.get("cdp_ready"),
                                                h.get("latency_max_ms")))
except Exception as ex:
    print("  !! 服务未就绪 %s" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?fh=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.5)
js("window.__MCP_HOOK_LOG__=[];'ok'")

print("\n== 1) browser_reverse_hook_multi 挂原生 window.fetch ==")
e1, t1 = call("browser_reverse_hook_multi", {"functions": json.dumps(["window.fetch"])}, 40)
print("     回复: %s" % t1.replace("\n", " ")[:200])
rec("hook_multi(window.fetch) 有明确结果", not t1.startswith("EXC:"), "")
rec("  且未返回 Hook错误", "Hook错误" not in t1, t1.replace("\n", " ")[:90])

print("\n== 2) browser_reverse_hook function_call 挂 window.fetch ==")
e2, t2 = call("browser_reverse_hook", {"type": "function_call", "target": "window.fetch"}, 40)
print("     回复: %s" % t2.replace("\n", " ")[:200])
rec("hook(fetch) 未报错", "Hook错误" not in t2, t2.replace("\n", " ")[:90])
time.sleep(0.8)
print("   fetch 是否被包装: __mcp_hooked=%s" % js("String(window.fetch && window.fetch.__mcp_hooked)"))
rec("window.fetch 被成功包装", js("String(window.fetch && window.fetch.__mcp_hooked)") == "true", "")

print("\n== 3) fetch 被 Hook 后仍能正常请求(语义不变) ==")
r = js("fetch('https://example.com/?probe=%s').then(function(r){return r.status})" % RUN)
time.sleep(1.2)
print("   fetch 返回:", r)
rec("fetch 仍可用", r not in ("ERR", "undefined", "null") and "ERR" not in r, r)

print("\n== 4) xhr_fetch 型 Hook 是否抓到真实请求 ==")
js("window.__MCP_HOOK_LOG__=[];'ok'")
e4, t4 = call("browser_reverse_hook", {"type": "xhr_fetch", "target": "example.com"}, 40)
print("     回复: %s" % t4.replace("\n", " ")[:200])
rec("hook(xhr_fetch) 未报错", "Hook错误" not in t4, t4.replace("\n", " ")[:90])
time.sleep(0.8)
js("fetch('https://example.com/?cap=%s').then(function(r){return r.status})" % RUN)
time.sleep(1.5)
blob = js("JSON.stringify(window.__MCP_HOOK_LOG__||'undef')")
print("   日志: %s" % blob[:300])
rec("xhr_fetch 抓到了本次请求",
    ("example.com" in blob) and ("cap=%s" % RUN in blob or "url" in blob), blob[:110])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
