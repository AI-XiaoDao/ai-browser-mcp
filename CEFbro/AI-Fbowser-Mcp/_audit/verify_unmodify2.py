# -*- coding: utf-8 -*-
"""验收 unmodify/unreplace（修正版：用**全新 URL** 避免浏览器缓存掩盖效果）。

上一版失败的原因是**缓存**: 对同一个 URL 反复导航会命中缓存, 过滤器根本不会被调用 ——
日志实测证明通道是好的: `[MCP] 手写篡改已挂载: block → https://example.com/?diag=1`。

本版设计:
  规则 url 用 "example.com/?unmod" (子串) -> 能匹配 ?unmod=1 / ?unmod=2 等**各不相同的** URL
  A 基线      -> ?unmod=0 正常
  B 加 block  -> ?unmod=1 应被屏蔽(全新 URL, 必走过滤器)
  C unmodify  -> 应报撤销 1 条
  D 撤销后    -> ?unmod=2 (全新 URL) 应恢复正常  ← 真正证明"规则被删掉了"
  E 再 unmodify -> 幂等成功报 0 条
  F unreplace   -> 幂等成功报 0 条
  G replace_data 也能被 unmodify 撤销(动作不限)
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
RULE = "example.com/?unmod"
BLOCK_MARK = '资源已屏蔽'
R = []


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


def body_of(suffix):
    """导航到一个**全新** URL 并返回正文(避免缓存)"""
    url = "https://" + RULE + suffix
    call("browser_navigate", {"url": url, "wait_for_load": True}, 90)
    time.sleep(0.4)
    e, t = call("browser_evaluate",
                {"code": "(document.body?document.body.innerText:'').slice(0,90)"}, 40)
    return t.strip()[:120]


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:240])


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

call("browser_intercept", {"action": "clear"})
print("== A) 基线(全新 URL ?unmod=0) ==")
b0 = body_of("=0")
print("   正文: %r" % b0)
arm("基线未被屏蔽", BLOCK_MARK not in b0, b0)

print("\n== B) 加 block 规则(url=%s) 后访问全新 URL ?unmod=1 ==" % RULE)
e, t = call("browser_intercept", {"action": "block", "url": RULE})
print("   block -> %s" % t[:130])
b1 = body_of("=1")
print("   正文: %r" % b1)
arm("block 生效(全新 URL 被屏蔽)", BLOCK_MARK in b1, b1)

print("\n== C) unmodify 撤销(用完整 URL 指定) ==")
e, t = call("browser_intercept", {"action": "unmodify",
                                  "url": "https://" + RULE + "=1"})
print("   unmodify -> isError=%s %s" % (e, t[:230]))
arm("unmodify 报出撤销 1 条", (not e) and (" 1 条" in t), t[:170])

print("\n== D) 撤销后访问**另一个全新 URL** ?unmod=2(应恢复) ==")
b2 = body_of("=2")
print("   正文: %r" % b2)
arm("unmodify 真的删掉了规则(新 URL 不再被屏蔽)", BLOCK_MARK not in b2, b2)

print("\n== E) 再 unmodify 同一规则(已不存在) ==")
e, t = call("browser_intercept", {"action": "unmodify",
                                  "url": "https://" + RULE + "=1"})
print("   -> isError=%s %s" % (e, t[:200]))
arm("撤销不存在 = 幂等成功且报 0 条", (not e) and (" 0 条" in t), t[:150])

print("\n== F) unreplace(无 replace_file 规则) ==")
e, t = call("browser_intercept", {"action": "unreplace",
                                  "url": "https://" + RULE + "=1"})
print("   -> isError=%s %s" % (e, t[:200]))
arm("unreplace 幂等成功且报 0 条", (not e) and (" 0 条" in t), t[:150])

print("\n== G) replace_data 规则也能被 unmodify 撤销(动作不限) ==")
call("browser_intercept", {"action": "replace_data", "url": RULE,
                           "replace_text": "<html><body>REPLACED-BODY</body></html>"})
b3 = body_of("=3")
print("   replace_data 后 ?unmod=3 正文: %r" % b3)
e, t = call("browser_intercept", {"action": "unmodify", "url": "https://" + RULE + "=3"})
print("   unmodify -> %s" % t[:170])
b4 = body_of("=4")
print("   撤销后 ?unmod=4 正文: %r" % b4)
arm("replace_data 能被 unmodify 撤销",
    ('REPLACED-BODY' in b3) and ('REPLACED-BODY' not in b4),
    "改后=%r 撤销后=%r" % (b3, b4))

call("browser_intercept", {"action": "clear"})
ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
