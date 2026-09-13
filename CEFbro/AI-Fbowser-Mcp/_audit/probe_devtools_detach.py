# -*- coding: utf-8 -*-
"""用**正确的**工具触发 DevTools 分离事件, 并修掉上一版探测器的口径缺陷。

上一版把回包按 `result` 解析, 而"工具不存在"是走 JSON-RPC `error` 的 ——
于是 `browser_debugger_disable`(不存在) 被误读成 `isError=False + 空正文`。
本次:
  ① 修正解析: `error` 字段也要显式区分;
  ② DevTools 附加: `browser_debugger_enable`;  分离: `browser_vip_disable_debugger`(清单里真实存在)。
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
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def n_events(name):
    e, t = call("browser_event", {"event_type": name}, 40)
    return len(t.split('"event":"%s"' % name)) - 1


print('== DevTools 附加 -> 分离 ==')
e, t = call("browser_debugger_enable", {})
print('   debugger_enable : isError=%s %s' % (e, t[:120]))
time.sleep(1.2)
print('   devtools_attached 条数 = %d' % n_events("devtools_attached"))
e, t = call("browser_vip_disable_debugger", {})
print('   vip_disable_debugger: isError=%s %s' % (e, t[:160]))
time.sleep(1.5)
print('   devtools_detached 条数 = %d' % n_events("devtools_detached"))
if n_events("devtools_detached") == 0:
    # 再试另一条可能路径: 关掉调试器后再 enable 一次(有些实现是"重连即先 detach")
    call("browser_debugger_enable", {})
    time.sleep(1.2)
    print('   重连后再查 devtools_detached = %d' % n_events("devtools_detached"))
    e, t = call("browser_event", {"event_type": "devtools_detached"})
    print('   原文: %s' % t[:200])
