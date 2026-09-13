# -*- coding: utf-8 -*-
r"""判定: 跨域(OOPIF)框架在 CDP 侧框架树里到底有没有/顺序是否与 CEF 清单一致。

结论决定"按名/按 id 解析 OOPIF 失败"的根因:
  · CDP 树里**没有**该框架      -> CDP 隔离世界路线天然够不到 OOPIF(需换原生路线, 应如实说明)
  · CDP 树里**有**但顺序不同    -> 是"按序号对齐"的算法问题, 应改成按 URL/其它键匹配
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
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


call("browser_navigate", {"url": "https://example.com/?oopif=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.6)
call("browser_execute_js", {"code":
     "(function(){document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"s1\" name=\"samefr\" srcdoc=\"<b>x</b>\"></iframe>');"
     "var f=document.createElement('iframe');f.id='x1';f.name='xofr';f.src='https://example.org/';"
     "document.body.appendChild(f);return 'ok'})()"})
time.sleep(3.0)

e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
print('CEF 清单(%d):' % len(frames))
for f in frames:
    print('   %-42s name=%-10r main=%s url=%s' % (f.get('id'), f.get('name'), f.get('is_main'),
                                                  str(f.get('url'))[:60]))

e2, t2 = call("browser_cdp_call", {"method": "Page.getFrameTree", "params": "{}"})
raw = t2
print('\nCDP Page.getFrameTree 原始(截断): %s' % raw[:600])
ids = re.findall(r'"id"\s*:\s*"([0-9A-Fa-f]+)"', raw)
urls = re.findall(r'"url"\s*:\s*"([^"]*)"', raw)
print('\nCDP 顺序 id (%d):' % len(ids))
for i, x in enumerate(ids):
    print('   %-42s url=%s' % (x, urls[i] if i < len(urls) else '?'))

print('\n判读:')
cef_ids = [f.get('id') for f in frames]
print('   CEF 条数=%d  CDP 条数=%d' % (len(cef_ids), len(ids)))
print('   CEF 里带 8- 前缀(OOPIF)的 id: %s' % [x for x in cef_ids if x.startswith('8-')])
print('   同序假设是否可能成立: %s' % ('否(条数不同)' if len(cef_ids) != len(ids) else '条数相同, 需逐项看 url'))
