# -*- coding: utf-8 -*-
r"""复现 fastcheck 第⑩臂的回归: browser_fill_set_value {frame_id} 写到了**主框架**。

打印框架清单与原始回包, 判定是"框架解析失败后静默写主框架"还是"探针取错了框架"。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


def js(expr, **kw):
    a = {"code": expr}
    a.update(kw)
    e, t = call("browser_execute_js", a)
    return ('ERR:' if e else '') + val(t)


call("browser_navigate", {"url": "https://example.com/?repro=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.5)
js("document.body.insertAdjacentHTML('beforeend',"
   "'<input id=\"g1tgt\" value=\"MAIN\"><iframe id=\"g1fr\" name=\"mcpfcheck\" "
   "srcdoc=\"<input id=g1tgt value=IFRAME>\"></iframe>');'ok'")
time.sleep(1.2)

e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
print('框架清单(%d):' % len(frames))
for f in frames:
    print('   id=%-42s name=%-12r main=%s' % (f.get('id'), f.get('name'), f.get('is_main')))
sub = next((f for f in frames if f.get('is_main') is False), None)
fid = (sub or {}).get('id')
print('取到的子框架 id=%r' % fid)

print('\n-- 按 id 写 --')
e, t = call("browser_fill_set_value", {"selector": "#g1tgt", "value": "IN_FRAME", "frame_id": fid})
print('   isError=%s 回包=%s' % (e, val(t)[:200]))
iv = js("(function(){var f=document.getElementById('g1fr');var e=f&&f.contentDocument&&"
        "f.contentDocument.querySelector('#g1tgt');return e?e.value:'__NO_IFRAME__'})()")
mv = js("document.getElementById('g1tgt').value")
print('   写后: iframe=%r 主=%r' % (iv, mv))
print('   判读: %s' % ('OK' if (iv == 'IN_FRAME' and mv == 'MAIN') else
                       '★写到了错误的框架(主框架被改)' if mv == 'IN_FRAME' else '★两边都没写成功'))

print('\n-- 重置后按**名**写 --')
js("document.getElementById('g1tgt').value='MAIN';"
   "(function(){var f=document.getElementById('g1fr');"
   "f.contentDocument.querySelector('#g1tgt').value='IFRAME'})();'ok'")
e, t = call("browser_fill_set_value", {"selector": "#g1tgt", "value": "BY_NAME", "frame_id": 'mcpfcheck'})
print('   isError=%s 回包=%s' % (e, val(t)[:200]))
iv = js("(function(){var f=document.getElementById('g1fr');var e=f&&f.contentDocument&&"
        "f.contentDocument.querySelector('#g1tgt');return e?e.value:'__NO_IFRAME__'})()")
mv = js("document.getElementById('g1tgt').value")
print('   写后: iframe=%r 主=%r' % (iv, mv))

print('\n-- 对照: 前置校验(带 frame_id) 自身的回包 --')
e, t = call("browser_fill_exists", {"selector": "#g1tgt", "frame_id": fid})
print('   browser_fill_exists -> isError=%s %s' % (e, val(t)[:200]))
e, t = call("browser_dom_query", {"selector": "#g1tgt", "attribute": "value", "frame_id": fid})
print('   browser_dom_query(带 attribute) -> isError=%s %s' % (e, val(t)[:200]))
