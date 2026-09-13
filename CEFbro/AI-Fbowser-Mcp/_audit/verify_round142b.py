# -*- coding: utf-8 -*-
r"""第142轮验收(精简版): DOM 族**能力**验证 —— 与已验证成功的裸 CDP 顺序完全一致, 不走多余调用。

修前/已知: 类库"开发者DOM"路线调一次就会让本会话 CDP 命令通道失效(之后每条 30s);
本脚本验证改走 CDP 之后: 枚举/改属性/删属性/删节点**同步生效、可回读**, 且**收尾 CDP 仍健康**。

判据(每步都用重新枚举或页面侧断言做回读):
  ① 干净实例基线 execute_js 0.03s;
  ② `browser_vip_dom_get_document depth=4` → 树里能定位 `#mcpProbeDiv`(nodeId + 属性齐全);
  ③ `remove_attr` → 重新枚举该节点属性里 `data-probe` 消失;
  ④ `set_attr`(重新枚举取最新 nodeId)→ 回读 `data-probe=edited`;
  ⑤ `remove_node`(重新枚举取最新 nodeId)→ 重新枚举找不到 **且** 页面侧 `getElementById===null` **且** 子节点也没了;
  ⑥ `pierce=false/true` 节点数差异 + 影子节点只在 true 时可见;
  ⑦ 收尾 `execute_js` 仍 0.03s 级(**不再 30s**)。

用法: py -3 _audit\verify_round142b.py
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
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


def tree_root(txt):
    """回包是 {"id":..,"success":true,"data":{"root":{...}}} —— 逐层剥到 root(探针解析也要当被测对象)。"""
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


def dump(n):
    if not isinstance(n, dict):
        return 0
    return 1 + sum(dump(c) for c in (n.get("children") or [])) + sum(dump(c) for c in (n.get("shadowRoots") or []))


def enum(depth=4, pierce=False):
    e, t, d = call("browser_vip_dom_get_document", {"depth": depth, "pierce": pierce}, to=90)
    return (None if e else tree_root(t)), t, d


PROBE_JS = ("var d=document.createElement('div');d.id='mcpProbeDiv';d.className='probe-cls';"
            "d.setAttribute('data-probe','yes');d.innerHTML='<span id=mcpProbeSpan>x</span>';"
            "document.body.appendChild(d);"
            "var h=document.createElement('div');h.id='mcpShadowHost';"
            "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shadowInner>S</span>';"
            "document.body.appendChild(h);'ok'")

loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?d142b=%d" % int(time.time())})
call("browser_execute_js", {"code": PROBE_JS})
e, t, d = call("browser_execute_js", {"code": "1+1"})
rec("①基线 execute_js 0.03s 级", (not e) and d < 1.0, "%.2fs" % d)

root, raw, d = enum()
div = find(root, lambda n: attrs(n).get("id") == "mcpProbeDiv")
rec("②枚举成功且能定位 #mcpProbeDiv(nodeId+属性)", div is not None,
    "%.2fs nodeId=%s attrs=%s" % (d, div.get("nodeId") if div else None, attrs(div) if div else None))
nid = div.get("nodeId") if div else 0

if nid:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": nid, "attr_name": "data-probe", "confirm": True})
    rec("③remove_attr 成功", not e, "%.2fs" % d)
    root2, _, _ = enum()
    div2 = find(root2, lambda n: attrs(n).get("id") == "mcpProbeDiv")
    rec("③回读: data-probe 已消失", div2 is not None and "data-probe" not in attrs(div2),
        "attrs=%s" % (attrs(div2) if div2 else None))
    nid = (div2.get("nodeId") if div2 else nid) or nid

    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "set_attr", "node_id": nid, "attr_name": "data-probe", "value": "edited", "confirm": True})
    rec("④set_attr 成功", not e, "%.2fs %s" % (d, t[:60]))
    root3, _, _ = enum()
    div3 = find(root3, lambda n: attrs(n).get("id") == "mcpProbeDiv")
    rec("④回读: data-probe=edited", div3 is not None and attrs(div3).get("data-probe") == "edited",
        "attrs=%s" % (attrs(div3) if div3 else None))
    nid = (div3.get("nodeId") if div3 else nid) or nid

    e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": nid, "confirm": True})
    rec("⑤remove_node 成功", not e, "%.2fs %s" % (d, t[:60]))
    root4, _, _ = enum()
    gone = find(root4, lambda n: attrs(n).get("id") == "mcpProbeDiv")
    rec("⑤回读: 节点已从树里消失", gone is None, "仍找到=%s" % (gone is not None))
    e5, t5, _ = call("browser_execute_js", {"code": "String(document.getElementById('mcpProbeDiv')===null)"})
    rec("⑤页面侧: getElementById 为 null", "true" in t5, t5[:60])
    e6, t6, _ = call("browser_execute_js", {"code": "String(document.getElementById('mcpProbeSpan')===null)"})
    rec("⑤子节点一并删除(span 也没了)", "true" in t6, t6[:60])
else:
    for tag in ("③remove_attr 成功", "③回读: data-probe 已消失", "④set_attr 成功", "④回读: data-probe=edited",
                "⑤remove_node 成功", "⑤回读: 节点已从树里消失", "⑤页面侧: getElementById 为 null",
                "⑤子节点一并删除(span 也没了)"):
        rec(tag, False, "未取到 nodeId")

r_f, _, _ = enum(6, pierce=False)
r_t, _, _ = enum(6, pierce=True)
nf, nt = dump(r_f), dump(r_t)
has_f = find(r_f, lambda n: attrs(n).get("id") == "shadowInner") is not None
has_t = find(r_t, lambda n: attrs(n).get("id") == "shadowInner") is not None
rec("⑥pierce=true 能看见影子节点(false 时看不见)", has_t and not has_f,
    "节点数 %d vs %d; 影子节点 %s vs %s" % (nf, nt, has_f, has_t))

e, t, d = call("browser_execute_js", {"code": "9+9"})
rec("⑦收尾 execute_js 仍 0.03s 级(**不再 30s**)", (not e) and d < 1.0, "%.2fs" % d)
e, t, d = call("browser_status", {})
rec("⑦browser_status 可用", (not e), "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
