# -*- coding: utf-8 -*-
"""逐个验收本轮纳入同步等待的 12 个工具: 到底"一次调用就拿到东西"了吗?

判据: 回包非空、不是 _async 回执、不是超时。
已知 browser_scrape 会返回**空串**(同步转换器处理不了它的载荷形状) -> 必须回退,
这正是"加进白名单必须逐个真机验收"的原因。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


CASES = [
    ("browser_dom_get_html", {"selector": "h1"}),
    ("browser_dom_select", {"selector": "h1"}),
    ("browser_dom_set_html", {"selector": "#mcpX", "html": "<b>ok</b>"}),
    ("browser_extract", {"type": "links", "limit": 5}),
    ("browser_view_source", {}),
    ("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1"}),
    ("browser_vip_dom_get_document", {"depth": 2}),
    ("browser_vip_dom_search", {"query": "Example"}),
    ("browser_reverse_cookie_sources", {}),
    ("browser_inject", {"type": "js", "code": "window.__mcpInj=1"}),
    ("browser_canvas_noise", {"action": "inject", "level": 1}),
    ("browser_permission_spoof", {"action": "apply"}),
]

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?wk=1", "wait_for_load": True})

keep, drop = [], []
for name, args in CASES:
    e, t = call(name, args)
    empty = (t.strip() in ('""', "", "{}"))
    is_async = '"_async":true' in t
    timeout = '超时' in t
    verdict = 'KEEP' if (not e and not empty and not is_async and not timeout) else 'DROP'
    (keep if verdict == 'KEEP' else drop).append(name)
    print("%-34s %-5s isError=%-5s 空=%-5s 异步=%-5s 超时=%-5s" %
          (name, verdict, e, empty, is_async, timeout))
    print("      %s" % t[:220].replace('\n', ' '))

print("\n== 可保留(一次调用即拿到东西): %d ==" % len(keep))
for n in keep:
    print("   %s" % n)
print("== 需回退(仍是回执/空/超时): %d ==" % len(drop))
for n in drop:
    print("   %s" % n)
