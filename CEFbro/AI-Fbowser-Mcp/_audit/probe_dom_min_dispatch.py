# -*- coding: utf-8 -*-
r"""最后一个假设: 工具路径的节点编辑之所以挂住, 是 `执行CDP并同步等待` 的**额外动作**(自救/补域/删旧结果)
与 DOM 命令不合; 换成"派发 + 直接同步等待"这一对最小原语是否就好?

对照(同一实例, 顺序执行):
  A 工具路径: browser_vip_dom_node_edit remove_attr
  B 最小原语: 先 browser_cdp_call 派发 DOM.removeAttribute(带 browser_id?) -> 其实 browser_cdp_call 就是
    `执行CDP命令` + 外层同步等待。这里改用 **browser_cdp_call** 直接调 DOM 命令(它已被证明可用),
    并逐次量 execute_js。
若 B 组健康而 A 组挂住 ⇒ 把 node_edit 改成"复用 browser_cdp_call 那条通道"(即派发+外层等待)即可。

用法: py -3 _audit\probe_dom_min_dispatch.py
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


def health(tag):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    print('   %-26s execute_js %.2fs %s' % (tag, d, 'OK' if d < 1 else '慢/坏'))
    return d


def node_id(txt, want):
    try:
        o = json.loads(txt)
    except Exception:
        return 0
    for _ in range(4):
        if isinstance(o, dict) and "root" in o:
            o = o["root"]
            break
        o = o.get("data") if isinstance(o, dict) else None
    def find(n):
        if not isinstance(n, dict):
            return None
        a = n.get("attributes") or []
        at = {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2)} if isinstance(a, list) else {}
        if at.get("id") == want:
            return n
        for c in (n.get("children") or []):
            r = find(c)
            if r:
                return r
        return None
    n = find(o)
    return n.get("nodeId") if n else 0


print('===== B 组: 用 browser_cdp_call 直调 DOM 编辑命令(无 shadow root 页面) =====')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?md=%d" % int(time.time())})
call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.id='p1';d.setAttribute('data-x','1');document.body.appendChild(d);'ok'"})
health('基线')

e, t, d = call("browser_cdp_call", {"method": "DOM.enable", "params": "{}"}, to=30)
print('   DOM.enable: %.2fs' % d)
e, t, d = call("browser_cdp_call", {"method": "DOM.getDocument", "params": "{\"depth\":-1,\"pierce\":false}"}, to=60)
nid = node_id(t, 'p1')
print('   getDocument: %.2fs nodeId=%s' % (d, nid))
health('getDocument 后')

if nid:
    e, t, d = call("browser_cdp_call", {"method": "DOM.removeAttribute",
                                        "params": json.dumps({"nodeId": nid, "name": "data-x"})}, to=60)
    print('   removeAttribute(裸): %.2fs isError=%s %s' % (d, e, t[:80]))
    health('removeAttribute 后')
    e2, t2, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1').getAttribute('data-x'))"})
    print('   页面侧 getAttribute -> %s' % t2[:60])
    e, t, d = call("browser_cdp_call", {"method": "DOM.removeNode", "params": json.dumps({"nodeId": nid})}, to=60)
    print('   removeNode(裸): %.2fs isError=%s' % (d, e))
    health('removeNode 后')
    e3, t3, _ = call("browser_execute_js", {"code": "String(document.getElementById('p1')===null)"})
    print('   页面侧 getElementById===null -> %s' % t3[:60])
