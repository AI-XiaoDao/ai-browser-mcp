# -*- coding: utf-8 -*-
r"""诊断: 为什么第一次 arm 有时 0.05s 返回且没有快照?
打印**原始回包全文**并区分三条路径(快照 / 已武装文案 / CDP 派发失败), 对照两种前置(有无 context_menu set)。

用法: py -3 _audit\probe_arm_paths.py
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
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def kind(t):
    if "declared_count" in t:
        return "SNAPSHOT"
    if "已武装" in t:
        return "ARMED(未抓到)"
    if "CDP" in t or "无法" in t or "失败" in t:
        return "FAIL"
    return "OTHER"


def trial(name, preset):
    loop.kill_app()
    if not loop.start_app():
        print('!! %s 启动失败' % name); return
    call("browser_navigate", {"url": "https://example.com/?ap=%d" % int(time.time())})
    if preset:
        e, t, d = call("browser_context_menu", {"action": "set",
                                                "items": "item|MCP索引测试项|26501|1|0|\naccelat||0|1|0|70C"}, to=30)
        print('  [%s] 预置 set: isError=%s %.2fs' % (name, e, d))
    e, t, d = call("browser_menu_probe", {"action": "arm", "x": 240, "y": 170}, to=60)
    print('  [%s] arm#1 isError=%-5s %.2fs -> %s' % (name, e, d, kind(t)))
    print('        %s' % t[:300])
    time.sleep(0.6)
    e2, t2, d2 = call("browser_menu_probe", {"action": "arm", "x": 240, "y": 170}, to=60)
    print('  [%s] arm#2 isError=%-5s %.2fs -> %s' % (name, e2, d2, kind(t2)))
    e3, t3, d3 = call("browser_context_menu", {"action": "get"}, to=30)
    try:
        p = json.loads(t3)
        p = json.loads(p.get("data")) if isinstance(p.get("data"), str) else p
    except Exception:
        p = {}
    print('  [%s] context_menu get: apply_count=%s last_applied=%s verified=%s failed=%s'
          % (name, p.get("apply_count"), p.get("last_applied_items"), p.get("verified_items"),
             str(p.get("apply_failed"))[:90]))
    call("browser_context_menu", {"action": "clear"}, to=30)


print('== A: 不预置规格 ==')
trial('A', False)
print('\n== B: 先预置规格(含 accelat 索引行) ==')
trial('B', True)
