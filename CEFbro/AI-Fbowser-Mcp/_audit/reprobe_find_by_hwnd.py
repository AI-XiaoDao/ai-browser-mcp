# -*- coding: utf-8 -*-
r"""用**真实**窗口句柄复测 browser_find_by_hwnd: 台账里它的失败是"未找到窗口句柄为 1"(探针假目标),
若真实句柄能通过, 则该失败属探针假目标而非功能缺陷 —— 应把探针覆盖值改对, 让台账反映真实状态。
"""
import json
import os
import sys
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


def val(t):
    try:
        return json.loads(t)
    except Exception:
        return t


e, t = call("browser_get_window_handle", {})
print('window_handle: isError=%s %s' % (e, t[:200]))
hwnd = None
try:
    hwnd = val(t).get("hwnd") or (val(t).get("data") or {}).get("hwnd")
except Exception:
    pass
print('解析到 hwnd=%r' % hwnd)

if hwnd:
    e2, t2 = call("browser_find_by_hwnd", {"hwnd": int(hwnd)})
    print('find_by_hwnd(真实句柄): isError=%s %s' % (e2, t2[:300]))
    e3, t3 = call("browser_find_by_hwnd", {"hwnd": 1})
    print('find_by_hwnd(假句柄=1): isError=%s %s' % (e3, t3[:200]))
