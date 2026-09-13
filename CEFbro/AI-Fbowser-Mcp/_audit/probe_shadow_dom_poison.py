# -*- coding: utf-8 -*-
r"""最后一个判别: 阴影根(shadow root)是否就是"用一次 DOM 编辑后通道死掉"的触发条件?

verify_round142b 与已验证健康的裸序列只差两点: ①注入了 shadow root ②用了 DOM.removeAttribute(工具路径)。
本探针按**最小序列**逐步走, 每步之后量 execute_js:
  baseline → 注入(带 shadow root 的 div) → get_document → remove_attr → get_document → execute_js

用法: py -3 _audit\probe_shadow_dom_poison.py
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


def health(tag):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    print('   %-24s execute_js %.2fs %s' % (tag, d, 'OK' if d < 1 else '慢/坏'))
    return d


def node_of(txt, want_id):
    try:
        o = json.loads(txt)
    except Exception:
        return 0
    for _ in range(4):
        if isinstance(o, dict) and "root" in o:
            o = o["root"]
            break
        o = o.get("data") if isinstance(o, dict) else None
        if isinstance(o, str):
            o = json.loads(o)
    def find(n):
        if not isinstance(n, dict):
            return None
        a = n.get("attributes") or []
        at = {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}
        if at.get("id") == want_id:
            return n
        for k in ("children", "shadowRoots"):
            for c in (n.get(k) or []):
                r = find(c)
                if r:
                    return r
        return None
    n = find(o)
    return n.get("nodeId") if n else 0


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?sp=%d" % int(time.time())})
health('基线')

call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');"
    "d.innerHTML='<span id=inner>x</span>';document.body.appendChild(d);"
    "var h=document.createElement('div');h.id='host1';"
    "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=sh>S</span>';document.body.appendChild(h);'ok'"})
health('注入(含 shadow root)后')

e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=60)
nid = node_of(t, 'p1')
print('   get_document#1 %.2fs nodeId(p1)=%s' % (d, nid))
health('get_document#1 后')

if nid:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": nid, "attr_name": "data-x", "confirm": True}, to=60)
    print('   remove_attr %.2fs isError=%s %s' % (d, e, t[:70]))
    health('remove_attr 后')

    e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=60)
    print('   get_document#2 %.2fs isError=%s len=%d' % (d, e, len(t)))
    health('get_document#2 后')

    print('   对照: 页面侧断言 data-x 是否已消失')
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-x'))"})
    print('      getAttribute -> %s' % t2[:60])
