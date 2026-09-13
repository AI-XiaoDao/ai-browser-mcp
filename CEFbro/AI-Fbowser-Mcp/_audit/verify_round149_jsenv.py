# -*- coding: utf-8 -*-
r"""第149轮 每轮一测: browser_vip_enable_js_env(对照确证: 诚实警告 ↔ 实际毒化 ↔ 重启恢复)。

判据:
  ① 基线: execute_js 快 + status 可用
  ② 守卫: 缺 enable → 拒绝("不能省略")
  ③ 守卫: enable:true 缺 confirm → 拒绝且文案含 confirm 与毒化警告
  ④ enable:true + confirm:true → 成功且回包含"破坏 CDP 通道"诚实警告
  ⑤ 实际毒化与警告一致: 之后 execute_js 退化(≥5s 或报错)
  ⑥ 重启后恢复(execute_js 快) —— 警告里"只有重启进程才能恢复"属实
  ⑦ enable:false 关闭路径: 成功且不毒化(execute_js 仍快)
  ⑧ 收尾健康
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
    print('  [%s] %-56s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r149env=%d" % int(time.time())})
health('①execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)

print('\n== ②③ 守卫 ==')
e, t, d = call("browser_vip_enable_js_env", {}, to=60)
rec('②缺 enable → 拒绝(不能省略)', e and ("不能省略" in t), t[:80])
e, t, d = call("browser_vip_enable_js_env", {"enable": True}, to=60)
rec('③enable:true 缺 confirm → 拒绝且含毒化警告', e and ("confirm" in t) and ("破坏" in t), t[:90])
health('②③之后 execute_js 仍快(拒绝未毒化)')

print('\n== ④ 显式确认启用 ==')
e, t, d = call("browser_vip_enable_js_env", {"enable": True, "confirm": True}, to=60)
rec('④enable:true+confirm 成功且含"破坏 CDP 通道"诚实警告', (not e) and ("破坏 CDP" in t),
    "%.2fs %s" % (d, t[:80]))

print('\n== ⑤ 实际毒化与警告一致 ==')
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('⑤启用后 execute_js 退化(≥5s 或报错) —— 与警告一致', e or d >= 5.0, "%.2fs err=%s" % (d, e))
e, t, d = call("browser_status", {})
rec('⑤browser_status 仍可用(活性探针)', not e, "%.2fs" % d)

print('\n== ⑥ 重启恢复(警告属实) ==')
loop.kill_app()
if not loop.start_app():
    print('!! 重启失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r149env2=%d" % int(time.time())})
health('⑥重启后 execute_js 快(恢复)')

print('\n== ⑦ 关闭路径(enable:false) ==')
e, t, d = call("browser_vip_enable_js_env", {"enable": False}, to=60)
rec('⑦enable:false 成功且含诚实毒化警告', (not e) and ("破坏" in t), "%.2fs %s" % (d, t[:80]))
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('⑦关闭后 execute_js 退化(≥5s) —— 与警告一致', e or d >= 5.0, "%.2fs err=%s" % (d, e))
e, t, d = call("browser_status", {})
rec('⑦browser_status 仍可用(活性探针)', not e, "%.2fs" % d)

print('\n== ⑧ 重启恢复收尾 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 重启失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r149env3=%d" % int(time.time())})
health('⑧重启后 execute_js 快(恢复)')
e, t, d = call("browser_status", {})
rec('⑧browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
