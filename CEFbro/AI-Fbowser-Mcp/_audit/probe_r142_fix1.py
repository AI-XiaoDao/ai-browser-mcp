# -*- coding: utf-8 -*-
r"""R142 修复后探针: 定位毒化源 + 测 CDP 原生替代(search/enable/节点编辑)。

顺序(干净实例, 每步后测 execute_js 时延):
  A 基线 fast
  B node_edit 路由(不再调用 启用) → fast?
  C search 预查找(类库) → fast?       # 类库 performSearch 是否毒化
  D discard_search(类库) → fast?       # 类库 discardSearchResults 是否毒化
  E 我方通道 CDP DOM.performSearch → 可用? searchId 格式?
  F 我方通道 CDP DOM.discardSearch(用 E 的 id) → 可用?
  G 我方通道 CDP DOM.enable → 之后 get_document x2 的 nodeId 是否稳定? 通道健康?
  H 用稳定 id 走我方通道 DOM.removeAttribute → 页面侧回读
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


def js(code, to=60):
    return call("browser_execute_js", {"code": code}, to=to)


def health(tag):
    e, t, d = js("1+1")
    ok = (not e) and d < 1.0
    print('  [%s] %-46s %.2fs err=%s txt=%s' % ('PASS' if ok else 'FAIL', tag, d, e, t[:60]))
    return ok


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r142fix1=%d" % int(time.time())})
js("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');document.body.appendChild(d);'ok'")

print('== A 基线 ==')
health('A execute_js 基线')

print('== B node_edit 路由(无启用) ==')
e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": 5, "attr_name": "data-x", "confirm": True})
print('  B node_edit %.2fs err=%s txt=%s' % (d, e, t[:80]))
health('B 之后 execute_js')

print('== C search 预查找(类库) ==')
e, t, d = call("browser_vip_dom_search", {"query": "p1"}, to=90)
sid = ""
try:
    sid = json.loads(t).get("searchId") or ""
except Exception:
    pass
print('  C search %.2fs err=%s searchId=%s txt=%s' % (d, e, sid, t[:80]))
health('C 之后 execute_js')

print('== D discard_search(类库) ==')
if sid:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "discard_search", "search_id": sid})
    print('  D discard %.2fs err=%s txt=%s' % (d, e, t[:80]))
    health('D 之后 execute_js')

print('== E 我方通道 CDP performSearch ==')
e, t, d = call("browser_cdp_call", {"method": "DOM.performSearch", "params": json.dumps({"query": "data-x"})})
print('  E performSearch %.2fs err=%s txt=%s' % (d, e, t[:120]))
sid2 = ""
if not e:
    try:
        o = json.loads(t)
        inner = o.get("data") or o
        if isinstance(inner, str):
            inner = json.loads(inner)
        sid2 = str(inner.get("searchId") or "")
    except Exception:
        pass
print('  E 解析出 searchId=%s' % sid2)
health('E 之后 execute_js')

print('== F 我方通道 CDP discardSearch(用 E 的 id) ==')
if sid2:
    e, t, d = call("browser_cdp_call", {"method": "DOM.discardSearch", "params": json.dumps({"searchId": sid2})})
    print('  F discardSearch %.2fs err=%s txt=%s' % (d, e, t[:120]))
    health('F 之后 execute_js')

print('== G 我方通道 CDP DOM.enable 后 nodeId 稳定性 ==')
e, t, d = call("browser_cdp_call", {"method": "DOM.enable", "params": json.dumps({"includeWhitespace": "none"})})
print('  G enable %.2fs err=%s txt=%s' % (d, e, t[:80]))
health('G enable 之后 execute_js')
ids = []
for i in (1, 2):
    e, t, d = call("browser_vip_dom_get_document", {"depth": 4})
    nid = None
    if not e:
        try:
            o = json.loads(t)
            root = o.get("data") or o
            if isinstance(root, str):
                root = json.loads(root)
            root = root.get("root") or root

            def find(n):
                if not isinstance(n, dict):
                    return None
                attrs = (n.get("attributes") or [])
                ad = {attrs[k]: attrs[k + 1] for k in range(0, len(attrs) - 1, 2)} if isinstance(attrs, list) else {}
                if ad.get("id") == "p1":
                    return n
                for k in ("children", "shadowRoots"):
                    for c in (n.get(k) or []):
                        r = find(c)
                        if r:
                            return r
                return None
            n2 = find(root)
            nid = n2.get("nodeId") if n2 else None
        except Exception:
            pass
    print('  G get_document#%d %.2fs err=%s nodeId(p1)=%s' % (i, d, e, nid))
    if nid is not None:
        ids.append(nid)
print('  G 两次 nodeId: %s (相同=稳定)' % ids)
health('G 两次枚举后 execute_js')

print('== H 我方通道 removeAttribute(用稳定 id) ==')
if ids:
    e, t, d = call("browser_cdp_call", {"method": "DOM.removeAttribute",
                                        "params": json.dumps({"nodeId": ids[0], "name": "data-x"})})
    print('  H removeAttribute %.2fs err=%s txt=%s' % (d, e, t[:80]))
    health('H 之后 execute_js')
    e2, t2, d2 = js("String(document.getElementById('p1').getAttribute('data-x'))")
    print('  H 页面侧回读 data-x: %s (期望 null) err=%s %.2fs' % (t2[:40], e2, d2))

print('== 收尾 ==')
health('收尾 execute_js')
call("browser_status", {})
print('DONE')
