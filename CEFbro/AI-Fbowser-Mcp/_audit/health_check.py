# -*- coding: utf-8 -*-
r"""CDP 健康探针(只读, 不做任何注入): 依次量 status / execute_js / dom_query / cdp_call 的延迟与错误。

用途: 在"某臂变红"时先判定是**会话被搞坏**还是**机器负载/偶发**, 再决定要不要重启。
判据: 全部 <3s 且无错误 => 健康; 出现 ~5s/10s/30s 的台阶或报错 => 会话已退化(需重启)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=45):
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


CASES = [
    ("browser_status", {}),
    ("browser_get_url", {}),
    ("browser_execute_js", {"code": "1+1"}),
    ("browser_dom_query", {"selector": "h1"}),
    ("browser_cdp_call", {"method": "Runtime.evaluate",
                          "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"}),
    ("browser_get_text", {"selector": "h1"}),
]
worst = 0.0
bad = []
for n, a in CASES:
    t0 = time.time()
    e, t = call(n, a)
    dt = time.time() - t0
    worst = max(worst, dt)
    if dt >= 3.0 or e:
        bad.append((n, round(dt, 2), e, t[:80]))
    print('   %-20s %6.2fs err=%-5s %s' % (n, dt, e, t[:70].replace('\n', ' ')))

print('\n最慢 %.2fs; 异常项 %d 个' % (worst, len(bad)))
for b in bad:
    print('   !! %s %.2fs err=%s %s' % b)
print('判读: %s' % ('**健康**(全部 <3s 且无错误)' if not bad else '**已退化/异常** —— 建议重启实例后复测'))
