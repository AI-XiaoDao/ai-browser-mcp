# -*- coding: utf-8 -*-
r"""第147轮 每轮一测: browser_set_s5_proxy(受控对照: 死端口代理阻断导航 → 清除恢复)。

判据:
  ① 基线: 导航成功 + execute_js 快 + status 可用
  ② set_s5_proxy 127.0.0.1:1(死端口) → 成功且含"刷新"
  ③ 设置后新导航(异源带唯一标记) → 失败(被代理阻断, 行为级生效证明)
  ④ 代理设置本身不毒化 CDP: execute_js 仍快
  ⑤ clear_s5_proxy → 成功
  ⑥ 清除后同导航 → 成功且 location.href 含唯一标记(恢复)
  ⑦ 守卫: address 为空被拒
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
MARK = "s5block%d" % int(time.time())


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


def href():
    e, t, d = call("browser_execute_js", {"code": "String(location.href)"}, to=60)
    return t


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
e, t, d = call("browser_navigate", {"url": "https://example.com/?r147s5=%d" % int(time.time())}, to=90)
rec('①基线导航成功', not e, "%.2fs" % d)
health('①execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)

print('\n== ② 设置死端口 S5 代理 ==')
e, t, d = call("browser_set_s5_proxy", {"address": "127.0.0.1:1"}, to=60)
rec('②set_s5_proxy 成功且含"刷新"', (not e) and ("刷新" in t), "%.2fs %s" % (d, t[:70]))

print('\n== ③ 代理生效的行为级证明: 新导航被阻断 ==')
e, t, d = call("browser_navigate", {"url": "https://example.net/?%s=1" % MARK,
                                    "wait_for_load": True}, to=90)
time.sleep(1.5)
t_href = href()
rec('③设置后异源导航被死代理阻断(页面落入错误页, 未达目标)', MARK not in t_href and "error" in t_href,
    "href=%s" % t_href[:80])

print('\n== ④ 代理设置不毒化 CDP ==')
health('④execute_js 仍快')
e, t, d = call("browser_status", {})
rec('④browser_status 可用', not e, "%.2fs" % d)

print('\n== ⑤ 清除 S5 代理 ==')
e, t, d = call("browser_vip_clear_s5_proxy", {}, to=60)
rec('⑤clear_s5_proxy 成功', not e, "%.2fs %s" % (d, t[:70]))

print('\n== ⑥ 清除后同导航恢复(轮询 href) ==')
e, t, d = call("browser_navigate", {"url": "https://example.net/?%s=1" % MARK,
                                    "wait_for_load": True}, to=90)
rec('⑥清除后同导航成功', not e, "%.2fs" % d)
ok6 = False
t_href2 = ""
for _ in range(12):
    t_href2 = href()
    if MARK in t_href2:
        ok6 = True
        break
    time.sleep(0.5)
rec('⑥location.href 含唯一标记(真恢复)', ok6, t_href2[:80])
health('⑥之后 execute_js 仍快')

print('\n== ⑦ 守卫 ==')
e, t, d = call("browser_set_s5_proxy", {}, to=60)
rec('⑦address 为空被拒', e and ("address" in t), t[:70])

print('\n== ⑧ 收尾 ==')
health('⑧收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑧browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
