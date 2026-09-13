# -*- coding: utf-8 -*-
"""补验: browser_frame_by_id 用 browser_get_frames 回包里**真实的 id 字段**取值, 必须 found:true。"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []


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


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


call("browser_navigate", {"url": "https://example.com/?fbid=1", "wait_for_load": True})
call("browser_execute_js", {"code": "document.body.insertAdjacentHTML('beforeend','<iframe id=mf2 srcdoc=\"<p>inner</p>\"></iframe>')"})
time.sleep(1.0)
e, t = call("browser_get_frames")
frames = []
try:
    frames = json.loads(t).get("frames") or []
except Exception as ex:
    print('   解析异常 %r 原文 %s' % (ex, t[:200]))
print('   frames = %s' % json.dumps(frames, ensure_ascii=False)[:300])
sub = next((f for f in frames if f.get('is_main') is False), None)
main = next((f for f in frames if f.get('is_main') is True), None)

if sub:
    e, t = call("browser_frame_by_id", {"frame_id": sub['id']})
    rec('用真实 id(子框架) -> found:true + url + is_main:false',
        (not e) and '"found":true' in t and '"is_main":false' in t, t)
    e, t = call("browser_frame_by_id", {"id": sub['id']})
    rec('兼容字段名 id -> 同样 found:true', (not e) and '"found":true' in t, t)
else:
    rec('子框架用例', False, '没找到子框架(iframe 可能未生成)')
if main:
    e, t = call("browser_frame_by_id", {"frame_id": main['id']})
    rec('主框架 -> found:true + is_main:true', (not e) and '"is_main":true' in t, t)

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
