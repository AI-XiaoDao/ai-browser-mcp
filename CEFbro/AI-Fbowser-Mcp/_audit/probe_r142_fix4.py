# -*- coding: utf-8 -*-
r"""R142 探针4(干净重启): 搜索族全流程约束。
  ① enable
  ② performSearch → id (无任何 getDocument 干扰)
  ③ getSearchResults 立即取 → nodeIds?
  ④ performSearch + includeUserAgentShadowDOM:true → 干净 or 报错?
  ⑤ discardSearch → ok?
  ⑥ performSearch → getDocument(重建映射) → getSearchResults → 是否失效(约束证实)
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
    print('  [%s] %-44s %.2fs err=%s txt=%s' % ('PASS' if ok else 'FAIL', tag, d, e, t[:40]))
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
            if "searchId" in o or "nodeIds" in o or "nodeId" in o:
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
call("browser_navigate", {"url": "https://example.com/?r142fix4=%d" % int(time.time())})
js("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');document.body.appendChild(d);'ok'")
health('0 基线')

print('== ① enable ==')
e, t, d = cdp("DOM.enable", {"includeWhitespace": "none"})
print('  ① enable %.2fs err=%s txt=%s' % (d, e, t[:80]))
health('① 之后')

print('== ② performSearch ==')
e, t, d = cdp("DOM.performSearch", {"query": "data-x"})
p = payload(t)
print('  ② performSearch %.2fs err=%s payload=%s' % (d, e, p))
sid = str(p.get("searchId") or "") if (not e and p) else ""
health('② 之后')

print('== ③ getSearchResults 立即取 ==')
if sid:
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": 10})
    p = payload(t)
    print('  ③ getSearchResults %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:120]))
    health('③ 之后')

print('== ④ performSearch + includeUserAgentShadowDOM ==')
e, t, d = cdp("DOM.performSearch", {"query": "data-x", "includeUserAgentShadowDOM": True})
p = payload(t)
print('  ④ performSearch(UA影子) %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:120]))
health('④ 之后')

print('== ⑤ discardSearch ==')
if sid:
    e, t, d = cdp("DOM.discardSearch", {"searchId": sid})
    print('  ⑤ discardSearch %.2fs err=%s txt=%s' % (d, e, t[:120]))
    health('⑤ 之后')

print('== ⑥ 搜索后 getDocument 再取结果(约束证实) ==')
e, t, d = cdp("DOM.performSearch", {"query": "data-x"})
p = payload(t)
sid6 = str(p.get("searchId") or "") if (not e and p) else ""
print('  ⑥a performSearch err=%s sid=%s' % (e, sid6))
call("browser_vip_dom_get_document", {"depth": 3})
if sid6:
    e, t, d = cdp("DOM.getSearchResults", {"searchId": sid6, "fromIndex": 0, "toIndex": 10})
    p = payload(t)
    print('  ⑥b 枚举后 getSearchResults %.2fs err=%s payload=%s txt=%s' % (d, e, p, t[:120]))
    health('⑥ 之后')

print('== 收尾 ==')
health('收尾')
call("browser_status", {})
print('DONE')
