# -*- coding: utf-8 -*-
r"""决定性小实验: 工具路径的 CDP DOM 命令为何会在**第二次**之后把通道弄死? 试 `DOM.enable` 是否解决。

背景: 裸 `browser_cdp_call` 顺序(getDocument→setAttributeValue→getDocument→removeAttribute→getDocument→removeNode→getDocument)
在**同一实例**内全程健康(收尾 execute_js 0.03s); 而工具路径(执行CDP并同步等待)在 `remove_attr` 成功之后,
下一次 getDocument 就再也拿不到结果, 且收尾 execute_js 30s+。
差别候选: ① 没有先 `DOM.enable`(CEF 未维护节点映射 ⇒ 引用 nodeId 的命令挂住) ② 等待机制。

本探针在**工具路径**上先补 `DOM.enable`, 再重复 裸路径 的成功序列。

用法: py -3 _audit\probe_dom_enable_first.py
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


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?ef=%d" % int(time.time())})
call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');"
    "document.body.appendChild(d);'ok'"})
e, t, d = call("browser_execute_js", {"code": "1+1"})
print('基线 execute_js: %.2fs' % d)

print('\n[1] 先 DOM.enable(裸 CDP)')
e, t, d = call("browser_cdp_call", {"method": "DOM.enable", "params": "{}"}, to=30)
print('    isError=%s %.2fs %s' % (e, d, t[:80]))
e, t, d = call("browser_execute_js", {"code": "2+2"})
print('    enable 后 execute_js: %.2fs %s' % (d, t[:50]))

print('\n[2] 工具路径 get_document')
e, t, d = call("browser_vip_dom_get_document", {"depth": 3}, to=60)
print('    isError=%s %.2fs len=%d' % (e, d, len(t)))
e, t, d = call("browser_execute_js", {"code": "3+3"})
print('    之后 execute_js: %.2fs %s' % (d, t[:50]))

print('\n[3] 工具路径 get_document 第二次(关键: 之前就是这一步死的)')
e, t, d = call("browser_vip_dom_get_document", {"depth": 3}, to=60)
print('    isError=%s %.2fs len=%d %s' % (e, d, len(t), t[:70]))
e, t, d = call("browser_execute_js", {"code": "4+4"})
print('    之后 execute_js: %.2fs %s' % (d, t[:50]))

print('\n[4] 工具路径 remove_attr')
nid = 0
try:
    o = json.loads(t)
    for _ in range(4):
        if isinstance(o, dict) and "root" in o:
            break
        o = o.get("data") if isinstance(o, dict) else None
    root = o.get("root") if isinstance(o, dict) else None
    def find(n):
        if not isinstance(n, dict):
            return None
        a = n.get("attributes") or []
        at = {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}
        if at.get("id") == "p1":
            return n
        for c in (n.get("children") or []):
            r = find(c)
            if r:
                return r
        return None
    node = find(root)
    nid = node.get("nodeId") if node else 0
except Exception as ex:
    print('    解析失败: %r' % (ex,))
print('    nodeId=%s' % nid)
if nid:
    e, t, d = call("browser_vip_dom_node_edit", {"action": "remove_attr", "node_id": nid, "attr_name": "data-x", "confirm": True}, to=60)
    print('    remove_attr isError=%s %.2fs %s' % (e, d, t[:80]))
    e, t, d = call("browser_execute_js", {"code": "5+5"})
    print('    之后 execute_js: %.2fs %s' % (d, t[:50]))
    print('\n[5] 工具路径 get_document 第三次')
    e, t, d = call("browser_vip_dom_get_document", {"depth": 3}, to=60)
    print('    isError=%s %.2fs len=%d' % (e, d, len(t)))
    e, t, d = call("browser_execute_js", {"code": "6+6"})
    print('    之后 execute_js: %.2fs %s' % (d, t[:50]))
