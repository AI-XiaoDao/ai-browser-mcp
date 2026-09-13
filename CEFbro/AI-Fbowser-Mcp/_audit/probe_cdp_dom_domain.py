# -*- coding: utf-8 -*-
r"""关键实验: **CDP 自己的 DOM 域**能否替代类库"开发者DOM"(后者实测会让我们的 CDP 命令通道失效)?

背景(本轮实测): 调一次 `browser_vip_dom_get_document`(内部 `开发者DOM.启用("all")`)之后,
所有 CDP 命令 30s 才靠原生回退返回 —— 与类库截图路线同一类副作用。
而 CDP 自带 `DOM.getDocument / DOM.setAttributeValue / DOM.removeNode / DOM.removeAttribute`,
若它们在**本机可用且无害**, 整个 DOM 族就该改走 CDP。

本探针在**同一实例**内按顺序量:
  ① 基线 execute_js; ② `DOM.getDocument`; ③ 定位 `#mcpProbeDiv` 的 nodeId;
  ④ `DOM.setAttributeValue` → 重新 getDocument 回读; ⑤ `DOM.removeAttribute` → 回读;
  ⑥ `DOM.removeNode` → 重新 getDocument + 页面侧 `getElementById` 双回读;
  ⑦ 收尾 execute_js(通道是否仍 0.03s)。

用法: py -3 _audit\probe_cdp_dom_domain.py
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
_rid = [4400]


def call(n, a=None, to=90, rid=None):
    if rid is None:
        _rid[0] += 1
        rid = _rid[0]
    b = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0, rid
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0, rid


def cdp(method, params=None, to=60):
    """裸 CDP 调用: 派发 + 从回包/mcp_result 取结果(载荷可能在 result 或 message 里)。"""
    e, t, d, rid = call("browser_cdp_call", {"method": method,
                                             "params": json.dumps(params or {}, ensure_ascii=False)}, to=to)
    if e:
        return None, t
    # 同步回包优先
    obj = try_json(t)
    if obj is not None and ("root" in obj or "nodeId" in obj):
        return obj, ""
    e2, t2, _, _ = call("mcp_result", {"request_id": str(rid)}, to=60)
    obj2 = try_json(t2)
    if isinstance(obj2, dict):
        inner = obj2.get("message") or obj2.get("result")
        if isinstance(inner, str):
            obj3 = try_json(inner)
            if obj3 is not None:
                return obj3, ""
        return obj2, ""
    return None, t2[:150]


def try_json(s):
    try:
        return json.loads(s)
    except Exception:
        return None


def find(node, pred):
    if not isinstance(node, dict):
        return None
    if pred(node):
        return node
    for k in ("children", "shadowRoots"):
        for ch in (node.get(k) or []):
            r = find(ch, pred)
            if r:
                return r
    return None


def attrs(node):
    a = (node or {}).get("attributes") or []
    return {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?cdpdom=%d" % int(time.time())})
call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.id='mcpProbeDiv';d.setAttribute('data-probe','yes');"
    "d.innerHTML='<span id=mcpProbeSpan>x</span>';document.body.appendChild(d);'ok'"})
e, t, d, _ = call("browser_execute_js", {"code": "1+1"})
print('①基线 execute_js: isError=%s %.2fs' % (e, d))

print('\n② DOM.getDocument(depth=4, pierce=true)')
tree, err = cdp("DOM.getDocument", {"depth": 4, "pierce": True})
root = (tree or {}).get("root") if isinstance(tree, dict) else None
print('   结果: %s' % ('有 root' if root else ('失败/空: %s' % (err or str(tree)[:120]))))
div = find(root, lambda n: attrs(n).get("id") == "mcpProbeDiv") if root else None
print('   定位 #mcpProbeDiv: %s' % ("nodeId=%s attrs=%s" % (div.get("nodeId"), attrs(div)) if div else "未找到"))
nid = div.get("nodeId") if div else 0

if nid:
    print('\n③ DOM.setAttributeValue(data-probe=edited)')
    r, err = cdp("DOM.setAttributeValue", {"nodeId": nid, "name": "data-probe", "value": "edited"})
    print('   回包: %s' % (str(r)[:100] if r is not None else err))
    tree2, _ = cdp("DOM.getDocument", {"depth": 4, "pierce": True})
    div2 = find((tree2 or {}).get("root"), lambda n: attrs(n).get("id") == "mcpProbeDiv")
    print('   回读 attrs=%s' % (attrs(div2) if div2 else None))
    nid = div2.get("nodeId") if div2 else nid

    print('\n④ DOM.removeAttribute(data-probe)')
    r, err = cdp("DOM.removeAttribute", {"nodeId": nid, "name": "data-probe"})
    print('   回包: %s' % (str(r)[:100] if r is not None else err))
    tree3, _ = cdp("DOM.getDocument", {"depth": 4, "pierce": True})
    div3 = find((tree3 or {}).get("root"), lambda n: attrs(n).get("id") == "mcpProbeDiv")
    print('   回读 attrs=%s' % (attrs(div3) if div3 else None))
    nid = div3.get("nodeId") if div3 else nid

    print('\n⑤ DOM.removeNode')
    r, err = cdp("DOM.removeNode", {"nodeId": nid})
    print('   回包: %s' % (str(r)[:100] if r is not None else err))
    tree4, _ = cdp("DOM.getDocument", {"depth": 4, "pierce": True})
    div4 = find((tree4 or {}).get("root"), lambda n: attrs(n).get("id") == "mcpProbeDiv")
    print('   重新枚举: %s' % ('仍在' if div4 else '已消失'))
    e5, t5, _, _ = call("browser_execute_js", {"code": "String(document.getElementById('mcpProbeDiv')===null)"})
    print('   页面侧 getElementById: %s' % t5[:60])

print('\n⑥ 收尾 execute_js(通道是否仍健康)')
e, t, d, _ = call("browser_execute_js", {"code": "2+2"})
print('   isError=%s %.2fs %s' % (e, d, t[:50]))
