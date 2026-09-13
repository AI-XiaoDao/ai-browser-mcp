# -*- coding: utf-8 -*-
r"""第148轮 每轮一测: browser_shutdown(设计上会退出整个进程; oracle = 守卫拒绝 + 确认后进程真退出 + 重启可恢复)。

判据:
  ① 干净启动: execute_js 快 + status 可用
  ② 守卫: 无 confirm → 拒绝(文案含 confirm)
  ③ 守卫: confirm:false → 同拒
  ④ confirm:true + delay_seconds:1 → 成功回包"安全关闭"
  ⑤ 进程在 ≤15s 内真退出(HTTP 端点不可达)
  ⑥ 重启后可恢复(再次健康)
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-56s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


def alive():
    e, t, d = call("browser_status", {}, to=3)
    return not e


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
health('①execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)

print('\n== ②③ 守卫(无 confirm 必须拒绝) ==')
e, t, d = call("browser_shutdown", {}, to=60)
rec('②无 confirm → 拒绝(文案含 confirm)', e and ("confirm" in t), t[:80])
e, t, d = call("browser_shutdown", {"confirm": False}, to=60)
rec('③confirm:false → 同拒', e and ("confirm" in t), t[:80])
health('②③之后 execute_js 仍快(拒绝未伤通道)')

print('\n== ④ confirm:true 真执行 ==')
e, t, d = call("browser_shutdown", {"confirm": True, "delay_seconds": 1}, to=60)
rec('④confirm:true 成功回包(含"安全关闭")', (not e) and ("安全关闭" in t), "%.2fs %s" % (d, t[:70]))

print('\n== ⑤ 进程真退出(≤15s) ==')
gone = False
t0 = time.time()
while time.time() - t0 < 15:
    if not alive():
        gone = True
        break
    time.sleep(0.5)
rec('⑤进程在 ≤15s 内退出', gone, "%.1fs" % (time.time() - t0))

print('\n== ⑥ 重启可恢复 ==')
if not loop.start_app():
    print('!! 重启失败'); sys.exit(1)
health('⑥重启后 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑥重启后 browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
