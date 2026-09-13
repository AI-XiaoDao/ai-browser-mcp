# -*- coding: utf-8 -*-
r"""第142轮最终验收: DOM 族(CDP 路线 + 影子树安全闸门)。

已知实测结论(本轮):
  · 类库"开发者DOM"路线会打死 CDP 命令通道 ⇒ 已改默认走 CDP;
  · CDP `DOM.getDocument` 可重复使用且无害(3 次, 每次之后 execute_js 0.03s);
  · **含 shadow root 的页面**: 引用 nodeId 的 DOM 编辑会挂住并打死通道 ⇒ 工具必须先检测再拒绝。

本脚本判据:
  ① 普通页面(无影子树): 枚举 → 得 nodeId; 编辑(remove_attr/set_attr/remove_node)**同步生效**且可回读;
     每次编辑后 `execute_js` 仍 0.03s 级(**整段不被毒化**);
  ② 含影子树页面: `browser_vip_dom_node_edit` **明确拒绝**(可行动文案, 指向 browser_execute_js),
     且**没有**执行任何破坏性命令 —— 之后 `execute_js` 依然 0.03s 级;
  ③ `pierce=true` 能看到影子树内容(false 时看不到);
  ④ 收尾健康。

用法: py -3 _audit\verify_round142c.py
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


def enum(depth=4, pierce=False):
    e, t, d = call("browser_vip_dom_get_document", {"depth": depth, "pierce": pierce}, to=90)
    return (None if e else root_of(t)), d


def health(tag, limit=1.0):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    ok = (not e) and d < limit
    rec(tag, ok, "%.2fs" % d)
    return ok


PLAIN_JS = ("var d=document.createElement('div');d.id='mcpProbeDiv';d.className='probe-cls';"
            "d.setAttribute('data-probe','yes');d.innerHTML='<span id=mcpProbeSpan>x</span>';"
            "document.body.appendChild(d);'ok'")
SHADOW_JS = ("var d=document.createElement('div');d.id='plainDiv';d.setAttribute('data-x','1');"
             "document.body.appendChild(d);"
             "var h=document.createElement('div');h.id='host1';"
             "var r=h.attachShadow({mode:'open'});r.innerHTML='<span id=shInner>SHADOW</span>';"
             "document.body.appendChild(h);'ok'")

print('== 干净实例: 普通页面(无影子树) ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?d142c=%d" % int(time.time())})
call("browser_execute_js", {"code": PLAIN_JS})
health("①基线 execute_js 0.03s 级")

root, d = enum()
div = find(root, lambda n: attrs(n).get("id") == "mcpProbeDiv")
rec("①枚举并定位 #mcpProbeDiv", div is not None,
    "%.2fs nodeId=%s attrs=%s" % (d, div.get("nodeId") if div else None, attrs(div) if div else None))
nid = div.get("nodeId") if div else 0

if nid:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": nid, "attr_name": "data-probe", "confirm": True})
    rec("①remove_attr 成功", not e, "%.2fs" % d)
    health("①remove_attr 后 execute_js 仍快")
    root2, _ = enum()
    div2 = find(root2, lambda n: attrs(n).get("id") == "mcpProbeDiv")
    rec("①回读: data-probe 已消失", div2 is not None and "data-probe" not in attrs(div2),
        "attrs=%s" % (attrs(div2) if div2 else None))
    nid = (div2.get("nodeId") if div2 else nid) or nid

    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "set_attr", "node_id": nid, "attr_name": "data-probe", "value": "edited", "confirm": True})
    rec("①set_attr 成功", not e, "%.2fs %s" % (d, t[:50]))
    health("①set_attr 后 execute_js 仍快")
    root3, _ = enum()
    div3 = find(root3, lambda n: attrs(n).get("id") == "mcpProbeDiv")
    rec("①回读: data-probe=edited", div3 is not None and attrs(div3).get("data-probe") == "edited",
        "attrs=%s" % (attrs(div3) if div3 else None))
    nid = (div3.get("nodeId") if div3 else nid) or nid

    e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_node", "node_id": nid, "confirm": True})
    rec("①remove_node 成功", not e, "%.2fs %s" % (d, t[:50]))
    health("①remove_node 后 execute_js 仍快")
    e5, t5, _ = call("browser_execute_js", {"code": "String(document.getElementById('mcpProbeDiv')===null)"})
    rec("①页面侧: 节点已删除", "true" in t5, t5[:60])
else:
    for tag in ("①remove_attr 成功", "①remove_attr 后 execute_js 仍快", "①回读: data-probe 已消失",
                "①set_attr 成功", "①set_attr 后 execute_js 仍快", "①回读: data-probe=edited",
                "①remove_node 成功", "①remove_node 后 execute_js 仍快", "①页面侧: 节点已删除"):
        rec(tag, False, "未取到 nodeId")

print('\n== 含影子树的页面: 必须**拒绝**且不毒化会话 ==')
call("browser_execute_js", {"code": SHADOW_JS})
call("browser_navigate", {"url": "https://example.com/?d142c2=%d" % int(time.time())})
call("browser_execute_js", {"code": SHADOW_JS})
root_s, _ = enum(6, pierce=True)
plain = find(root_s, lambda n: attrs(n).get("id") == "plainDiv")
rec("②影子树页面里仍能定位普通节点(只读枚举可用)", plain is not None, "nodeId=%s" % (plain.get("nodeId") if plain else None))
sh = find(root_s, lambda n: attrs(n).get("id") == "shInner")
rec("③pierce=true 能看到影子树内容(#shInner)", sh is not None, "nodeId=%s" % (sh.get("nodeId") if sh else None))
root_np, _ = enum(6, pierce=False)
sh_np = find(root_np, lambda n: attrs(n).get("id") == "shInner")
info("pierce=false 时是否可见影子节点", "可见" if sh_np else "不可见(符合预期)")

if plain:
    e, t, d = call("browser_vip_dom_node_edit",
                   {"action": "remove_attr", "node_id": plain.get("nodeId"), "attr_name": "data-x", "confirm": True})
    rec("②含影子树页面 → 明确拒绝(可行动)", e and ("shadow root" in t) and ("browser_execute_js" in t),
        "%.2fs %s" % (d, t[:90]))
    health("②拒绝之后 execute_js 仍 0.03s 级(**未被毒化**)")
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('plainDiv').getAttribute('data-x'))"})
    rec("②页面未被改动(属性仍在)", "1" in t2, t2[:60])
else:
    rec("②含影子树页面 → 明确拒绝(可行动)", False, "未定位到 plainDiv")
    rec("②拒绝之后 execute_js 仍 0.03s 级(**未被毒化**)", False, "")

print('\n== 收尾 ==')
health("④收尾 execute_js 0.03s 级")
e, t, d = call("browser_status", {})
rec("④browser_status 可用", (not e), "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过 (INFO %d 条)' % (len(RES) - len(bad), len(RES), len(INFO)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
