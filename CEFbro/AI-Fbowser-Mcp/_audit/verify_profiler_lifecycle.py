# -*- coding: utf-8 -*-
"""browser_reverse_profile 修复验收(行为级)。

四臂:
  A 诚实失败臂 stop 未 start -> 必须明确失败(修复前是 _async 假成功)
  B 正常流程臂 start -> (页面跑一段 CPU) -> stop -> 必须回**真实 profile**(含 nodes)
  C 精确间隔臂 start_precise -> stop -> 同样要有 profile(证明 enable+start 补齐了)
  D 查询臂 query -> 有真实返回
修复前: A 假成功; B/C 的 stop 回 success 却无 profile(内核报 No recording profiles found 被吞)。
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
TOOL = "browser_reverse_profile"

# 让页面真的烧点 CPU, 采样才有内容
BUSY = ("(function(){var s=0;for(var i=0;i<3000000;i++){s+=Math.sqrt(i);}"
        "return s})()")


def c(n, a, to=70):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


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
c("browser_navigate", {"url": "https://example.com/?profv=1", "wait_for_load": True})


def has_profile(t):
    """判据: 回包里出现真实剖析结构 nodes/callFrame, 而不是只有 success:true"""
    return ('"nodes"' in t) and ('callFrame' in t)


print("== A 诚实失败臂: stop 之前没 start ==")
e, t = c(TOOL, {"action": "stop"})
print("   isError=%s -> %s" % (e, t[:280]))
print("   [%s] A 明确失败并给出原因" % ("PASS" if (e or "No recording" in t) else "FAIL"))

print("\n== B 正常流程臂: start -> 烧CPU -> stop ==")
e, t = c(TOOL, {"action": "start"})
print("   start isError=%s -> %s" % (e, t[:200]))
c("browser_evaluate", {"code": BUSY}, 60)
time.sleep(0.4)
e, t = c(TOOL, {"action": "stop"}, 90)
ok_b = has_profile(t)
print("   stop isError=%s | 含真实 nodes/callFrame = %s" % (e, ok_b))
print("   stop 回包前 300 字: %s" % t[:300])
print("   [%s] B stop 真的取回了 profile" % ("PASS" if ok_b else "FAIL"))

print("\n== C 精确间隔臂: start_precise -> 烧CPU -> stop ==")
e, t = c(TOOL, {"action": "start_precise"})
print("   start_precise isError=%s -> %s" % (e, t[:200]))
c("browser_evaluate", {"code": BUSY}, 60)
time.sleep(0.4)
e, t = c(TOOL, {"action": "stop"}, 90)
ok_c = has_profile(t)
print("   stop isError=%s | 含真实 nodes/callFrame = %s" % (e, ok_c))
print("   [%s] C start_precise 路径也能取回 profile" % ("PASS" if ok_c else "FAIL"))

print("\n== D 查询臂: query ==")
e, t = c(TOOL, {"action": "query"})
print("   query isError=%s -> %s" % (e, t[:220]))
print("   [%s] D query 有真实返回" % ("PASS" if (not e and "coverage_result" in t) else "FAIL"))

e, t = c("browser_evaluate", {"code": "'alive:'+document.title"}, 20)
print("\n   终态存活检查: %s" % t[:120])
