# -*- coding: utf-8 -*-
r"""第156轮: browser_vip_execute_js_context 六个执行参数暴露验收。

判据:
  ① 基线健康
  ② tools/list: schema 含 timeout_ms/repl_mode/user_gesture/silent/disable_breaks/include_command_line_api
  ③ 守卫: target=main 未启用环境 → 可行动失败(原行为保持)
  ④ 启用环境(毒化如警告) → 带全部6参数执行 6*7 → 轮询 mcp_result 得 42(参数被接受且执行成功)
  ⑤ 重启恢复
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=90):
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
    print('  [%s] %-58s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r156exec=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ② schema 暴露 ==')
try:
    b = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
    props = {}
    for t in (o.get("result") or {}).get("tools") or []:
        if t.get("name") == "browser_vip_execute_js_context":
            props = list(t.get("inputSchema", {}).get("properties", {}).keys())
    rec('②schema 含全部6个新参数', all(k in props for k in
        ("timeout_ms", "repl_mode", "user_gesture", "silent", "disable_breaks", "include_command_line_api")), props)
except Exception as ex:
    rec('②tools/list', False, repr(ex))

print('\n== ③ 守卫保持: target=main 未启用 → 拒绝 ==')
e, t, d = call("browser_vip_execute_js_context", {"code": "1", "target": "main"}, to=60)
rec('③未启用环境 → 可行动失败', e and ("browser_vip_enable_js_env" in t), t[:90])

print('\n== ④ 启用环境后带6参数执行(默认路径零前置自动解析) ==')
e, t, d = call("browser_vip_enable_js_env", {"enable": True, "confirm": True}, to=60)
rec('④enable 成功(毒化如警告)', (not e) and ("破坏" in t), "%.2fs" % d)
e, t, d = call("browser_vip_execute_js_context",
               {"code": "6*7", "timeout_ms": 30000, "repl_mode": False, "user_gesture": True,
                "silent": False, "disable_breaks": False, "include_command_line_api": True}, to=60)
rec('④带6参数提交成功(异步, 未给 context_id)', not e, "%.2fs %s" % (d, t[:70]))
tid = ""
m = re.search(r"task_[0-9_]+", t)
if m:
    tid = m.group(0)
rec('④回执含 task_id', bool(tid), tid)
ok42 = False
if tid:
    for _ in range(20):
        e2, t2, _ = call("mcp_result", {"request_id": tid}, to=30)
        if not e2 and "42" in t2:
            ok42 = True
            break
        if e2 and ("VIP操作失败" in t2 or "自动解析环境清单失败" in t2):
            break
        time.sleep(0.5)
rec('④默认路径自动解析 context_id → 6*7=42', ok42, tid)

print('\n== ④b target=main 对照 ==')
e, t, d = call("browser_vip_execute_js_context",
               {"code": "6*7", "target": "main", "timeout_ms": 30000}, to=60)
rec('④b target=main 提交成功', not e, "%.2fs" % d)
m2 = re.search(r"task_[0-9_]+", t)
ok42b = False
if m2:
    for _ in range(20):
        e2, t2, _ = call("mcp_result", {"request_id": m2.group(0)}, to=30)
        if not e2 and "42" in t2:
            ok42b = True
            break
        if e2 and ("VIP操作失败" in t2):
            break
        time.sleep(0.5)
rec('④b target=main → 6*7=42', ok42b, m2.group(0) if m2 else '')

print('\n== ⑤ 重启恢复 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 重启失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r156exec2=%d" % int(time.time())})
health('⑤重启后 execute_js 快(恢复)')
e, t, d = call("browser_status", {})
rec('⑤browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
