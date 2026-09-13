# -*- coding: utf-8 -*-
r"""G1b 前置探针: `browser_get_frames`(CEF 侧) 与 `Page.getFrameTree`(CDP 侧) 的**顺序/名字**是否可对应?

上一轮已证: ① CEF id(`6-…`)与 CDP frameId 不是同一套; ② 用 CDP frameId 走
`Page.createIsolatedWorld` + `Runtime.evaluate {contextId}` 能读到 iframe 内部。
本探针要回答"怎么把用户给的 frame_id(CEF id 或框架名)映射成 CDP frameId" —— 只有顺序或名字可对应,
才能在 `browser_execute_js {frame_id}` 里自动映射。
造 3 个 iframe(两个有名、一个匿名, 其中一个**嵌套**), 然后逐项对照。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


call("browser_navigate", {"url": "https://example.com/?g1b=%d" % int(time.time()),
                          "wait_for_load": True})
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=a name=frameA srcdoc=\"<p id=ia>A</p>\"></iframe>"
     "<iframe id=b srcdoc=\"<p id=ib>B</p>\"></iframe>"
     "<iframe id=c name=frameC srcdoc=\"<iframe id=c1 name=frameC1 srcdoc=&quot;<p id=ic>C1</p>&quot;></iframe>\"></iframe>');'ok'"})
time.sleep(1.5)

print('== A. CEF 侧(browser_get_frames) ==')
_, t = call("browser_get_frames", {})
cef = []
try:
    cef = json.loads(t).get("frames") or []
except Exception as ex:
    print('   解析失败 %r' % ex)
for i, f in enumerate(cef):
    print('   [%d] id=%s name=%r main=%s' % (i, f.get('id'), (f.get('name') or '')[:44], f.get('is_main')))

print('\n== B. CDP 侧(Page.getFrameTree, 树序展平) ==')
_, t2 = call("browser_cdp_call", {"method": "Page.getFrameTree", "params": {}}, 40)
flat = t2.replace('\\"', '"')
tree = None
try:
    tree = json.loads(flat)
    if isinstance(tree, dict) and 'data' in tree:
        tree = tree['data']
except Exception as ex:
    print('   解析失败 %r 原文 %s' % (ex, flat[:200]))


def walk(node, out, depth=0):
    fr = (node or {}).get('frame') or {}
    out.append((depth, fr.get('id'), fr.get('name'), fr.get('url'), fr.get('parentId')))
    for ch in (node or {}).get('childFrames') or []:
        walk(ch, out, depth + 1)
    return out


cdp = walk((tree or {}).get('frameTree') or tree or {}, [])
for i, (d, cid, nm, url, pid) in enumerate(cdp):
    print('   [%d] depth=%d id=%s name=%r url=%s' % (i, d, cid, (nm or '')[:24], (url or '')[:40]))

print('\n== C. 对照 ==')
print('   CEF 框架数=%d, CDP 框架数=%d' % (len(cef), len(cdp)))
print('   CEF 名字: %s' % [ (f.get('name') or '')[:14] for f in cef ])
print('   CDP 名字: %s' % [ (c[2] or '')[:14] for c in cdp ])
same_order = (len(cef) == len(cdp))
print('   数量是否一致: %s' % same_order)

print('\n== D. 用 CDP 第 4 个框架(索引3)试隔离世界求值 ==')
if len(cdp) > 3:
    cid = cdp[3][1]
    e3, t3 = call("browser_cdp_call", {"method": "Page.createIsolatedWorld",
                                       "params": {"frameId": cid, "worldName": "mcp_g1b",
                                                  "grantUniversalAccess": True}}, 40)
    print('   createIsolatedWorld(%s): %s' % (cid[:12], t3[:140]))
    m = re.search(r'"executionContextId":\s*(\d+)', t3.replace('\\"', '"'))
    if m:
        ctx = int(m.group(1))
        e4, t4 = call("browser_cdp_call", {"method": "Runtime.evaluate",
                                           "params": {"expression":
                                                      "(function(){var e=document.getElementById('ic');"
                                                      "return 'G1B:'+(e?e.textContent:'__NO_ELEM__')})()",
                                                      "contextId": ctx, "returnByValue": True}}, 40)
        print('   evaluate@%d: %s' % (ctx, t4[:220]))
        print('   [%s] 索引映射成立(读到嵌套 iframe 里的 C1)'
              % ('PASS' if 'G1B:C1' in t4.replace('\\"', '"') else 'FAIL'))
