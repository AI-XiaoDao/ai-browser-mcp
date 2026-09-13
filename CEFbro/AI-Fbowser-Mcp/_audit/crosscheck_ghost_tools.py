# -*- coding: utf-8 -*-
"""交叉核对: 那 5 个台账里没有的"幽灵" —— 到底是不在工具清单里(清单过期), 还是存在却没被测?

直接问正在跑的实例要 tools/list, 逐个确认。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
CHECK = [
    'browser_aliases', 'browser_batch', 'browser_create_tab', 'browser_debugger_pause',
    'browser_task_runner_post',
    'browser_fingerprint_languages', 'browser_reverse_css_coverage',
]


def rpc(method, params=None):
    b = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        b["params"] = params
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode("utf-8"))


o = rpc("tools/list")
tools = (o.get("result") or {}).get("tools") or []
names = [t.get("name") for t in tools]
print('实例工具总数 = %d' % len(names))
print()
for c in CHECK:
    hit = [t for t in tools if t.get("name") == c]
    if hit:
        d = (hit[0].get("description") or "")[:90]
        print('%-38s 在清单里 ✔  %s' % (c, d))
    else:
        # 找近似名(可能有别名)
        near = [n for n in names if c.split('_')[-1] in (n or '')]
        print('%-38s **不在清单里** 近似: %s' % (c, near[:6]))
