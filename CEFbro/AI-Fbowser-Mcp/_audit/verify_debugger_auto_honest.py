# -*- coding: utf-8 -*-
"""验收 browser_debugger_auto 的"静默假成功"修复 + 新增的"零命中"快速失败。

修复内容:
  · 0 命中 -> 诚实失败(原来**无条件** success:true, 只带 hits:0)
  · 断点 locations 为空 且 未传 url(不会导航) -> 立即失败, 不把 max_ms 等满
  · 默认等待预算 60000ms -> 12000ms(客户端常在 15s 就放弃, 原值只会造成"客户端超时+服务端还在等")
  · 新增 completed / stop_reason 字段如实标注是否跑满

判据(三条互相约束, 防止把工具"修成永远失败"):
 ① 零命中(breakpoint 正则匹配不到任何脚本) -> 必须**失败**且**很快**(远小于 max_ms)  [不白等]
 ② 断点有效但永不命中 -> 必须**失败**, 绝不能再出现 success:true hits:0            [不假成功]
 ③ **正对照**: 断点真的命中 -> 必须 **success:true 且 hits>=1**                     [不假失败]
    ③ 用"注入内联脚本 + setInterval 周期性执行目标行"构造真实命中, 否则无法排除
    "我把成功路径也改坏了" 这种可能。
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


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:92]))


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
call("browser_navigate", {"url": "https://example.com/?autofix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① 零命中 -> 快速失败(不把 max_ms 等满) ==")
BUDGET = 20000
e, t, dt = call("browser_debugger_auto",
                {"breakpoint": "mcp_no_such_script_zzz_9911", "line": 0, "max_ms": BUDGET}, 60)
print("     isError=%s 用时=%.2fs" % (e, dt))
print("     resp: %s" % t[:300])
rec("是失败(非假成功)", e and ('"success":true' not in t), t[:88])
rec("给出'0 个脚本位置'的可行动原因", ("0 个脚本位置" in t) or ("locations 为空" in t), t[:88])
rec("用时远小于预算(未白等 %dms)" % BUDGET, dt < 6.0, "%.2fs" % dt)

print("\n== ② 断点有效但永不命中 -> 必须诚实失败, 不得 success:true hits:0 ==")
NEVER = "\n".join([
    "window.mcpNeverTick=0;",
    "window.mcpNeverCalled=function mcpNeverCalled(){",
    "  window.mcpNeverTick=window.mcpNeverTick+1;",
    "};",
])
inj = ("(function(){var s=document.createElement('script');"
       "s.textContent=%s;document.body.appendChild(s);return 'ok'})()"
       % json.dumps(NEVER))
call("browser_execute_js", {"code": inj}, 30)
target_line = NEVER.split("\n").index("  window.mcpNeverTick=window.mcpNeverTick+1;")
print("     注入的内联脚本行号(0起) = %d 内容: %r" % (target_line, NEVER.split("\n")[target_line]))
e, t, dt = call("browser_debugger_auto",
                {"breakpoint": "example\\.com", "line": target_line,
                 "max_ms": 3000, "max_hits": 2}, 60)
print("     isError=%s 用时=%.2fs" % (e, dt))
print("     resp: %s" % t[:300])
rec("不再是 success:true 的假成功", '"success":true' not in t, t[:88])
if '"success":true' not in t:
    rec("失败原因可行动(提到未命中/停止原因)",
        ("未捕获到任何断点命中" in t) or ("0 个脚本位置" in t), t[:88])

print("\n== ③ 正对照: 断点真命中 -> 必须 success:true 且 hits>=1(防止把成功路径改坏) ==")
FIRING = "\n".join([
    "window.mcpTick=0;",
    "window.mcpFired=function mcpFired(){",
    "  window.mcpTick=window.mcpTick+1;",
    "};",
    "window.mcpTimer=setInterval(window.mcpFired, 300);",
])
inj2 = ("(function(){var s=document.createElement('script');"
        "s.textContent=%s;document.body.appendChild(s);return 'ok'})()"
        % json.dumps(FIRING))
e, t, dt = call("browser_execute_js", {"code": inj2}, 30)
print("     注入: isError=%s %s" % (e, t[:80]))
fire_line = FIRING.split("\n").index("  window.mcpTick=window.mcpTick+1;")
print("     目标行(0起) = %d" % fire_line)
e, t, dt = call("browser_debugger_auto",
                {"breakpoint": "example\\.com", "line": fire_line,
                 "max_ms": 8000, "max_hits": 2}, 60)
print("     isError=%s 用时=%.2fs" % (e, dt))
print("     resp: %s" % t[:400])
try:
    obj = json.loads(t)
    inner = obj.get("data") if isinstance(obj.get("data"), dict) else obj
    hits = inner.get("hits")
    ok3 = (inner.get("success") is True) and isinstance(hits, int) and hits >= 1
    print("     success=%s hits=%s completed=%s stop_reason=%s"
          % (inner.get("success"), hits, inner.get("completed"), str(inner.get("stop_reason"))[:40]))
except Exception as ex:
    ok3 = False
    print("     (解析失败: %s)" % ex)
rec("真命中时仍然成功且 hits>=1", ok3, t[:88])

# 清场: 停掉周期任务, 关掉断点, 免污染后续测量
call("browser_execute_js", {"code": "(function(){if(window.mcpTimer)clearInterval(window.mcpTimer);"
                                   "window.mcpFired=function(){};window.mcpNeverCalled=function(){};return 'clean'})()"}, 30)
call("browser_cdp_call", {"method": "Debugger.setBreakpointsActive", "params": "{\"active\":false}"}, 20)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
