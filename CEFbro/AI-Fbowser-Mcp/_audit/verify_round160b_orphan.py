# -*- coding: utf-8 -*-
r"""第160轮(孤儿对照): 不存在的父ID → 施加失败且 apply_failed 指名(单独首臂, 避开模态约束)。

判据:
  ① 基线健康
  ② set 孤儿规格(item 父ID=99999) → 成功
  ③ arm(本会话第一次菜单打开) → 施加 → get: apply_failed 含 99999(可行动失败)
  ④ 收尾健康
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
            if "apply_failed" in o or "spec_lines" in o:
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
call("browser_navigate", {"url": "https://example.com/?r160b=%d" % int(time.time())})
health('①execute_js 快')

e, t, d = call("browser_context_menu", {"action": "set",
                                        "items": "item|孤儿|26504|1|99999|"}, to=60)
rec('②set 孤儿规格成功', (not e) and payload(t).get("spec_lines") == 1, "%.2fs" % d)
e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
rec('③arm 成功(首臂)', not e, "%.2fs" % d)
e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
p = payload(t)
af = p.get("apply_failed") or ""
rec('③apply_failed 含 99999(可行动失败)', "99999" in af, af[:100])
health('③之后 execute_js 仍快')

print('\n== ④ 收尾 ==')
health('④收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('④browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
