# -*- coding: utf-8 -*-
"""★关键实验: browser_navigate 会不会被**上一次导航遗留的 load_end 事件**假满足?

背景(第106轮实测): back/forward 纳入同步后, 调用内 0.03s 就"等待条件满足: load_end → 后退前那一页"
—— 事件驱动那条等待路径不判序事件属于哪一次导航。navigate **在同步名单里**, 若同样受影响,
那是**高危真缺陷**(会谎称页面已载入, AI 随后读到旧页面的 DOM)。

区分性设计: 先正常导航到 A(此时必然已产生若干 load_end 事件), 紧接着导航到一个**永远载入不了**的
地址(黑洞 IP)。正确行为 = **如实超时/失败**; 假满足 = **几乎立刻返回成功**。
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
A = "https://example.com/?navTrap=1"
BLACKHOLE = "https://10.255.255.1/"


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


def live_url():
    e, t = call("browser_evaluate", {"code": "location.href"}, 30)
    m = re.search(r'"(https?://[^"]*)"', t)
    return m.group(1) if m else t.strip()[:60]


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

print("== 准备: 正常导航到 A, 确保已有 load_end 事件 ==")
e, t = call("browser_navigate", {"url": A, "wait_for_load": True}, 90)
print("   -> isError=%s | %s" % (e, t[:180]))
time.sleep(1.0)
u0 = live_url()
print("   实时 URL: %s" % u0)
print("   [%s] 准备就绪(A 已载入)" % ('PASS' if 'navTrap=1' in u0 else 'FAIL'))

print("\n== ★主体: 紧接着导航到**黑洞地址**(永远载入不了, max_ms=8000) ==")
t0 = time.time()
e2, t2 = call("browser_navigate", {"url": BLACKHOLE, "wait_for_load": True,
                                   "max_ms": 8000}, 120)
el = time.time() - t0
u1 = live_url()
print("   用时 %.2fs isError=%s" % (el, e2))
print("   回包: %s" % t2[:300])
print("   实时 URL: %s" % u1)

fast_success = (not e2) and (el < 3.0) and ('超时' not in t2) and ('失败' not in t2)
print()
print("   [%s] 未被旧事件假满足(慢或如实报错)" % ('PASS' if not fast_success else 'FAIL'))
print("   [%s] 若成功则页面确实已是目标页" % ('PASS' if (fast_success and BLACKHOLE in u1) or not fast_success else 'FAIL'))
print("\n   判读: 用时 <3s 且报成功 = **假满足**(高危); 用时≈8s 且报超时 = 正常。")
