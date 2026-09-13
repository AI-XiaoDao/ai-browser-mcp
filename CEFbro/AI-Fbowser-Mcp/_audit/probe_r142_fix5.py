# -*- coding: utf-8 -*-
r"""R142 探针5(干净重启): 搜索取值正确范围 + querySelector + 回读形状 + disable。
  ① DOM.disable 存在?
  ② disable 后 performSearch → "not enabled"?
  ③ enable → performSearch → getSearchResults {0, resultCount} → nodeIds
  ④ getDocument(depth=1) → root → DOM.querySelector "#p1" → nodeId
  ⑤ 用 querySelector id setAttributeValue → 回读
  ⑥ getAttributes 形状
  ⑦ removeNode 后 getAttributes → "Could not find node"(即验证节点已删)
  ⑧ getOuterHTML 文本节点形状
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


def js(code, to=60):
    return call("browser_execute_js", {"code": code}, to=to)


def health(tag):
    e, t, d = js("1+1")
    ok = (not e) and d < 1.0
    print('  [%s] %-44s %.2fs err=%s' % ('PASS' if ok else 'FAIL', tag, d, e))
    return ok


def cdp(method, params, to=60):
    return call("browser_cdp_call", {"method": method, "params": json.dumps(params)}, to=to)


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return None
    for _ in range(4):
        if isinstance(o, dict):
            if any(k in o for k in ("searchId", "nodeIds", "nodeId", "attributes", "outerHTML", "root")):
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
call("browser_navigate", {"url": "https://example.com/?r142fix5=%d" % int(time.time())})
js("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');var s=document.createElement('span');s.id='sp';s.textContent='hello';d.appendChild(s);document.body.appendChild(d);'ok'")
health('0 基线')

print('== ① DOM.disable 存在? ==')
e, t, d = cdp("DOM.disable", {})
print('  ① disable %.2fs err=%s txt=%s' % (d, e, t[:80]))

print('== ② disable 后 performSearch ==')
e, t, d = cdp("DOM.performSearch", {"query": "data-x"})
print('  ② performSearch %.2fs err=%s txt=%s' % (d, e, t[:80]))

print('== ③ enable → performSearch → getSearchResults(正确范围) ==')
e, t, d = cdp("DOM.enable", {"includeWhitespace": "none"})
print('  ③a enable %.2fs err=%s' % (d, e))
e, t, d = cdp("DOM.performSearch", {"query": "data-x"})
p = payload(t)
print('  ③b performSearch %.2fs err=%s payload=%s' % (d, e, p))
sid = str(p.get("searchId") or "") if (not e and p) else ""
cnt = int(p.get("resultCount") or 0) if (not e and p) else 0
if sid:
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": cnt})
    p = payload(t)
    print('  ③c getSearchResults(0..%d) %.2fs err=%s payload=%s txt=%s' % (cnt, d, e, p, t[:100]))
    health('③ 之后')

print('== ④ getDocument(depth=1) → querySelector "#p1" ==')
e, t, d = call("browser_vip_dom_get_document", {"depth": 1})
p = payload(t)
root = None
if not e and p:
    root = p.get("root") or {}
print('  ④a getDocument(depth=1) %.2fs err=%s rootKeys=%s' % (d, e, list(root.keys())[:8] if isinstance(root, dict) else None))
rid = root.get("nodeId") if isinstance(root, dict) else None
if rid:
    e, t, d = cdp("DOM.querySelector", {"nodeId": rid, "selector": "#p1"})
    p = payload(t)
    print('  ④b querySelector %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:80]))
    qid = (p or {}).get("nodeId")
    health('④ 之后')
    print('== ⑤ 用 querySelector id 做 setAttributeValue ==')
    if qid:
        e, t, d = cdp("DOM.setAttributeValue", {"nodeId": qid, "name": "data-y", "value": "7"})
        print('  ⑤ setAttributeValue %.2fs err=%s txt=%s' % (d, e, t[:80]))
        health('⑤ 之后')
        e2, t2, d2 = js("String(document.getElementById('p1').getAttribute('data-y'))")
        print('  ⑤ 页面侧回读 data-y=%s (期望 7) %.2fs' % (t2[:40], d2))
        print('== ⑥ getAttributes 形状 ==')
        e, t, d = cdp("DOM.getAttributes", {"nodeId": qid})
        p = payload(t)
        print('  ⑥ getAttributes %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:100]))
        health('⑥ 之后')
        print('== ⑦ removeNode 后 getAttributes ==')
        e, t, d = cdp("DOM.removeNode", {"nodeId": qid})
        print('  ⑦a removeNode %.2fs err=%s txt=%s' % (d, e, t[:80]))
        e, t, d = cdp("DOM.getAttributes", {"nodeId": qid})
        print('  ⑦b getAttributes(已删) %.2fs err=%s txt=%s (期望 Could not find node)' % (d, e, t[:100]))
        health('⑦ 之后')

print('== ⑧ getOuterHTML 文本节点形状 ==')
e, t, d = cdp("DOM.performSearch", {"query": "hello"})
p = payload(t)
sid8 = str(p.get("searchId") or "") if (not e and p) else ""
cnt8 = int(p.get("resultCount") or 0) if (not e and p) else 0
print('  ⑧a performSearch hello err=%s cnt=%s' % (e, cnt8))
if sid8 and cnt8:
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid8, "fromIndex": 0, "toIndex": cnt8})
    p = payload(t)
    print('  ⑧b getSearchResults err=%s payload=%s' % (e, p))
    nids = (p or {}).get("nodeIds") or []
    if nids:
        e, t, d = cdp("DOM.getOuterHTML", {"nodeId": nids[0]})
        p = payload(t)
        print('  ⑧c getOuterHTML(文本节点) err=%s payload=%s txt=%s' % (e, p, t[:100]))
    health('⑧ 之后')

print('== 收尾 ==')
health('收尾')
call("browser_status", {})
print('DONE')
