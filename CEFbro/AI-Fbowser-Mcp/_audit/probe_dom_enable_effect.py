# -*- coding: utf-8 -*-
r"""诊断(第142轮): ①`browser_vip_dom_get_document` 现在到底回什么(解析失败导致 nodeId 取不到)?
②`开发者DOM.启用("all")` 是否会把**我们的 CDP 命令通道**弄坏(上一轮验收末尾 execute_js 30s)?

用法: py -3 _audit\probe_dom_enable_effect.py
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


def call(n, a=None, to=90):
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
call("browser_navigate", {"url": "https://example.com/?de=%d" % int(time.time())})
call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.id='mcpProbeDiv';d.setAttribute('data-probe','yes');"
    "document.body.appendChild(d);'ok'"})
e, t, d = call("browser_execute_js", {"code": "1+1"})
print('①基线 execute_js: isError=%s %.2fs %s' % (e, d, t[:40]))

print('\n② 枚举 DOM 的**原始回包**(前 700 字符):')
e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=90)
print('   isError=%s %.2fs len=%d' % (e, d, len(t)))
print('   %s' % t[:700])
try:
    o = json.loads(t)
    print('   顶层键: %s' % sorted(o)[:8])
    if "root" in o:
        def cnt(n):
            return 1 + sum(cnt(c) for c in (n.get("children") or []))
        print('   节点总数=%d' % cnt(o["root"]))
except Exception as ex:
    print('   JSON 解析失败: %r' % (ex,))

print('\n③ 枚举之后 execute_js(看 CDP 通道是否被打坏):')
e, t, d = call("browser_execute_js", {"code": "2+2"}, to=60)
print('   isError=%s %.2fs %s' % (e, d, t[:60]))

print('\n④ 再用一次枚举(pierce=true) 后 execute_js:')
e, t, d = call("browser_vip_dom_get_document", {"depth": 4, "pierce": True}, to=90)
print('   枚举 isError=%s %.2fs len=%d' % (e, d, len(t)))
e, t, d = call("browser_execute_js", {"code": "3+3"}, to=60)
print('   isError=%s %.2fs %s' % (e, d, t[:60]))

print('\n⑤ 节点编辑(remove_attr)之后 execute_js:')
try:
    o = json.loads(t) if False else None
except Exception:
    pass
e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": 999, "attr_name": "data-probe", "confirm": True}, to=60)
print('   node_edit isError=%s %.2fs %s' % (e, d, t[:80]))
e, t, d = call("browser_execute_js", {"code": "4+4"}, to=60)
print('   isError=%s %.2fs %s' % (e, d, t[:60]))
e, t, d = call("browser_status", {}, to=30)
print('   browser_status isError=%s %.2fs' % (e, d))
