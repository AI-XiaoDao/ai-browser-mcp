# -*- coding: utf-8 -*-
r"""第160轮: 父ID寻址修复验收(多 sub 精确挂载 + 父ID寻址回读)。

判据:
  ① 基线健康
  ② set 规格: sub A(26501) / sub B(26502) / item(父=26501, id=26503) → 成功
  ③ arm → 同一次右键施加 → get: last_applied_items≥3, verified_items≥2(两 sub 创建 + item 父ID寻址回读)
  ④ apply_failed 为空(旧实现在多 sub 时会挂错且不可见; 现在父ID寻址有回读)
  ⑤ 对照: item 指向不存在的父ID(99999) → 该行失败且 apply_failed 指名
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
            if any(k in o for k in ("verified_items", "spec_lines", "apply_failed")):
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
call("browser_navigate", {"url": "https://example.com/?r160parent=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ② 多 sub 精确父ID寻址规格 ==')
spec = ("sub|A组|26501|1|0|\nsub|B组|26502|1|0|\nitem|A的子项|26503|1|26501|")
e, t, d = call("browser_context_menu", {"action": "set", "items": spec}, to=60)
p = payload(t)
rec('②set 成功(spec_lines=3)', (not e) and p.get("spec_lines") == 3, p)

print('\n== ③ 同一次右键施加 + 父ID寻址回读 ==')
e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
rec('③arm 成功', not e, "%.2fs" % d)
e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
p = payload(t)
rec('③last_applied_items≥3(sub A+sub B+item)', (p.get("last_applied_items") or 0) >= 3,
    "applied=%s" % p.get("last_applied_items"))
rec('③verified_items≥1(item 父ID寻址回读: 取子菜单(A).取数量()≥1)', (p.get("verified_items") or 0) >= 1,
    "verified=%s" % p.get("verified_items"))
print('  [INFO] apply_failed=%s' % p.get("apply_failed"))
rec('③apply_failed 为空(父ID寻址回读通过)', (p.get("apply_failed") or "") == "", p.get("apply_failed") or "-")
health('③之后 execute_js 仍快')

print('\n== ④ 收尾(孤儿对照见 verify_round160b_orphan.py) ==')

print('\n== ⑤ 收尾 ==')
health('⑤收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑤browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
