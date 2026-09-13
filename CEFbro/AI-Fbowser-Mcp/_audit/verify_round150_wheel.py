# -*- coding: utf-8 -*-
r"""第150轮 每轮一测(最后一个): browser_vip_mouse_wheel(内核级滚轮, 已知会毒化 CDP)。

判据:
  ① 基线: 造可滚动页面, scrollY=0, execute_js 快
  ② 守卫: 缺 x/y → 拒绝
  ③ 守卫: 缺 delta_x/delta_y → 拒绝
  ④ 真调用 {x,y,delta_y:400} → 成功
  ⑤ 页面侧回读 scrollY > 0(真滚动; 该回读本身走已毒化通道, 允许 ≤35s 完成)
  ⑥ 毒化与警告一致: 之后 execute_js 退化(≥5s)
  ⑦ 重启恢复(execute_js 快)
  ⑧ 收尾 status
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
call("browser_navigate", {"url": "https://example.com/?r150wheel=%d" % int(time.time())})
e, t, d = call("browser_execute_js",
               {"code": "for(var i=0;i<60;i++){var d=document.createElement('div');d.textContent='row'+i+' '+('x'.repeat(200));document.body.appendChild(d)}window.scrollTo(0,0);'tall'"}, to=60)
rec('①造可滚动页面', (not e) and ("tall" in t), "%.2fs" % d)
e, t, d = call("browser_execute_js", {"code": "window.scrollY"})
rec('①scrollY=0 基线', "0" in t, t[:40])
health('①execute_js 快')

print('\n== ②③ 守卫 ==')
e, t, d = call("browser_vip_mouse_wheel", {"x": 300, "delta_y": 400}, to=60)
rec('②缺 y → 拒绝', e and ("y" in t), t[:80])
e, t, d = call("browser_vip_mouse_wheel", {"x": 300, "y": 200}, to=60)
rec('③缺 delta → 拒绝(不静默滚0)', e and ("delta" in t), t[:80])
health('②③之后 execute_js 仍快(拒绝未毒化)')

print('\n== ④⑤ 真滚动 + 页面侧回读 ==')
e, t, d = call("browser_vip_mouse_wheel", {"x": 300, "y": 200, "delta_y": 400}, to=60)
rec('④真调用成功', not e, "%.2fs %s" % (d, t[:50]))
e, t, d = call("browser_execute_js", {"code": "window.scrollY"}, to=60)
sy = ""
try:
    sy = json.loads(t).get("message", "")
except Exception:
    sy = t
try:
    syv = int(float(sy))
except Exception:
    syv = -1
rec('⑤页面侧 scrollY > 0(真滚动; 回读走已毒化通道, 允许较慢)', syv > 0, "scrollY=%s %.2fs" % (sy, d))

print('\n== ⑥ 毒化与警告一致 ==')
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('⑥滚轮后 execute_js 退化(≥5s) —— 与警告一致', e or d >= 5.0, "%.2fs err=%s" % (d, e))
e, t, d = call("browser_status", {})
rec('⑥browser_status 可用(活性探针)', not e, "%.2fs" % d)

print('\n== ⑦ 重启恢复 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 重启失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r150wheel2=%d" % int(time.time())})
health('⑦重启后 execute_js 快(恢复)')
e, t, d = call("browser_status", {})
rec('⑧browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
