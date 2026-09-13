# -*- coding: utf-8 -*-
r"""第161轮: 自建项真值回读验收(取菜单类型/取快捷键, 按命令ID)。

判据:
  ① 基线健康
  ② set 规格: item(26501)+accel 70C / check(26502) / radio(26503,群9) / sub(26504) → 成功
  ③ arm(首臂) → get: last_applied_items≥4; verified_items≥4(四类创建各一条类型回读) 或 ≥5(accel 真值回读)
  ④ apply_failed 为空
  ⑤ 收尾健康
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
call("browser_navigate", {"url": "https://example.com/?r161own=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ② 四类自建项 + accel ==')
spec = ("item|自建项|26501|1|0|70C\ncheck|自建勾|26502|1|0|\nradio|自建单|26503|9|0|\nsub|自建子|26504|1|0|")
e, t, d = call("browser_context_menu", {"action": "set", "items": spec}, to=60)
p = payload(t)
rec('②set 成功(spec_lines=4)', (not e) and p.get("spec_lines") == 4, p)

print('\n== ③ arm → 施加摘要(真值回读) ==')
e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
rec('③arm 成功(首臂)', not e, "%.2fs" % d)
e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
p = payload(t)
rec('③last_applied_items≥4', (p.get("last_applied_items") or 0) >= 4, "applied=%s" % p.get("last_applied_items"))
rec('③verified_items≥4(四类类型回读+item 父ID/accel 视情况)', (p.get("verified_items") or 0) >= 4,
    "verified=%s" % p.get("verified_items"))
af = p.get("apply_failed") or ""
print('  [INFO] apply_failed=%s' % af)
rec('③apply_failed 为空(类型回读全过)', af == "", af[:100])
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
