# -*- coding: utf-8 -*-
"""判别实验: 回读报出的"期望与实测相反"是真没生效, 还是我用错了 getter?

做法 —— 在回调内对**同一个命令ID**依次 置禁止状态(真)/置禁止状态(假)/置可见状态(真)/
置可见状态(假)/选中状态(真)/选中状态(假), **每次置完立刻读一次**, 把原始布尔值记下来:

  禁止T->?  禁止F->?  可见T->?  可见F->?  选中T->?  选中F->?

判据(对每个 ID 都成立才说明这条链是通的):
  · 一条链通(如 禁止T->T 且 禁止F->F)  => setter 生效且 getter 反映该量;
    那么回读给的"不一致"就是**真实结论**(该 ID 上那个状态确实没被改)。
  · 两次读**相同**                         => 该 getter 不反映该状态(可能读的是别的量);
    回读方式需要改, 而不是报"没生效"。

覆盖 4 类 ID: 102(默认项, 可禁用) / 130(默认项, 可隐藏) / 113(默认项, 非勾选类) /
26501(我们自建的普通项)。
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
SPEC = "\n".join([
    "item|自建项|0|1|0|",
    "diag||26501|1|0|",
    "diag||102|1|0|",
    "diag||130|1|0|",
    "diag||113|1|0|",
])


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


def flat(t):
    return t.replace('\\"', '"')


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?diag=1", "wait_for_load": True}, 90)
time.sleep(0.6)

print("== 下发布置诊断的规格 ==")
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print("   isError=%s | %s" % (e, t[:240]))
if e:
    sys.exit(1)

print("\n== 右键一次 -> 回调内逐项置真/置假并回读 ==")
for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
    call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                             "params": {"type": typ, "x": 130, "y": 130,
                                        "button": "right", "clickCount": 1,
                                        "buttons": btn}}, 40)
time.sleep(1.5)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
print("   -> %s" % f[:900])

blocks = re.findall(r'\[diag (\d+) ([^\]]*)\]', f)
print("\n== 原始回读值 ==")
if not blocks:
    print("   !! 没有 diag 记录 —— 回调可能没跑, 或锚点没生效")
for cid, body in blocks:
    print("   ID %-6s %s" % (cid, body))

print("\n== 判据 ==")
ok = 0
for cid, body in blocks:
    d = dict(re.findall(r'(\S+?)->([TF])', body))
    lines = []
    good = True
    for k in ("禁止T", "禁止F", "可见T", "可见F", "选中T", "选中F"):
        if k not in d:
            lines.append("%s=缺" % k)
            good = False
        else:
            lines.append("%s=%s" % (k, d[k]))
    # 关键: T 读与 F 读是否不同 -> 该链是否真的通
    for name, a, b in (("禁止", "禁止T", "禁止F"), ("可见", "可见T", "可见F"),
                       ("选中", "选中T", "选中F")):
        if a in d and b in d:
            state = "链通(读值随设置变化)" if d[a] != d[b] else "★链不通(两次读相同)"
        else:
            state = "?"
        print("   ID %-6s %-4s %s | %s" % (cid, name, state, " ".join(lines)))
        if d.get(a) != d.get(b):
            good = True
    if good:
        ok += 1

print("\n   4 个 ID 中 %d 个至少有一条链是通的" % ok)
call("browser_context_menu", {"action": "clear"})
print("== 完 ==")
