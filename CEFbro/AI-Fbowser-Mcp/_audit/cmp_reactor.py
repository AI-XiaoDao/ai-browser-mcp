# -*- coding: utf-8 -*-
"""同条件对比: 通配 * 与具体事件名, 在同一实例同一时刻各注册一条, 导航后看哪条生效。
目的: 确认"只有 * 生效"这个结论是否稳定(排除脚本差异/时序差异)。"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

B = "http://127.0.0.1:9222"


def raw(n, a, t=30):
    try:
        r = urllib.request.Request(
            B + "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": n, "arguments": a}}).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=t).read().decode())
        rr = d.get("result") or {}
        return "".join(i.get("text") or "" for i in (rr.get("content") or [])).replace("\n", " ")[:110]
    except Exception as ex:
        return "EXC:%s" % ex


raw("browser_kernel_reactor", {"action": "clear"})
print("== 同条件对比: 两条规则各注册一次 ==")
print("   add *               ->", raw("browser_kernel_reactor",
      {"action": "add", "event": "*", "code": "window.__starSeen=1;document.title='STAR_OK'", "cooldown_ms": 100}))
print("   add resource_response ->", raw("browser_kernel_reactor",
      {"action": "add", "event": "resource_response", "code": "document.title='RESP_OK'", "cooldown_ms": 100}))
raw("browser_navigate", {"url": "https://example.com/?cmp=%d" % int(time.time()), "wait_for_load": True}, 30)
time.sleep(1.5)
t = raw("browser_get_title", {})
print("   导航后标题 =", t)
print("   >>> * 生效 =", "STAR_OK" in t, " | resource_response 生效 =", "RESP_OK" in t)
print("   页面侧标记 window.__starSeen =", raw("browser_execute_js", {"code": "String(window.__starSeen)"}))
raw("browser_kernel_reactor", {"action": "clear"})
