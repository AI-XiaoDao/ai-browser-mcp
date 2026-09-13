# -*- coding: utf-8 -*-
r"""第142轮验收: VIP 开发者 DOM 族 —— ①pierce/ua_shadow 透传 ②节点编辑 7 个 action 真机可用。

判据(用**重新枚举 + 页面侧断言**双预言机, 不看回包文案):
  ① tools/list: `browser_vip_dom_get_document` 有 pierce、`browser_vip_dom_search` 有 ua_shadow、
     `browser_vip_dom_node_edit` 已注册且声明 6 个参数;
  ② 枚举结果里能定位到注入的 `#mcpProbeDiv`(含属性列表);
  ③ `remove_attr` → 重新枚举该节点属性里 `data-probe` **消失**;
  ④ `set_attr` → 重新枚举属性值变成新值(正反向对照);
  ⑤ `remove_node` → 重新枚举节点消失 **且** 页面侧 `document.getElementById('mcpProbeDiv')===null`;
  ⑥ `discard_search` → 用预查找的 searchId 调用成功;
  ⑦ 守卫: 无 confirm 拒绝、node_id=1 拒绝、未知 action 拒绝;
  ⑧ `pierce`: 影子树内容在 pierce=false/true 下的差异(如实记录, 差异不显著时记 INFO);
  ⑨ 收尾健康。

用法: py -3 _audit\verify_round142.py
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


def payload(txt):
    try:
        o = json.loads(txt)
    except Exception:
        return {}
    d = o.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return o if isinstance(o, dict) else {}


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


def info(tag, detail=""):
    INFO.append(tag)
    print('  [INFO] %-48s %s' % (tag, str(detail)[:100]))


def enumerate_dom(depth=4, pierce=False):
    """枚举 DOM 并返回**根节点子树**。

    ⚠ 回包形态是 CDP `DOM.getDocument` 的 `{"root":{...}}` —— 解析后必须从 `root` 往下走,
    否则 `children` 为空、节点总数算成 1(上一版就是这么把"能定位到节点"误判成失败的)。
    """
    e, t, d = call("browser_vip_dom_get_document", {"depth": depth, "pierce": pierce}, to=90)
    if e:
        return None, t
    txt = t
    try:
        o = json.loads(txt)
    except Exception:
        try:
            o = json.loads(json.loads(txt).get("message") or "{}")
        except Exception:
            o = {}
    if not isinstance(o, dict) or not o:
        p = payload(t) if 'payload' in globals() else {}
        tid = (p.get("task_id") if isinstance(p, dict) else None) or \
              ((p.get("data") or {}).get("task_id") if isinstance(p.get("data"), dict) else None)
        if tid:
            e2, t2, _ = call("mcp_result", {"request_id": tid}, to=60)
            try:
                o = json.loads(t2)
            except Exception:
                o = {}
    # ⚠ 回包是 `{"id":..,"success":true,"data":{"root":{...}}}`: root 藏在 data 里(实测),
    #   上一版只看顶层 root ⇒ 解析成 0 个节点。这里逐层剥到 root 为止。
    层 = o
    for _ in range(4):
        if not isinstance(层, dict):
            break
        if "root" in 层:
            return 层["root"], ""
        nxt = 层.get("data")
        if isinstance(nxt, str):
            try:
                nxt = json.loads(nxt)
            except Exception:
                break
        if not isinstance(nxt, dict):
            break
        层 = nxt
    return (层 if isinstance(层, dict) else None), "解析失败: %s" % txt[:120]


def find_node(tree, pred, out=None):
    """在 CDP getDocument 树里深度优先找第一个满足 pred 的节点。"""
    if out is None:
        out = []
    if not isinstance(tree, dict):
        return None
    if pred(tree):
        return tree
    for ch in (tree.get("children") or []):
        r = find_node(ch, pred, out)
        if r:
            return r
    for ch in (tree.get("shadowRoots") or []):
        r = find_node(ch, pred, out)
        if r:
            return r
    return None


def attrs_of(node):
    a = node.get("attributes") or []
    return {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}


PROBE_JS = ("var d=document.createElement('div');d.id='mcpProbeDiv';d.className='probe-cls';"
            "d.setAttribute('data-probe','yes');d.innerHTML='<span id=mcpProbeSpan>标记文本</span>';"
            "document.body.appendChild(d);"
            "var h=document.createElement('div');h.id='mcpShadowHost';"
            "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shadowInner>ShadowSentinel</span>';"
            "document.body.appendChild(h);'ok'")

print('== ① tools/list ==')
try:
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode(),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    tools = ((o.get("result") or {}).get("tools") or [])

    def props(n):
        t = [x for x in tools if x.get("name") == n]
        return (((t[0].get("inputSchema") or {}).get("properties") or {}) if t else {})

    rec("工具数 328", len(tools) == 328, "tools=%d" % len(tools))
    rec("get_document 声明 pierce", "pierce" in props("browser_vip_dom_get_document"),
        sorted(props("browser_vip_dom_get_document")))
    rec("dom_search 声明 ua_shadow", "ua_shadow" in props("browser_vip_dom_search"),
        sorted(props("browser_vip_dom_search")))
    np = props("browser_vip_dom_node_edit")
    rec("node_edit 已注册且声明 6 参数",
        {"action", "node_id", "attr_name", "value", "search_id", "confirm"} <= set(np), sorted(np))
except Exception as ex:
    rec("tools/list 读取", False, repr(ex))

print('\n== 干净实例 + 注入测试节点 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?dom142=%d" % int(time.time())})
call("browser_execute_js", {"code": PROBE_JS})

print('\n== ② 枚举并定位 #mcpProbeDiv ==')
tree, err = enumerate_dom(4)
if not tree:
    rec("枚举 DOM 成功", False, err[:120])
    print('\n结果: 0/%d(枚举失败, 后续无法验证)' % len(RES)); sys.exit(1)
rec("枚举 DOM 成功且是 CDP 节点树", isinstance(tree, dict) and "root" in tree, "顶层键=%s" % sorted(tree)[:6])
div = find_node(tree, lambda n: attrs_of(n).get("id") == "mcpProbeDiv")
rec("能在树里定位 #mcpProbeDiv(含属性)", div is not None, "nodeId=%s attrs=%s" % (div.get("nodeId") if div else None, attrs_of(div) if div else {}))
node_id = div.get("nodeId") if div else 0
span = find_node(tree, lambda n: attrs_of(n).get("id") == "mcpProbeSpan")
span_id = span.get("nodeId") if span else 0

print('\n== ③ remove_attr(移除 data-probe) ==')
if node_id:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": node_id, "attr_name": "data-probe", "confirm": True})
    rec("remove_attr 提交成功", not e, "%.2fs %s" % (d, t[:80]))
    time.sleep(0.3)
    tree2, _ = enumerate_dom(4)
    div2 = find_node(tree2, lambda n: attrs_of(n).get("id") == "mcpProbeDiv") if tree2 else None
    rec("回读: data-probe 已消失", div2 is not None and "data-probe" not in attrs_of(div2),
        "attrs=%s" % (attrs_of(div2) if div2 else None))
    print('\n== ④ set_attr(置 data-probe=edited) ==')
    # DOM 变化后 nodeId 可能失效 ⇒ 每次编辑前重新枚举拿最新 nodeId(这也是描述里要求的使用协议)
    if div2:
        node_id = div2.get("nodeId") or node_id
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "set_attr", "node_id": node_id, "attr_name": "data-probe", "value": "edited", "confirm": True})
    rec("set_attr 提交成功", not e, "%.2fs" % d)
    time.sleep(0.3)
    tree3, _ = enumerate_dom(4)
    div3 = find_node(tree3, lambda n: attrs_of(n).get("id") == "mcpProbeDiv") if tree3 else None
    rec("回读: data-probe=edited", div3 is not None and attrs_of(div3).get("data-probe") == "edited",
        "attrs=%s" % (attrs_of(div3) if div3 else None))
    if div3:
        node_id = div3.get("nodeId") or node_id
else:
    for tag in ("remove_attr 提交成功", "回读: data-probe 已消失", "set_attr 提交成功", "回读: data-probe=edited"):
        rec(tag, False, "未取到 nodeId")

print('\n== ⑤ remove_node(连同子节点) ==')
if node_id:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": node_id, "confirm": True})
    rec("remove_node 提交成功", not e, "%.2fs" % d)
    time.sleep(0.8)
    tree4, _ = enumerate_dom(4)
    gone = find_node(tree4, lambda n: attrs_of(n).get("id") == "mcpProbeDiv") if tree4 else None
    rec("回读: 节点已从树里消失", gone is None, "仍找到=%s" % (gone is not None))
    e5, t5, _ = call("browser_execute_js", {"code": "String(document.getElementById('mcpProbeDiv')===null)"})
    rec("页面侧独立断言: getElementById 为 null", "true" in t5, t5[:70])
    e6, t6, _ = call("browser_execute_js", {"code": "String(document.getElementById('mcpProbeSpan')===null)"})
    rec("子节点也一并删除(span 也 null)", "true" in t6, t6[:70])
else:
    for tag in ("remove_node 提交成功", "回读: 节点已从树里消失", "页面侧独立断言: getElementById 为 null", "子节点也一并删除(span 也 null)"):
        rec(tag, False, "未取到 nodeId")

print('\n== ⑥ discard_search ==')
e, t, d = call("browser_vip_dom_search", {"query": "ShadowSentinel"}, to=90)
sid = ""
try:
    sid = json.loads(t).get("searchId") or ""
    if not sid:
        sid = (payload(t).get("searchId") or "")
except Exception:
    sid = ""
rec("预查找返回 searchId", bool(sid), "searchId=%s | %s" % (sid, t[:70]))
if sid:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "discard_search", "search_id": sid}, to=60)
    rec("discard_search 成功", not e, "%.2fs %s" % (d, t[:80]))

print('\n== ⑦ 守卫 ==')
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": 5})
rec("缺 confirm 被拒", e and ("confirm" in t), t[:80])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": 1, "confirm": True})
rec("node_id=1(根节点) 被拒", e and ("根" in t), t[:80])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "nonsense", "node_id": 5, "confirm": True})
rec("未知 action 被拒且列出可用值", e and ("remove_node" in t), t[:80])
e, t, _ = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": 5, "confirm": True})
rec("缺 attr_name 被拒", e and ("attr_name" in t), t[:80])

print('\n== ⑧ pierce 差异(如实记录) ==')
treeA, _ = enumerate_dom(6, pierce=False)
treeB, _ = enumerate_dom(6, pierce=True)
def count_nodes(n):
    if not isinstance(n, dict):
        return 0
    return 1 + sum(count_nodes(c) for c in (n.get("children") or [])) + sum(count_nodes(c) for c in (n.get("shadowRoots") or []))
na, nb = count_nodes(treeA), count_nodes(treeB)
has_shadow_a = find_node(treeA, lambda n: attrs_of(n).get("id") == "shadowInner") is not None
has_shadow_b = find_node(treeB, lambda n: attrs_of(n).get("id") == "shadowInner") is not None
info("pierce=false/true 节点数", "%d vs %d; 影子节点可见: %s vs %s" % (na, nb, has_shadow_a, has_shadow_b))
rec("pierce=true 至少不劣于 false(节点数不减少)", nb >= na, "%d vs %d" % (na, nb))
e, t, _ = call("browser_vip_dom_search", {"query": "ShadowSentinel", "ua_shadow": True}, to=90)
info("ua_shadow=true 预查找", t[:90])

print('\n== ⑨ 收尾健康 ==')
e, t, d = call("browser_execute_js", {"code": "1+1"})
rec("execute_js 正常", (not e) and d < 1.0, "%.2fs" % d)
e, t, _ = call("browser_status", {})
rec("browser_status 可用", (not e), "")

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过 (INFO %d 条)' % (len(RES) - len(bad), len(RES), len(INFO)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
