# -*- coding: utf-8 -*-
r"""实测: `browser_reverse_preload` 的 `Page.addScriptToEvaluateOnNewDocument` 到底有没有在新文档里执行?

一轮探针里出现过"CDP 返回 success + identifier, 但导航后哨兵读不到"的现象, 必须复测清楚:
  ① 提交预注入代码(同时设 window 哨兵与 document.title 哨兵 —— 双预言机);
  ② 导航到带时间戳的新地址;
  ③ 等页面稳定后读两个哨兵;
  ④ 再导航一次(第二次机会)复读;
  ⑤ 对照: 同一实例用 browser_inject {persist:true,type:js} 的同型哨兵(上一轮已实测有效)。

用法: py -3 _audit\probe_preload_effective.py
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


def call(n, a=None, to=60):
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


def payload(txt):
    try:
        o = json.loads(txt)
    except Exception:
        return {}
    d = o.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return o if isinstance(o, dict) else {}


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?pl=%d" % int(time.time())})

print('\n[1] 提交预注入(双哨兵: window + document.title)')
e, t, d = call("browser_reverse_preload",
               {"code": "window.__plSentinel='C1';document.title='PRELOADED';"}, to=60)
print('    preload -> isError=%s %.2fs' % (e, d))
print('    %s' % t[:220])
p = payload(t)
if p:
    print('    载荷字段: %s' % sorted(p.keys()))
    print('    cdp_result=%s' % str(p.get("cdp_result"))[:120])

print('\n[2] 导航到新地址 → 读哨兵(第一次机会)')
call("browser_navigate", {"url": "https://example.com/?pl2=%d" % int(time.time())})
time.sleep(1.0)
e, t, _ = call("browser_execute_js", {"code": "String(window.__plSentinel)"})
print('    window 哨兵 -> %s' % t[:100])
e, t, _ = call("browser_get_title", {})
print('    title 哨兵 -> %s' % t[:100])

print('\n[3] 再导航一次 → 复读(第二次机会)')
call("browser_navigate", {"url": "https://example.com/?pl3=%d" % int(time.time())})
time.sleep(1.0)
e, t, _ = call("browser_execute_js", {"code": "String(window.__plSentinel)"})
print('    window 哨兵 -> %s' % t[:100])
e, t, _ = call("browser_get_title", {})
print('    title 哨兵 -> %s' % t[:100])

print('\n[4] 对照: browser_inject {persist:true,type:js} 同型哨兵')
call("browser_inject", {"type": "js", "persist": True,
                        "code": "window.__injSentinel='I1';", "inject_id": "pl_probe"})
call("browser_navigate", {"url": "https://example.com/?pl4=%d" % int(time.time())})
time.sleep(0.8)
e, t, _ = call("browser_execute_js", {"code": "String(window.__injSentinel)"})
print('    persist:js 哨兵 -> %s' % t[:100])
