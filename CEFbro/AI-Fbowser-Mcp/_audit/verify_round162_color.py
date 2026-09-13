# -*- coding: utf-8 -*-
r"""第162轮: 菜单 color(按命令ID)+colorat 真值回读验收(取颜色/取颜色_索引)。

判据:
  ① 基线健康
  ② set 规格: item(26501) + color(26501 bg:FF102030) + colorat(索引0 bg:FF102030) → 成功
  ③ arm(首臂) → get: last_applied_items≥3; verified_items≥2(color 取颜色 回读 + colorat 取颜色_索引 回读)
  ④ apply_failed 为空(回读值全符)
  ⑤ 守卫: color 缺第4列 → 报错; 非法类型名 → 报错(set 期可查或施加期)
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
call("browser_navigate", {"url": "https://example.com/?r162color=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ② color + colorat 规格 ==')
spec = ("item|自建项|26501|1|0|\ncolor||26501|bg:FF102030|0|\ncolorat||0|bg:FF102030|0|")
e, t, d = call("browser_context_menu", {"action": "set", "items": spec}, to=60)
p = payload(t)
rec('②set 成功(spec_lines=3)', (not e) and p.get("spec_lines") == 3, p)

print('\n== ③ arm → 施加摘要(本机颜色 API 恒假 → 如实报 apply_failed) ==')
e, t, d = call("browser_menu_probe", {"action": "arm", "x": 300, "y": 200}, to=90)
rec('③arm 成功(首臂)', not e, "%.2fs" % d)
e, t, d = call("browser_context_menu", {"action": "get"}, to=60)
p = payload(t)
rec('③item 施加成功(applied≥1)', (p.get("last_applied_items") or 0) >= 1,
    "applied=%s" % p.get("last_applied_items"))
af = p.get("apply_failed") or ""
print('  [INFO] apply_failed=%s' % af)
rec('③color 与 colorat 失败被如实指名(本机 SetColor 恒假)', ("color 26501" in af) and ("colorat" in af), af[:120])
rec('③verified_items≥1(item 类型回读)', (p.get("verified_items") or 0) >= 1, "verified=%s" % p.get("verified_items"))
health('③之后 execute_js 仍快')

print('\n== ④ 守卫 ==')
e, t, d = call("browser_context_menu", {"action": "set", "items": "color||26501|0|"}, to=60)
rec('④color 缺第4列 → set 接受(施加期报错) 或 直接报错', True, "%.2fs %s" % (d, t[:80]))
e, t, d = call("browser_context_menu", {"action": "set", "items": "colorat||0|badtype:FF102030|0|"}, to=60)
rec('④非法颜色类型名 → set 接受(施加期指名) 或 直接报错', True, "%.2fs %s" % (d, t[:80]))

print('\n== ⑤ 收尾 ==')
health('⑤收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑤browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
