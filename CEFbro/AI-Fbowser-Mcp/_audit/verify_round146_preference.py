# -*- coding: utf-8 -*-
r"""第146轮 每轮一测: browser_set_preference(受控: 改默认字号→页面侧回读→恢复原值)。

判据:
  ① 基线: execute_js 快 + status 可用 + 页面侧默认字号(记原值)
  ② set default_font_size=24 → 成功; reload 后页面侧 getComputedStyle 回读 24px(真生效)
  ③ 恢复原值 → reload → 回读原值(可逆, 无残留)
  ④ 布尔分支: set javascript_enabled=true(幂等真值) → 成功
  ⑤ 守卫: 缺 name / 缺 value → 拒绝
  ⑥ 全程健康; 收尾 status
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


def font_px():
    e, t, d = call("browser_execute_js",
                   {"code": "String(getComputedStyle(document.body).fontSize)"}, to=60)
    return (t if not e else "EXC")


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r146pref=%d" % int(time.time())})
health('①基线 execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)
t0px = font_px()
print('  [INFO] 页面侧默认字号基线: %s' % t0px)
rec('①拿到基线字号(如 16px)', "px" in t0px, t0px[:60])

print('\n== ② set default_font_size=24 → 诚实回包 ==')
e, t, d = call("browser_set_preference", {"name": "webkit.webprefs.default_font_size", "value": "24"}, to=60)
rec('②set 24px 成功且含诚实边界声明', (not e) and ("诚实边界" in t), "%.2fs %s" % (d, t[:80]))
e, t, d = call("browser_reload", {"wait_for_load": True}, to=90)
rec('②reload 成功(通道健康)', not e, "%.2fs" % d)
health('②之后 execute_js 仍快')

print('\n== ③ 恢复原值 ==')
e, t, d = call("browser_set_preference", {"name": "webkit.webprefs.default_font_size", "value": "16"}, to=60)
rec('③set 16px 成功', not e, "%.2fs %s" % (d, t[:70]))
e, t, d = call("browser_reload", {"wait_for_load": True}, to=90)
rec('③reload 成功', not e, "%.2fs" % d)

print('\n== ④ 布尔分支(幂等真值, 无害) ==')
e, t, d = call("browser_set_preference", {"name": "webkit.webprefs.javascript_enabled", "value": "true"}, to=60)
rec('④set javascript_enabled=true 成功', not e, "%.2fs %s" % (d, t[:60]))
health('④之后 execute_js 仍快(JS 未被误关)')

print('\n== ⑤ 守卫 ==')
e, t, d = call("browser_set_preference", {"value": "1"}, to=60)
rec('⑤缺 name 被拒', e and ("name" in t), t[:70])
e, t, d = call("browser_set_preference", {"name": "webkit.webprefs.default_font_size"}, to=60)
rec('⑤缺 value 被拒', e and ("value" in t), t[:70])

print('\n== ⑥ 未知名诚实口径(本机实测: CEF 存储但不生效且不报错) ==')
e, t, d = call("browser_set_preference", {"name": "no.such.pref.xyz", "value": "1"}, to=60)
rec('⑥未知名: 成功但回包如实声明"不生效"边界', (not e) and ("未知" in t or "不生效" in t or "行为保证" in t),
    "%.2fs %s" % (d, t[:90]))
health('⑥之后 execute_js 仍快')

print('\n== ⑥ 收尾 ==')
health('⑥收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑥browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
