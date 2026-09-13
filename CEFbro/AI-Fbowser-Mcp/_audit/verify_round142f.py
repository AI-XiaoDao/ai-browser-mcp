# -*- coding: utf-8 -*-
r"""第142轮验收(定稿形态·真执行版): DOM 族全程我方 CDP 通道 —— 枚举 / 搜索 / 节点编辑(真执行+回读) / 守卫 / 健康。

判据:
  ⓪ tools/list 运行时 schema: node_edit 含 selector, search 含 from_index/to_index
  ① get_document 可重复 ×3(每次映射重建, 仍能定位 #p1), 通道健康
  ② pierce=true 在含影子树页面 → 安全闸门拒绝; pierce=false 正常且看不到影子节点; 通道健康
  ③ node_id 路径 remove_attr 真执行 + verified + 页面侧回读 null
  ④ 守卫: 缺 confirm / node_id=1 / 未知 action / 缺 attr_name 均拒
  ⑤ search query 单次调用: resultCount 正确 + nodeIds 为真实 id(非0) + 该 id 立即用于 set_node_value 成功回读
  ⑥ search ua_shadow 可用; search_id 翻页可用; discard_search 重建代理后旧 search_id 会话作废(可行动失败)
  ⑦ selector 路径 set_attr 真执行 + verified + 页面侧回读
  ⑧ 失效 node_id → 可行动失败(提示重新枚举/selector)
  ⑨ selector 路径 set_outer_html 真执行 + 页面侧回读
  ⑩ selector 路径 remove_node 真执行 + 页面侧回读
  ⑪ 全程每个健康探针 ≤1s; 收尾 status 可用
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
    print('  [%s] %-54s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.0):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return None
    for _ in range(5):
        if isinstance(o, dict):
            if any(k in o for k in ("root", "searchId", "nodeIds", "nodeId", "verified", "submitted")):
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


def root_of(t):
    return payload(t)


def find_node(root, pred):
    if not isinstance(root, dict):
        return None
    if pred(root):
        return root
    for k in ("children", "shadowRoots"):
        for c in (root.get(k) or []):
            r = find_node(c, pred)
            if r:
                return r
    return None


def attrs(n):
    a = (n or {}).get("attributes") or []
    return {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}


def find_id(txt, idv):
    r = root_of(txt)
    if not r:
        return None
    rr = r.get("root") if "root" in r else r
    return find_node(rr, lambda x: attrs(x).get("id") == idv)


JS = ("var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');"
      "var s=document.createElement('span');s.id='sp';s.textContent='needle_text';d.appendChild(s);"
      "var inp=document.createElement('input');inp.id='fi';inp.type='text';d.appendChild(inp);"
      "document.body.appendChild(d);"
      "var h=document.createElement('div');h.id='host1';"
      "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shInner>S</span>';"
      "document.body.appendChild(h);'ok'")

loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?d142f=%d" % int(time.time())})
call("browser_execute_js", {"code": JS})
health('⓪基线 execute_js 快')

print('\n== ⓪ tools/list 运行时 schema ==')
try:
    b = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
    tools = {}
    for t in (o.get("result") or {}).get("tools") or []:
        tools[t.get("name")] = t
    ne_props = list((tools.get("browser_vip_dom_node_edit") or {}).get("inputSchema", {}).get("properties", {}).keys())
    se_props = list((tools.get("browser_vip_dom_search") or {}).get("inputSchema", {}).get("properties", {}).keys())
    rec('⓪node_edit schema 含 selector', 'selector' in ne_props, ne_props)
    rec('⓪search schema 含 from_index/to_index', 'from_index' in se_props and 'to_index' in se_props, se_props)
    rec('⓪工具总数=328', len(tools) == 328, len(tools))
except Exception as ex:
    rec('⓪tools/list', False, repr(ex))

print('\n== ① 枚举(CDP 路线)可重复 ==')
ids = []
for i in (1, 2, 3):
    e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=90)
    n = find_id(t, "p1") if not e else None
    rec('①枚举#%d 成功且定位 #p1' % i, n is not None, "%.2fs nodeId=%s" % (d, n.get("nodeId") if n else None))
    if n:
        ids.append(n.get("nodeId"))
health('①三次枚举后 execute_js 仍快')
print('  [INFO] 三次枚举 nodeId:', ids)

print('\n== ② pierce 安全闸门 ==')
e_t, t_t, d_t = call("browser_vip_dom_get_document", {"depth": 6, "pierce": True}, to=90)
e_f, t_f, d_f = call("browser_vip_dom_get_document", {"depth": 6, "pierce": False}, to=90)
sh_f = find_id(t_f, "shInner") if not e_f else None
rec('②pierce=true 在含影子树页面 → 拒绝(可行动)', e_t and ("shadow root" in t_t) and ("browser_execute_js" in t_t),
    "%.2fs" % d_t)
rec('②pierce=false 仍可枚举(且看不到影子节点)', (not e_f) and sh_f is None, "%.2fs 找到影子=%s" % (d_f, sh_f is not None))
health('②之后 execute_js 仍快')

print('\n== ③ node_id 路径 remove_attr 真执行 ==')
e, t, d = call("browser_vip_dom_get_document", {"depth": 4}, to=90)
n3 = find_id(t, "p1") if not e else None
if n3:
    nid3 = n3.get("nodeId")
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": nid3, "attr_name": "data-x", "confirm": True}, to=60)
    p = payload(t)
    rec('③remove_attr 提交且 verified:true', e is False and p and p.get("submitted") and p.get("verified"),
        "%.2fs %s" % (d, (p or {}).get("readback")))
    health('③之后 execute_js 仍快')
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-x'))"})
    rec('③页面侧回读 data-x 已移除(null)', "null" in t2, t2[:50])
else:
    rec('③remove_attr 真执行', False, '未定位 #p1')
    rec('③页面侧回读', False, '')

print('\n== ④ 守卫 ==')
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": 5})
rec('④缺 confirm 被拒', e and ("confirm" in t), t[:70])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": 1, "confirm": True})
rec('④node_id=1 被拒', e and ("根" in t), t[:70])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "zzz", "node_id": 5, "confirm": True})
rec('④未知 action 被拒', e and ("remove_node" in t), t[:70])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": 5, "confirm": True})
rec('④缺 attr_name 被拒', e and ("attr_name" in t), t[:70])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "set_outer_html", "node_id": 5, "confirm": True})
rec('④set_outer_html 缺 value 被拒', e and ("value" in t), t[:70])
health('④之后 execute_js 仍快')

print('\n== ⑤ search 单次调用(预查找+取回) ==')
e, t, d = call("browser_vip_dom_search", {"query": "needle_text"}, to=90)
p = payload(t)
nids5 = (p or {}).get("nodeIds") or []
rec('⑤search 返回 resultCount=1 且 nodeIds 真实(非0)', (not e) and p and p.get("resultCount") == 1 and nids5 and nids5[0] > 0,
    "%.2fs %s" % (d, p))
health('⑤search 之后 execute_js 仍快')
if nids5 and nids5[0] > 0:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "set_node_value", "node_id": nids5[0], "value": "changed_9", "confirm": True}, to=60)
    p = payload(t)
    rec('⑤搜索结果 nodeId 立即 set_node_value 真执行+verified', e is False and p and p.get("verified"),
        "%.2fs" % d)
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('sp').textContent)"})
    rec('⑤页面侧回读 textContent=changed_9', "changed_9" in t2, t2[:50])
else:
    rec('⑤set_node_value 链', False, '未拿到搜索 nodeId')

print('\n== ⑥ ua_shadow / search_id 翻页 / discard_search ==')
e, t, d = call("browser_vip_dom_search", {"query": "changed_9", "ua_shadow": True}, to=90)
p = payload(t)
rec('⑥ua_shadow=true 预查找可用', (not e) and p and p.get("searchId"), "%.2fs %s" % (d, p))
sid6 = (p or {}).get("searchId") or ""
cnt6 = (p or {}).get("resultCount") or 0
e, t, d = call("browser_vip_dom_search", {"search_id": sid6, "from_index": 0, "to_index": 10}, to=90)
p = payload(t)
rec('⑥search_id 翻页取回(自动收敛 to_index)', (not e) and p and isinstance(p.get("nodeIds"), list), "%.2fs %s" % (d, p))
health('⑥search_id 之后 execute_js 仍快')
if sid6:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "discard_search", "search_id": sid6}, to=60)
    try:
        pd = json.loads(t)
    except Exception:
        pd = {}
    rec('⑥discard_search 重建代理成功', (not e) and bool(pd.get("success")), "%.2fs %s" % (d, (pd.get("note") or "")[:60]))
    e, t, d = call("browser_vip_dom_search", {"search_id": sid6}, to=90)
    rec('⑥discard 后旧 search_id 作废(可行动失败)', e and ("会话" in t), "%.2fs %s" % (d, t[:70]))
    health('⑥discard 之后 execute_js 仍快')
else:
    rec('⑥discard_search 链', False, '无 searchId')

print('\n== ⑦ selector 路径 set_attr 真执行 ==')
e, t, d = call("browser_vip_dom_node_edit",
               {"action": "set_attr", "selector": "#p1", "attr_name": "data-y", "value": "42", "confirm": True}, to=60)
p = payload(t)
rec('⑦selector set_attr 真执行+verified', e is False and p and p.get("verified"),
    "%.2fs readback=%s" % (d, (p or {}).get("readback")))
health('⑦之后 execute_js 仍快')
e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-y'))"})
rec('⑦页面侧回读 data-y=42', "42" in t2, t2[:50])

print('\n== ⑧ 失效 node_id → 可行动失败 ==')
stale = ids[0] if ids else 0
if stale:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "set_attr", "node_id": stale, "attr_name": "data-z", "value": "1", "confirm": True}, to=60)
    rec('⑧旧 node_id 提交 → 可行动失败(提示重新枚举/selector)', e and ("selector" in t or "重新" in t),
        "%.2fs %s" % (d, t[:80]))
    health('⑧之后 execute_js 仍快')
else:
    rec('⑧失效 node_id', False, '无旧 id')

print('\n== ⑨ selector set_outer_html 真执行 ==')
e, t, d = call("browser_vip_dom_node_edit",
               {"action": "set_outer_html", "selector": "#sp", "value": "<b id='bold'>BB</b>", "confirm": True}, to=60)
p = payload(t)
rec('⑨set_outer_html 真执行+verified', e is False and p and p.get("verified"), "%.2fs" % d)
e2, t2, _ = call("browser_execute_js", {"code": "String(!!document.getElementById('bold'))"})
rec('⑨页面侧回读 #bold 存在', "true" in t2, t2[:40])
health('⑨之后 execute_js 仍快')

print('\n== ⑩ selector remove_node 真执行 ==')
e, t, d = call("browser_vip_dom_node_edit",
               {"action": "remove_node", "selector": "#bold", "confirm": True}, to=60)
p = payload(t)
rec('⑩remove_node 真执行+verified(node-gone)', e is False and p and p.get("verified") and p.get("readback") == "node-gone",
    "%.2fs" % d)
e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('bold')===null)"})
rec('⑩页面侧回读 #bold 已移除', "true" in t2, t2[:40])
health('⑩之后 execute_js 仍快')

print('\n== ⑪ 收尾 ==')
health('⑪收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑪browser_status 可用', (not e), "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
