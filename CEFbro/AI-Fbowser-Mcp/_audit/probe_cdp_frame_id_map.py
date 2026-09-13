# -*- coding: utf-8 -*-
r"""接着查: CDP 眼里的 frameId 与 CEF 的框架标识(`6-XXXX`)是不是同一套?

`Page.createIsolatedWorld {frameId: "6-EDD3…"}` 回 "No frame for given id found" ⇒ 不是同一套。
本探针: 取 Page.getFrameTree, 打印 CDP 侧的 frame id/url/name, 再拿**CDP 的 id** 试一次
createIsolatedWorld + 在上下文里求值 —— 若成功, 则"按 iframe 求值"这条路可行, 只是需要一层 id 映射。
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


call("browser_navigate", {"url": "https://example.com/?ftree=%d" % int(time.time()),
                          "wait_for_load": True})
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"f1\" name=\"mcpfr3\" srcdoc=\"<p id=inner>FROM_IFRAME3</p>\"></iframe>');'ok'"})
time.sleep(1.0)

print('== A. CEF 侧框架清单(browser_get_frames) ==')
e, t = call("browser_get_frames", {})
cef_ids = []
try:
    fr = json.loads(t).get("frames") or []
    for f in fr:
        print('   cef id=%-40s name=%-30s main=%s' % (f.get('id'), (f.get('name') or '')[:30], f.get('is_main')))
        cef_ids.append(f.get('id'))
except Exception as ex:
    print('   解析失败 %r 原文 %s' % (ex, t[:200]))

print('\n== B. CDP 侧 getFrameTree ==')
e2, t2 = call("browser_cdp_call", {"method": "Page.getFrameTree", "params": {}}, 40)
flat = t2.replace('\\"', '"')
print('   %s' % flat[:600])
cdp_ids = re.findall(r'"id":\s*"([^"]+)"', flat)
print('   CDP 侧 id: %s' % cdp_ids[:6])
print('   与 CEF 侧是否有交集: %s' % (set(cdp_ids) & set(cef_ids) or '无'))

print('\n== C. 用 **CDP 的 id** 试 createIsolatedWorld ==')
# 找一个非主框架的 CDP id: getFrameTree 里 childFrames 下的 id
child = re.findall(r'"childFrames".*?"id":\s*"([^"]+)"', flat, re.S)
target = None
for c in cdp_ids:
    if c not in child:
        pass
if child:
    target = child[-1]
if not target and cdp_ids:
    target = cdp_ids[-1]
print('   目标 CDP frameId = %r' % target)
if target:
    e3, t3 = call("browser_cdp_call", {"method": "Page.createIsolatedWorld",
                                       "params": {"frameId": target, "worldName": "mcp_probe2",
                                                  "grantUniversalAccess": True}}, 40)
    print('   createIsolatedWorld: isError=%s %s' % (e3, t3[:240]))
    m = re.search(r'"executionContextId":\s*(\d+)', t3.replace('\\"', '"'))
    if m:
        ctx = int(m.group(1))
        e4, t4 = call("browser_cdp_call", {"method": "Runtime.evaluate",
                                           "params": {"expression":
                                                      "(function(){var e=document.getElementById('inner');"
                                                      "return 'CTX3:'+(e?e.textContent:'__NO_ELEM__')})()",
                                                      "contextId": ctx, "returnByValue": True}}, 40)
        print('   evaluate@ctx%d: isError=%s %s' % (ctx, e4, t4[:300]))
        print('   [%s] 在 iframe 上下文里读到 iframe 内部 DOM'
              % ('PASS' if 'CTX3:FROM_IFRAME3' in t4.replace('\\"', '"') else 'FAIL'))
