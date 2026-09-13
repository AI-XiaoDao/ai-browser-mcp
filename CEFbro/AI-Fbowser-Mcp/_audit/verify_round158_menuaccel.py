# -*- coding: utf-8 -*-
r"""第158轮: 菜单索引真值回读验收(修正版: 单次 arm 同时验证快照与施加)。

判据:
  ① 基线健康
  ② set 规格(仅 accelat@0 70C) → 成功(spec_lines=1)
  ③ arm 快照: has_accel=true 的条目带 accel{key_code,shift,ctrl,alt} 且至少一个 key_code>0
  ④ 同一次右键施加: get → verified_items=1(accelat 真值回读核对) 且 apply_failed 为空
  ⑤ set 期守卫: 索引列填命令ID(26501) → 拒绝
  ⑥ 收尾健康
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
    print('  [%s] %-58s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return {}
    for _ in range(5):
        if isinstance(o, dict):
            if any(k in o for k in ("items", "verified_items", "spec_lines", "applied")):
                return o
            nxt = o.get("data") or o.get("result")
            if isinstance(nxt, str):
                try:
                    nxt = json.loads(nxt)
                except Exception:
                    return {}
            o = nxt
        else:
            return {}
    return o if isinstance(o, dict) else {}


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r158b=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ② 预置规格(仅 accelat@0 70C) ==')
e, t, d = call("browser_context_menu", {"action": "set", "items": "accelat||0|1|0|70C"}, to=60)
p = payload(t)
rec('②set 成功(spec_lines=1)', (not e) and p.get("spec_lines") == 1, p)

print('\n== ③ arm 快照: accel 四元组(施加前状态) ==')
e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
rec('③arm 成功', not e, "%.2fs" % d)
e, t, d = call("browser_menu_probe", {"action": "get", "wait_ms": 800}, to=90)
p = payload(t)
items = p.get("items") or []
accel_items = [i for i in items if i.get("has_accel")]
with_accel = [i for i in accel_items if isinstance(i.get("accel"), dict)]
rec('③items 数与 read_count 一致', len(items) == p.get("read_count"), "items=%s read=%s" % (len(items), p.get("read_count")))
rec('③带快捷键条目都带 accel 四元组', len(with_accel) == len(accel_items), "accel_items=%s" % len(accel_items))
any_kc = any(isinstance(i.get("accel", {}).get("key_code"), int) and i.get("accel", {}).get("key_code", 0) > 0 for i in with_accel)
rec('③至少一个 accel.key_code>0(真值)', any_kc, with_accel[:1])

print('\n== ④ 同一次右键的施加: accelat 真值回读 ==')
e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
p = payload(t)
vi = p.get("verified_items")
af = p.get("apply_failed") or ""
rec('④verified_items=1(accelat 真值核对通过)', vi == 1, "verified=%s" % vi)
rec('④apply_failed 为空(无失败行)', af == "", af[:80])

print('\n== ⑤ set 期守卫 ==')
e, t, d = call("browser_context_menu", {"action": "set", "items": "accelat||26501|1|0|70C"}, to=60)
rec('⑤索引列填命令ID(26501) → 拒绝', e and ("accelat" in t), t[:90])

print('\n== ⑥ 收尾 ==')
health('⑥收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑥browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
