# -*- coding: utf-8 -*-
"""历史导航(back/forward)到底会不会触发 load_end?

决定性问题: 若会 -> 可把 back/forward 也纳入同步名单(一次调用即等到载入完成);
            若不会(bfcache 只换文档不重新加载) -> 纳入后必然超时, 应保持"回执+轮询"。
方法: back 之后拿到 task_id, 连续轮询 mcp_result, 看它是否收敛为非 _waiting。
"""
import json
import os
import re
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
A = "https://example.com/?wlA=1"
B = "https://example.com/?wlB=2"


def call(n, a, to=120):
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

call("browser_navigate", {"url": A, "wait_for_load": True}, 90)
call("browser_navigate", {"url": B, "wait_for_load": True}, 90)

print("== back 后轮询其等待任务 ==")
e, t = call("browser_back", {}, 90)
m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
tid = m.group(1) if m else ''
print("   back -> %s" % t[:200])
print("   task_id = %r" % tid)

if tid:
    for i in range(10):
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": tid}, 40)
        waiting = '_waiting' in t2
        print("   [%2d] %-14s %s" % (i + 1, '仍 _waiting' if waiting else '已收敛', t2[:150].replace('\n', ' ')))
        if not waiting:
            break
    else:
        print("   => 10 次仍未收敛: 历史导航**不触发** load_end(bfcache), 不应纳入同步名单")
