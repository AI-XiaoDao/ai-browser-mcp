# -*- coding: utf-8 -*-
r"""判定 CEF 框架清单的**顺序/配对**真相:
  H1: 取框架ID() 的顺序不是"主框架在前"  -> 按序号推断 is_main / 按序号对齐都会错
  H2: 取框架ID() 顺序正常, 但 取框架名称() 的顺序与之**不平行** -> browser_get_frames 的 name 字段配错

判别手段: 对每个 id 用**原生世界**执行 location.href(该框架真实身份), 与清单里配对的 name 对照。
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


def survey(tag):
    e, t = call("browser_get_frames", {})
    frames = json.loads(t).get("frames") or []
    print('\n===== %s: browser_get_frames 清单(%d) =====' % (tag, len(frames)))
    for i, f in enumerate(frames):
        fid = f.get('id')
        # 身份判定: 在**该框架自己的原生世界**里读它的 href(跨域也能读到自身的 href)
        e2, t2 = call("browser_execute_js", {"code": "location.href", "frame_id": fid, "world": "main"})
        href = val(t2) if not e2 else ('ERR:' + val(t2)[:40])
        e3, t3 = call("browser_execute_js", {"code": "String(window.name)", "frame_id": fid, "world": "main"})
        wname = val(t3) if not e3 else ('ERR:' + val(t3)[:40])
        print('   [%d] 清单name=%-14r is_main=%-5s id=%s' % (i, f.get('name'), f.get('is_main'), fid))
        print('        真实: href=%s | window.name=%r' % (href[:70], wname))


call("browser_navigate", {"url": "https://example.com/?order=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.5)
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"ofr\" name=\"orderfr\" srcdoc=\"<b>x</b>\"></iframe>');'ok'"})
time.sleep(1.0)
survey('刚建好命名 iframe')

# 制造"页面churn"后再看一次(fastcheck 里那次异常就出现在长会话之后)
for i in range(3):
    call("browser_dom_set_html", {"selector": "body", "html": "<p>churn%d</p>" % i})
    time.sleep(0.2)
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"ofr2\" name=\"orderfr2\" srcdoc=\"<b>y</b>\"></iframe>');'ok'"})
time.sleep(1.0)
survey('页面被重写 body 之后再建 iframe')
