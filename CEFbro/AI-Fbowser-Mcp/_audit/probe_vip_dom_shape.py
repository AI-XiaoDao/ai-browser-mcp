# -*- coding: utf-8 -*-
r"""探针: `browser_vip_dom_get_document` 的枚举结果**长什么样**(节点ID/属性/结构), 以便设计 node_edit 的验收。
同时记录 `browser_vip_dom_search` 的预查结果形态。

用法: py -3 _audit\probe_vip_dom_shape.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?dom=%d" % int(time.time())})
call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.id='mcpProbeDiv';d.className='probe-cls';"
    "d.setAttribute('data-probe','yes');d.innerHTML='<span id=mcpProbeSpan>标记文本</span>';"
    "document.body.appendChild(d);"
    "var h=document.createElement('div');h.id='mcpShadowHost';"
    "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shadowInner>ShadowSentinel</span>';"
    "document.body.appendChild(h);'ok'"})

print('== 枚举 DOM(depth=4) ==')
e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=90)
print('   isError=%s %.2fs len=%d' % (e, d, len(t)))
if not e:
    # 结果可能是 _async 回执 → 需要 mcp_result
    p = {}
    try:
        p = json.loads(t)
    except Exception:
        pass
    tid = (p.get("task_id") or (p.get("data") or {}).get("task_id")) if isinstance(p, dict) else None
    if tid:
        e2, t2, _ = call("mcp_result", {"request_id": tid}, to=60)
        print('   mcp_result isError=%s len=%d' % (e2, len(t2)))
        print('   内容前 1200 字符:\n%s' % t2[:1200])
        t = t2
    else:
        print('   直接内容前 1200 字符:\n%s' % t[:1200])

print('\n== 预查找文本(ShadowSentinel) ==')
e, t, d = call("browser_vip_dom_search", {"query": "ShadowSentinel"}, to=90)
print('   isError=%s %.2fs len=%d' % (e, d, len(t)))
try:
    p = json.loads(t)
    tid = p.get("task_id") or (p.get("data") or {}).get("task_id")
    if tid:
        e2, t2, _ = call("mcp_result", {"request_id": tid}, to=60)
        print('   mcp_result: %s' % t2[:600])
    else:
        print('   %s' % t[:600])
except Exception:
    print('   %s' % t[:600])
