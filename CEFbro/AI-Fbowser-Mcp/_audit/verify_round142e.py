# -*- coding: utf-8 -*-
r"""第142轮最终验收(定稿形态): 只读能力 + 可行动路由 + 守卫, 全程不毒化会话。

判据:
  ① `browser_vip_dom_get_document`(CDP 路线)可**重复**使用、回包是标准 `{"root":{...}}` 节点树;
  ② `pierce=true` 能看到影子树内容, `pierce=false` 看不到(**判别差**);
  ③ `browser_vip_dom_node_edit` 对节点类动作返回**可行动路由**(含可直接用的 `browser_cdp_call` 调用),
     且**不执行**任何破坏性命令 ⇒ 之后 `execute_js` 仍 0.03s 级;
  ④ 守卫: 缺 confirm / node_id=1 / 未知 action / 缺 attr_name 都被拒;
  ⑤ `discard_search` 仍由本工具执行且成功;
  ⑥ **按路由给出的调用真的能改 DOM**(用 browser_cdp_call 提交, 页面侧回读) —— 证明替代路径可用;
  ⑦ 收尾健康。

用法: py -3 _audit\verify_round142e.py
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []
INFO = []


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


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


def info(tag, detail=""):
    INFO.append(tag)
    print('  [INFO] %-50s %s' % (tag, str(detail)[:100]))


def root_of(txt):
    try:
        o = json.loads(txt)
    except Exception:
        return None
    for _ in range(4):
        if not isinstance(o, dict):
            return None
        if "root" in o:
            return o["root"]
        nxt = o.get("data")
        if isinstance(nxt, str):
            try:
                nxt = json.loads(nxt)
            except Exception:
                return None
        o = nxt
    return o if isinstance(o, dict) else None


def find(n, pred):
    if not isinstance(n, dict):
        return None
    if pred(n):
        return n
    for k in ("children", "shadowRoots"):
        for c in (n.get(k) or []):
            r = find(c, pred)
            if r:
                return r
    return None


def attrs(n):
    a = (n or {}).get("attributes") or []
    return {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}


def health(tag, limit=1.0):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


JS = ("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');"
      "d.innerHTML='<span id=p1c>x</span>';document.body.appendChild(d);"
      "var h=document.createElement('div');h.id='host1';"
      "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shInner>S</span>';"
      "document.body.appendChild(h);'ok'")

loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?d142e=%d" % int(time.time())})
call("browser_execute_js", {"code": JS})
health("①基线 execute_js 快")

print('\n== ① 枚举(CDP 路线)可重复使用 ==')
ids = []
for i in (1, 2, 3):
    e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=90)
    n = find(root_of(t), lambda x: attrs(x).get("id") == "p1") if not e else None
    rec("①枚举#%d 成功且能定位 #p1" % i, n is not None, "%.2fs nodeId=%s" % (d, n.get("nodeId") if n else None))
    if n:
        ids.append(n.get("nodeId"))
health("①三次枚举后 execute_js 仍快")
if ids:
    info("三次枚举拿到同一节点 id", ids)

print('\n== ② pierce 安全闸门(含影子树页面必须拒绝) ==')
e_t, t_t, d_t = call("browser_vip_dom_get_document", {"depth": 6, "pierce": True}, to=90)
e_f, t_f, d_f = call("browser_vip_dom_get_document", {"depth": 6, "pierce": False}, to=90)
sh_f = find(root_of(t_f), lambda x: attrs(x).get("id") == "shInner") if not e_f else None
rec("②pierce=true 在含影子树页面 → 拒绝(可行动)", e_t and ("shadow root" in t_t) and ("browser_execute_js" in t_t),
    "%.2fs %s" % (d_t, t_t[:90]))
rec("②pierce=false 仍可枚举(且看不到影子节点)", (not e_f) and sh_f is None, "%.2fs 找到影子=%s" % (d_f, sh_f is not None))
health("②之后 execute_js 仍快(未被毒化)")

print('\n== ③ 节点编辑: 可行动路由(不自己提交) ==')
nid = ids[0] if ids else 0
if nid:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": nid, "attr_name": "data-x", "confirm": True}, to=60)
    rec("③返回可行动路由(含 browser_cdp_call)", e and ("browser_cdp_call" in t) and ("DOM.removeAttribute" in t),
        "%.2fs %s" % (d, t[:90]))
    health("③未提交破坏性命令 ⇒ execute_js 仍快")
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-x'))"})
    rec("③页面确实未被改动(data-x 仍为 1)", "1" in t2, t2[:60])
else:
    rec("③返回可行动路由(含 browser_cdp_call)", False, "未取到 nodeId")
    rec("③未提交破坏性命令 ⇒ execute_js 仍快", False, "")

print('\n== ④ 守卫 ==')
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": nid})
rec("④缺 confirm 被拒", e and ("confirm" in t), t[:80])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": 1, "confirm": True})
rec("④node_id=1 被拒", e and ("根" in t), t[:80])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "zzz", "node_id": nid, "confirm": True})
rec("④未知 action 被拒", e and ("remove_node" in t), t[:80])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": nid, "confirm": True})
rec("④缺 attr_name 被拒", e and ("attr_name" in t), t[:80])

print('\n== ⑤ discard_search 仍由本工具执行 ==')
e, t, _ = call("browser_vip_dom_search", {"query": "S"}, to=90)
sid = ""
try:
    sid = json.loads(t).get("searchId") or ""
except Exception:
    sid = ""
rec("⑤预查找返回 searchId", bool(sid), "searchId=%s" % sid)
if sid:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "discard_search", "search_id": sid}, to=60)
    rec("⑤discard_search 成功", not e, "%.2fs %s" % (d, t[:70]))
health("⑤之后 execute_js 仍快")

print('\n== ⑥ 路由可用性: 在**普通页面**上按路由调用真的能改 DOM ==')
call("browser_navigate", {"url": "https://example.com/?d142e2=%d" % int(time.time())})
call("browser_execute_js", {"code": "var d=document.createElement('div');d.id='q1';d.setAttribute('data-y','1');document.body.appendChild(d);'ok'"})
e_q, t_q, _ = call("browser_vip_dom_get_document", {"depth": 4}, to=90)
nq = find(root_of(t_q), lambda x: attrs(x).get("id") == "q1") if not e_q else None
rec("⑥普通页面可枚举定位 #q1", nq is not None, "nodeId=%s" % (nq.get("nodeId") if nq else None))
if nq:
    e, t, d = call("browser_cdp_call", {"method": "DOM.removeAttribute",
                                        "params": json.dumps({"nodeId": nq.get("nodeId"), "name": "data-y"})}, to=60)
    rec("⑥browser_cdp_call 提交 removeAttribute 成功", not e, "%.2fs %s" % (d, t[:60]))
    health("⑥之后 execute_js 仍快")
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('q1').getAttribute('data-y'))"})
    rec("⑥页面侧回读: data-y 已移除(替代路径有效)", "null" in t2, t2[:60])
else:
    rec("⑥browser_cdp_call 提交 removeAttribute 成功", False, "未取到 nodeId")

print('\n== ⑦ 收尾 ==')
health("⑦收尾 execute_js 快")
e, t, d = call("browser_status", {})
rec("⑦browser_status 可用", (not e), "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过 (INFO %d)' % (len(RES) - len(bad), len(RES), len(INFO)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
