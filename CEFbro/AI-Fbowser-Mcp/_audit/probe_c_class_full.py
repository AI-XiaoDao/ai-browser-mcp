# -*- coding: utf-8 -*-
"""C 类两个工具到底有没有 poll_hint? (台账只存 note 前 300 字符, 可能被截断 -> 必须实测完整回包)

若完整回包里有 poll_hint, 则它们属"已告知要轮询"的 A 类, 不是缺陷;
若没有, 才是"数据型工具只回回执且不告诉你怎么取", 需要补。
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


def c(n, a, to=60):
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
c("browser_navigate", {"url": "https://example.com/?cclass=1", "wait_for_load": True})

for name, args in (("browser_reverse_cookie_sources", {}),
                   ("browser_permission_spoof", {"permissions": "geolocation"})):
    e, t = c(name, args)
    print("== %s ==" % name)
    print("   isError=%s | 完整回包长度 %d" % (e, len(t)))
    print("   %s" % t[:700])
    print("   含 poll_hint: %s | 含 _async: %s" % ('poll_hint' in t, '"_async"' in t))
    print()
