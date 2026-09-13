# -*- coding: utf-8 -*-
r"""R142 探针6(干净重启): 搜索真实 nodeId + disable/enable 清会话 + 文本节点 outerHTML。
  ① getDocument(depth=4) → performSearch → getSearchResults → nodeIds 为真实 id?
  ② disable → enable → 旧 searchId 再取 → "No search session"?(等效清除证实)
  ③ getOuterHTML 文本节点形状(set_node_value 回读依据)
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
call("browser_navigate", {"url": "https://example.com/?r142fix6=%d" % int(time.time())})
js("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');var s=document.createElement('span');s.id='sp';s.textContent='needle_text';d.appendChild(s);document.body.appendChild(d);'ok'")
health('0 基线')

print('== ① getDocument 先 → performSearch → getSearchResults ==')
cdp("DOM.enable", {"includeWhitespace": "none"})
e, t, d = call("browser_vip_dom_get_document", {"depth": 4})
print('  ①a getDocument err=%s %.2fs' % (e, d))
e, t, d = cdp("DOM.performSearch", {"query": "data-x"})
p = payload(t)
print('  ①b performSearch err=%s payload=%s' % (e, p))
sid = str(p.get("searchId") or "") if (not e and p) else ""
cnt = int(p.get("resultCount") or 0) if (not e and p) else 0
if sid:
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": cnt})
    p = payload(t)
    print('  ①c getSearchResults err=%s payload=%s (期望真实 id 非 0)' % (e, p))
    health('① 之后')

print('== ② disable+enable 清会话 ==')
if sid:
    e, t, d = cdp("DOM.disable", {})
    print('  ②a disable err=%s %.2fs txt=%s' % (e, d, t[:60]))
    e, t, d = cdp("DOM.enable", {"includeWhitespace": "none"})
    print('  ②b enable err=%s %.2fs' % (e, d))
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": 1})
    print('  ②c 旧sid取结果 err=%s txt=%s (期望 No search session)' % (e, t[:100]))
    health('② 之后')

print('== ③ getOuterHTML 文本节点形状 ==')
e, t, d = call("browser_vip_dom_get_document", {"depth": 4})
print('  ③a getDocument err=%s' % e)
e, t, d = cdp("DOM.performSearch", {"query": "needle_text"})
p = payload(t)
sid3 = str(p.get("searchId") or "") if (not e and p) else ""
cnt3 = int(p.get("resultCount") or 0) if (not e and p) else 0
print('  ③b performSearch needle_text err=%s cnt=%s' % (e, cnt3))
if sid3 and cnt3:
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid3, "fromIndex": 0, "toIndex": cnt3})
    p = payload(t)
    nids = (p or {}).get("nodeIds") or []
    print('  ③c getSearchResults err=%s nodeIds=%s' % (e, nids))
    if nids:
        e, t, d = cdp("DOM.getOuterHTML", {"nodeId": nids[0]})
        p = payload(t)
        print('  ③d getOuterHTML err=%s payload=%s txt=%s' % (e, p, t[:100]))
        health('③ 之后')

print('== 收尾 ==')
health('收尾')
call("browser_status", {})
print('DONE')
