# -*- coding: utf-8 -*-
"""测量 §101.4 记下的隐患: browser_debugger_evaluate 的"活帧"可能是**陈旧帧**。

背景: E1(报告 §101)让 evaluate 在缺 call_frame_id 时自动取"活帧", 走的是
  确保调试器已暂停 -> 取CDP事件数据JSON("Debugger.paused") -> 解析出 call_frame_id。
而 `确保调试器已暂停` 的**第一步**是: `如果 (取CDP事件数据JSON ("Debugger.paused") != "") 返回 真`
—— 只看"事件日志里有没有 paused 事件", 而事件日志是**跨导航、跨轮次保留**的。
于是可能出现: 页面早就 resume 了、甚至已经导航到新文档, 日志里那条旧 paused 还在,
工具就拿那条**旧帧 ID** 去求值 -> 内核回 `Invalid call frame id`。

判据(可证伪):
 ① 基线: 干净页面上 evaluate(缺帧 ID) 应成功 —— 若失败, 说明是更基础的问题
 ② **陈旧场景**: 制造暂停 -> resume -> **导航到新文档** -> 再 evaluate(缺帧 ID)
    · 稳健实现: 成功(要么取到有效活帧, 要么重新造一个暂停点并如实上报 auto_prepared)
    · 有缺陷实现: 报 "Invalid call frame id"(用了个早就不存在的帧)
 ③ 对照: 显式传一个**随便编的**帧 ID 必须仍然失败(证明②的成功不是因为"帧 ID 根本没被用")
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
res = []


def call(name, args, timeout=60):
    t0 = time.time()
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def unesc(t):
    return t.replace('\\"', '"')


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:88]))


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

print("== ① 基线: 干净页面上 evaluate(缺帧 ID) ==")
call("browser_navigate", {"url": "https://example.com/?stale=1", "wait_for_load": True}, 45)
time.sleep(0.6)
e, t, dt = call("browser_debugger_evaluate", {"expression": "document.title"}, 60)
print("   isError=%s %.2fs %s" % (e, dt, t[:200]))
rec("基线成功", not e, t[:86])

print("\n== ② 陈旧场景: 制造暂停 -> resume -> **导航到新文档** -> 再 evaluate ==")
e, t, _ = call("browser_debugger_stack", {}, 60)
print("   stack(制造暂停): isError=%s %s" % (e, t[:150].replace("\n", " ")))
frame = None
m = re.search(r'"call_frame_id"\s*:\s*"([^"]+)"', unesc(t))
if m:
    frame = m.group(1)
print("   拿到的帧 ID = %s" % frame)
e, t, _ = call("browser_debugger_resume", {}, 45)
print("   resume: isError=%s %s" % (e, t[:120].replace("\n", " ")))
# 导航到**新文档**(旧帧必然失效)
call("browser_navigate", {"url": "https://example.com/?stale=2", "wait_for_load": True}, 45)
time.sleep(0.8)
e, t, dt = call("browser_debugger_evaluate", {"expression": "document.title"}, 60)
print("   导航后 evaluate(缺帧 ID): isError=%s %.2fs" % (e, dt))
print("   %s" % t[:300])
u = unesc(t)
stale_hit = "Invalid call frame id" in u
rec("导航后 evaluate 仍成功(未用陈旧帧)", not e, t[:86])
rec("若失败, 不是因陈旧帧(无 Invalid call frame id)", not stale_hit, t[:86])
if "auto_prepared" in u:
    print("   (auto_prepared: %s)" % u[u.find("auto_prepared"):u.find("auto_prepared") + 160])

print("\n== ③ 对照: 显式传编造的帧 ID 必须失败 ==")
e2, t2, _ = call("browser_debugger_evaluate",
                 {"call_frame_id": "mcp-bogus-frame-xyz", "expression": "1"}, 45)
print("   isError=%s %s" % (e2, t2[:200]))
rec("编造帧 ID 仍失败(非假阳性)", e2, t2[:86])

# 收尾: 恢复
call("browser_debugger_resume", {}, 30)
bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
