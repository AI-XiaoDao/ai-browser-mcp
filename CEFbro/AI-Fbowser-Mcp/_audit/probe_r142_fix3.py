# -*- coding: utf-8 -*-
r"""R142 探针3(接探针2同一实例, 不重启): 
  ① performSearch 现在(DOM.enable 之后)可用? → enable 是否保持
  ② get_document 再取一次 → nodeId 是否继续变
  ③ getSearchResults → 用搜出的 nodeId 做 removeAttribute → 回读
  ④ 用**最新** get_document 的 nodeId 做 removeAttribute → 回读
  ⑤ 用**旧** get_document 的 nodeId(36) 做 setAttribute → 干净报错还是挂住?
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

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
    print('  [%s] %-44s %.2fs err=%s txt=%s' % ('PASS' if ok else 'FAIL', tag, d, e, t[:40]))
    return ok


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return None
    for _ in range(4):
        if isinstance(o, dict):
            if "searchId" in o or "nodeIds" in o or "root" in o or "nodeId" in o:
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


def get_doc_id():
    e, t, d = call("browser_vip_dom_get_document", {"depth": 4})
    if e:
        return None, t
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
        return (n2.get("nodeId") if n2 else None), ""
    except Exception as ex:
        return None, "parse:%r" % ex


print('== ① performSearch(DOM.enable 已开) ==')
e, t, d = call("browser_cdp_call", {"method": "DOM.performSearch", "params": json.dumps({"query": "data-x"})})
p = payload(t)
print('  ① performSearch %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:100]))
sid = str(p.get("searchId") or "") if (not e and p) else ""
health('① 之后 execute_js')

print('== ② get_document 再次取 id ==')
nid_new, perr = get_doc_id()
print('  ② 最新 nodeId(p1)=%s perr=%s (探针2里是 18/36)' % (nid_new, perr))
health('② 之后 execute_js')

print('== ③ 用搜索结果的 nodeId 做 removeAttribute ==')
if sid:
    e, t, d = call("browser_cdp_call", {"method": "DOM.getSearchResults",
                                        "params": json.dumps({"searchId": sid, "fromIndex": 0, "toIndex": 10})})
    p = payload(t)
    print('  ③ getSearchResults %.2fs err=%s payload=%s' % (d, e, p))
    nids = (p or {}).get("nodeIds") or []
    if nids:
        e, t, d = call("browser_cdp_call", {"method": "DOM.removeAttribute",
                                            "params": json.dumps({"nodeId": nids[0], "name": "data-x"})})
        print('  ③ removeAttribute(search id=%s) %.2fs err=%s txt=%s' % (nids[0], d, e, t[:80]))
        health('③ 之后 execute_js')
        e2, t2, d2 = js("String(document.getElementById('p1').getAttribute('data-x'))")
        print('  ③ 页面侧回读 data-x=%s (期望 null) %.2fs' % (t2[:40], d2))
    else:
        print('  ③ 未拿到 nodeIds')
        health('③ 之后 execute_js')

print('== ④ 用最新 get_document 的 id 做 setAttribute ==')
if nid_new:
    e, t, d = call("browser_cdp_call", {"method": "DOM.setAttributeValue",
                                        "params": json.dumps({"nodeId": nid_new, "name": "data-y", "value": "42"})})
    print('  ④ setAttributeValue(id=%s) %.2fs err=%s txt=%s' % (nid_new, d, e, t[:80]))
    health('④ 之后 execute_js')
    e2, t2, d2 = js("String(document.getElementById('p1').getAttribute('data-y'))")
    print('  ④ 页面侧回读 data-y=%s (期望 42) %.2fs' % (t2[:40], d2))

print('== ⑤ 用旧 id(36) 做 setAttribute → 干净报错还是挂? ==')
e, t, d = call("browser_cdp_call", {"method": "DOM.setAttributeValue",
                                    "params": json.dumps({"nodeId": 36, "name": "data-z", "value": "9"})}, to=60)
print('  ⑤ setAttributeValue(旧id=36) %.2fs err=%s txt=%s' % (d, e, t[:80]))
health('⑤ 之后 execute_js')

print('== 收尾 ==')
health('收尾 execute_js')
call("browser_status", {})
print('DONE')
