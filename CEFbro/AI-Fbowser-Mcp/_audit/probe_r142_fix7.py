# -*- coding: utf-8 -*-
r"""R142 探针7(干净重启): 节点编辑实现前的最后未知项。
  ① setOuterHTML 响应形状 + 替换后旧 nodeId 是否失效
  ② setAttributesAsText 效果(name/text → 属性)
  ③ setNodeValue 后 getOuterHTML 回读(文本节点)
  ④ removeAttribute 后 getAttributes 不再含该属性名
  ⑤ querySelector 未命中时的错误文本(可行动消息依据)
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
            if any(k in o for k in ("nodeIds", "nodeId", "attributes", "outerHTML", "root")):
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
call("browser_navigate", {"url": "https://example.com/?r142fix7=%d" % int(time.time())})
js("var d=document.createElement('div');d.id='p1';var s=document.createElement('span');s.id='sp';s.textContent='hello7';d.appendChild(s);document.body.appendChild(d);'ok'")
health('0 基线')
cdp("DOM.enable", {"includeWhitespace": "none"})

# 拿 p1 与 sp 的当前 nodeId
e, t, d = call("browser_vip_dom_get_document", {"depth": 4})
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


p1 = find(root)
print('p1 nodeId=%s' % (p1.get("nodeId") if p1 else None))
if not p1:
    sys.exit(1)
nid = p1["nodeId"]

print('== ① setOuterHTML 响应形状 + 旧 id 有效性 ==')
e, t, d = cdp("DOM.setOuterHTML", {"nodeId": nid, "outerHTML": "<div id='p1new' data-oh='yes'></div>"})
print('  ①a setOuterHTML %.2fs err=%s txt=%s' % (d, e, t[:120]))
e, t, d = cdp("DOM.getOuterHTML", {"nodeId": nid})
p = payload(t)
print('  ①b getOuterHTML(旧id) %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:120]))
e2, t2, d2 = js("String(document.getElementById('p1new') && document.getElementById('p1new').getAttribute('data-oh'))")
print('  ①c 页面侧回读 data-oh=%s (期望 yes) %.2fs' % (t2[:50], d2))
health('① 之后')

print('== ② setAttributesAsText ==')
e, t, d = cdp("DOM.querySelector", {"nodeId": root.get("nodeId"), "selector": "#p1new"})
p = payload(t)
qid = (p or {}).get("nodeId")
print('  ②a querySelector #p1new err=%s nodeId=%s' % (e, qid))
if qid:
    e, t, d = cdp("DOM.setAttributesAsText", {"nodeId": qid, "name": "data-a", "text": "5"})
    print('  ②b setAttributesAsText %.2fs err=%s txt=%s' % (d, e, t[:100]))
    e, t, d = cdp("DOM.getAttributes", {"nodeId": qid})
    p = payload(t)
    print('  ②c getAttributes err=%s payload=%s' % (e, p))
    health('② 之后')

print('== ③ setNodeValue + getOuterHTML 回读(文本节点) ==')
e, t, d = cdp("DOM.querySelector", {"nodeId": root.get("nodeId"), "selector": "#sp"})
p = payload(t)
spid = (p or {}).get("nodeId")
print('  ③a querySelector #sp err=%s nodeId=%s' % (e, spid))
if spid:
    e, t, d = cdp("DOM.setNodeValue", {"nodeId": spid, "value": "changed_text_9"})
    print('  ③b setNodeValue %.2fs err=%s txt=%s' % (d, e, t[:100]))
    e, t, d = cdp("DOM.getOuterHTML", {"nodeId": spid})
    p = payload(t)
    print('  ③c getOuterHTML(文本节点) err=%s payload=%s' % (e, p))
    e2, t2, d2 = js("String(document.getElementById('sp').textContent)")
    print('  ③d 页面侧回读 textContent=%s (期望 changed_text_9) %.2fs' % (t2[:50], d2))
    health('③ 之后')

print('== ④ removeAttribute 后 getAttributes ==')
if qid:
    e, t, d = cdp("DOM.removeAttribute", {"nodeId": qid, "name": "data-oh"})
    print('  ④a removeAttribute %.2fs err=%s txt=%s' % (d, e, t[:100]))
    e, t, d = cdp("DOM.getAttributes", {"nodeId": qid})
    p = payload(t)
    print('  ④b getAttributes err=%s payload=%s (data-oh 应已消失)' % (e, p))
    health('④ 之后')

print('== ⑤ querySelector 未命中错误文本 ==')
e, t, d = cdp("DOM.querySelector", {"nodeId": root.get("nodeId"), "selector": "#no_such_id_xyz"})
print('  ⑤ querySelector(未命中) %.2fs err=%s txt=%s' % (d, e, t[:120]))
health('⑤ 之后')

print('== 收尾 ==')
health('收尾')
call("browser_status", {})
print('DONE')
