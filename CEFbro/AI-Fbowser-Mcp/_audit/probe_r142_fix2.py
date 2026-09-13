# -*- coding: utf-8 -*-
r"""R142 探针2: 干净实例(全程不碰类库), 只走我方 CDP 通道:
  ① performSearch → searchId?
  ② getSearchResults → nodeIds?
  ③ discardSearch → ok?
  ④ DOM.enable → 健康? get_document x2 nodeId 稳定?
  ⑤ 稳定 id 下 removeAttribute → 页面侧回读
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
    print('  [%s] %-44s %.2fs err=%s txt=%s' % ('PASS' if ok else 'FAIL', tag, d, e, t[:40]))
    return ok


def inner_payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return None
    for _ in range(4):
        if isinstance(o, dict):
            if "searchId" in o or "nodeIds" in o or "root" in o:
                return o
            nxt = o.get("data") or o.get("result") or o.get("message")
            if isinstance(nxt, str):
                try:
                    nxt = json.loads(nxt)
                except Exception:
                    return None
            o = nxt
        else:
            return None
    return o if isinstance(o, dict) else None


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r142fix2=%d" % int(time.time())})
js("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');document.body.appendChild(d);'ok'")

print('== 0 基线 ==')
health('0 execute_js 基线')

print('== 1 我方通道 performSearch ==')
e, t, d = call("browser_cdp_call", {"method": "DOM.performSearch", "params": json.dumps({"query": "data-x"})})
p = inner_payload(t)
print('  1 performSearch %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:100]))
sid = ""
if not e and p:
    sid = str(p.get("searchId") or "")
print('  1 searchId=%s' % sid)
health('1 之后 execute_js')

print('== 2 我方通道 getSearchResults ==')
if sid:
    e, t, d = call("browser_cdp_call", {"method": "DOM.getSearchResults",
                                        "params": json.dumps({"searchId": sid, "fromIndex": 0, "toIndex": 10})})
    p = inner_payload(t)
    print('  2 getSearchResults %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:100]))
    health('2 之后 execute_js')

print('== 3 我方通道 discardSearch ==')
if sid:
    e, t, d = call("browser_cdp_call", {"method": "DOM.discardSearch", "params": json.dumps({"searchId": sid})})
    print('  3 discardSearch %.2fs err=%s txt=%s' % (d, e, t[:100]))
    health('3 之后 execute_js')

print('== 4 我方通道 DOM.enable + nodeId 稳定性 ==')
e, t, d = call("browser_cdp_call", {"method": "DOM.enable", "params": json.dumps({"includeWhitespace": "none"})})
print('  4 enable %.2fs err=%s txt=%s' % (d, e, t[:80]))
health('4 enable 之后 execute_js')
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
    print('  4 get_document#%d %.2fs err=%s nodeId(p1)=%s' % (i, d, e, nid))
    if nid is not None:
        ids.append(nid)
print('  4 两次 nodeId: %s %s' % (ids, '稳定' if len(ids) == 2 and ids[0] == ids[1] else '不稳定'))
health('4 两次枚举后 execute_js')

print('== 5 稳定 id 下 removeAttribute ==')
if len(ids) == 2 and ids[0] == ids[1]:
    e, t, d = call("browser_cdp_call", {"method": "DOM.removeAttribute",
                                        "params": json.dumps({"nodeId": ids[0], "name": "data-x"})})
    print('  5 removeAttribute %.2fs err=%s txt=%s' % (d, e, t[:80]))
    health('5 之后 execute_js')
    e2, t2, d2 = js("String(document.getElementById('p1').getAttribute('data-x'))")
    print('  5 页面侧回读 data-x: %s (期望 null) err=%s %.2fs' % (t2[:40], e2, d2))

print('== 收尾 ==')
health('收尾 execute_js')
e, t, d = call("browser_status", {})
print('  status err=%s %.2fs' % (e, d))
print('DONE')
