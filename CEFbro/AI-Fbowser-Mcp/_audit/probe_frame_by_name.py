# -*- coding: utf-8 -*-
r"""定位: 跨域 iframe 的**按名**寻址为何失败(而按 id 成功)。

同时量测: 解析框架执行上下文(CDP 路径, 供读取类工具) 与 解析框架对象/解析填表框架(原生路径) 对同一目标名的解析结果。
"""
import json
import os
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
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


call("browser_navigate", {"url": "https://example.com/?nm=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.6)
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"nfr\" name=\"namefr\" src=\"https://example.org/\"></iframe>');'ok'"})
time.sleep(3.0)

e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
print('框架清单:')
for f in frames:
    print('   id=%-40s name=%-14r main=%s' % (f.get('id'), f.get('name'), f.get('is_main')))
tgt = next((f for f in frames if f.get('name') == 'namefr'), None)
print('目标(跨域) id=%r' % ((tgt or {}).get('id')))

cases = [
    ('按 id + dom_get_html', 'browser_dom_get_html', {"selector": "h1", "frame_id": (tgt or {}).get('id')}),
    ('按名 + dom_get_html', 'browser_dom_get_html', {"selector": "h1", "frame_id": 'namefr'}),
    ('按名 + execute_js(CDP隔离)', 'browser_execute_js', {"code": "document.title", "frame_id": 'namefr'}),
    ('按 id + execute_js(CDP隔离)', 'browser_execute_js', {"code": "document.title", "frame_id": (tgt or {}).get('id')}),
    ('按名 + dom_query(带attribute)', 'browser_dom_query',
     {"selector": "h1", "attribute": "class", "frame_id": 'namefr'}),
]
for label, tool, args in cases:
    e, t = call(tool, args)
    print('   [%s] %-26s isError=%s -> %s' % ('ERR' if e else 'ok ', label, e, val(t)[:150]))
