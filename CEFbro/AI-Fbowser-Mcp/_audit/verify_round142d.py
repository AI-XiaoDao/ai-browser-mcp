# -*- coding: utf-8 -*-
r"""第142轮最终验收(两段式): 节点编辑改成"派发 + mcp_result 取回执"后是否真的可用且不毒化会话。

判据(全部有回读预言机):
  ① 普通页面: 枚举得 nodeId → `remove_attr` 回 async 回执 → `mcp_result` 取到结果 → 页面侧 `getAttribute` 变 null;
  ② 每次编辑后 `execute_js` 仍 0.03s 级(**不被毒化**);
  ③ `set_attr` 同法、回读 `data-x=edited`; `remove_node` 同法、页面侧 `getElementById===null`;
  ④ 含影子树页面: 提交前预检**拒绝**(可行动), 且之后 `execute_js` 仍快;
  ⑤ 收尾健康。

用法: py -3 _audit\verify_round142d.py
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
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


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


def node_id(want, depth=4):
    e, t, d = call("browser_vip_dom_get_document", {"depth": depth}, to=90)
    if e:
        return 0, t
    n = find(root_of(t), lambda x: attrs(x).get("id") == want)
    return (n.get("nodeId") if n else 0), "%.2fs" % d


def edit_and_wait(action, nid, extra=None):
    """两段式: 提交拿 task_id → mcp_result 取回执。"""
    args = {"action": action, "node_id": nid, "confirm": True}
    if extra:
        args.update(extra)
    e, t, d = call("browser_vip_dom_node_edit", args, to=60)
    if e:
        return False, t[:120]
    m = re.search(r"task_[0-9_]+", t)
    tid = m.group(0) if m else None
    if not tid:
        # 也可能回的是 request_id: 形如 <命令ID>_ed
        m2 = re.search(r'request_id:"([^"]+)"', t)
        tid = m2.group(1) if m2 else None
    if not tid:
        return False, "回执里没有 task_id: %s" % t[:120]
    time.sleep(0.4)
    e2, t2, _ = call("mcp_result", {"request_id": tid}, to=60)
    return (not e2), t2[:120]


def health(tag, limit=1.0):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


PLAIN_JS = ("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');"
            "d.innerHTML='<span id=p1c>x</span>';document.body.appendChild(d);'ok'")
SHADOW_JS = ("var d=document.createElement('div');d.id='plainDiv';d.setAttribute('data-x','1');"
             "document.body.appendChild(d);"
             "var h=document.createElement('div');h.id='host1';"
             "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shInner>S</span>';"
             "document.body.appendChild(h);'ok'")

print('== 普通页面(无影子树) ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?d142d=%d" % int(time.time())})
call("browser_execute_js", {"code": PLAIN_JS})
health("①基线 execute_js 快")
nid, note = node_id("p1")
rec("①枚举并定位 #p1", nid > 0, "nodeId=%s %s" % (nid, note))

if nid:
    ok, msg = edit_and_wait("remove_attr", nid, {"attr_name": "data-x"})
    rec("①remove_attr 两段式取到回执", ok, msg)
    health("①remove_attr 后 execute_js 仍快")
    e, t, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-x'))"})
    rec("①页面侧回读: data-x 已移除", "null" in t, t[:60])

    nid2, _ = node_id("p1")
    ok, msg = edit_and_wait("set_attr", nid2 or nid, {"attr_name": "data-x", "value": "edited"})
    rec("①set_attr 两段式取到回执", ok, msg)
    health("①set_attr 后 execute_js 仍快")
    e, t, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-x'))"})
    rec("①页面侧回读: data-x=edited", "edited" in t, t[:60])

    nid3, _ = node_id("p1")
    ok, msg = edit_and_wait("remove_node", nid3 or nid)
    rec("①remove_node 两段式取到回执", ok, msg)
    health("①remove_node 后 execute_js 仍快")
    e, t, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1')===null)"})
    rec("①页面侧回读: 节点已删除", "true" in t, t[:60])
    e, t, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1c')===null)"})
    rec("①子节点一并删除", "true" in t, t[:60])
else:
    for tag in ("①remove_attr 两段式取到回执", "①remove_attr 后 execute_js 仍快", "①页面侧回读: data-x 已移除",
                "①set_attr 两段式取到回执", "①set_attr 后 execute_js 仍快", "①页面侧回读: data-x=edited",
                "①remove_node 两段式取到回执", "①remove_node 后 execute_js 仍快", "①页面侧回读: 节点已删除",
                "①子节点一并删除"):
        rec(tag, False, "未取到 nodeId")

print('\n== 含影子树页面: 必须拒绝且不毒化 ==')
call("browser_navigate", {"url": "https://example.com/?d142d2=%d" % int(time.time())})
call("browser_execute_js", {"code": SHADOW_JS})
nid_s, _ = node_id("plainDiv")
rec("②影子树页面仍可只读枚举(定位 plainDiv)", nid_s > 0, "nodeId=%s" % nid_s)
e, t, d = call("browser_vip_dom_get_document", {"depth": 6, "pierce": True}, to=90)
sh = find(root_of(t), lambda x: attrs(x).get("id") == "shInner") if not e else None
rec("②pierce=true 能看到影子树内容(#shInner)", sh is not None, "nodeId=%s" % (sh.get("nodeId") if sh else None))
if nid_s:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": nid_s, "attr_name": "data-x", "confirm": True}, to=60)
    rec("②含影子树页面 → 明确拒绝(可行动)", e and ("shadow root" in t), "%.2fs %s" % (d, t[:90]))
    health("②拒绝后 execute_js 仍快(**未被毒化**)")
else:
    rec("②含影子树页面 → 明确拒绝(可行动)", False, "未定位到 plainDiv")

print('\n== 收尾 ==')
health("④收尾 execute_js 快")
e, t, d = call("browser_status", {})
rec("④browser_status 可用", (not e), "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
