# -*- coding: utf-8 -*-
r"""第144轮 每轮一测: browser_close_try(受控环境, 绝不触发主窗口关闭)。

判据:
  ① 基线: execute_js 快 + status 可用
  ② 创建后台第二浏览器 → 新 id(≠1)
  ③ browser_close_try{browser_id:新id} → 成功且带「回读确认」(转发 browser_close 的关闭回读)
  ④ browser_list 回读: 该 id 消失(真关了)
  ⑤ 主实例不受影响
  ⑥ 守卫: 不带 browser_id(主窗口) 且无 confirm → 拒绝且文案含 confirm:true 与替代
  ⑦ 守卫: browser_id=1(主窗口) 无 confirm → 同拒
  ⑧ 负控: browser_id=99999 → 可行动失败(目标不存在)
  ⑨ 收尾健康
(刻意不测 confirm:true 的主窗口路径: 它会退出整个 MCP 服务, 属设计行为, 台账注释已有记录)
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
    print('  [%s] %-54s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.0):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


def list_ids():
    e, t, d = call("browser_list", {}, to=60)
    ids = []
    if not e:
        try:
            o = json.loads(t)
            data = o.get("data") or o
            if isinstance(data, str):
                data = json.loads(data)
            for br in (data.get("browsers") or []):
                ids.append(br.get("id"))
        except Exception:
            pass
    return e, t, ids


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r144ct=%d" % int(time.time())})
health('①基线 execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)

print('\n== ② 创建后台第二浏览器 ==')
e, t, d = call("browser_create", {"url": "https://example.com/?bgct=1",
                                  "background": True, "tag": "close_try_probe_144"}, to=90)
rec('②browser_create(background) 成功', not e, "%.2fs" % d)
e, t, ids0 = list_ids()
new_ids = [i for i in ids0 if i != 1]
rec('②browser_list 可见新 id(≠1)', len(new_ids) >= 1, "ids=%s" % ids0)
nid = new_ids[0] if new_ids else 0

print('\n== ③ 关闭非主浏览器(无需 confirm) ==')
if nid:
    e, t, d = call("browser_close_try", {"browser_id": nid}, to=60)
    rec('③browser_close_try 成功且带回读确认', (not e) and (str(nid) in t) and ("回读确认" in t),
        "%.2fs %s" % (d, t[:70]))
    e, t, ids1 = list_ids()
    rec('④目标 id 已从列表消失(真关了)', nid not in ids1, "ids=%s (原 %s)" % (ids1, ids0))
    health('⑤execute_js 仍快(主实例不受影响)')
    e, t, d = call("browser_status", {})
    rec('⑤browser_status 可用', not e, "%.2fs" % d)
else:
    rec('③browser_close_try 成功且带回读确认', False, '未取到新 id')
    rec('④目标 id 已消失', False, '')
    rec('⑤execute_js 仍快', False, '')

print('\n== ⑥/⑦ 主窗口守卫(无 confirm 必须拒绝) ==')
e, t, d = call("browser_close_try", {}, to=60)
rec('⑥不带 browser_id → 拒绝且含 confirm:true 与替代', e and ("confirm:true" in t) and ("browser_id" in t),
    "%.2fs %s" % (d, t[:80]))
e, t, d = call("browser_close_try", {"browser_id": 1}, to=60)
rec('⑦browser_id=1(主窗口) → 同拒', e and ("confirm:true" in t), "%.2fs %s" % (d, t[:80]))
health('⑥⑦之后 execute_js 仍快')

print('\n== ⑧ 负控: 不存在的 id ==')
e, t, d = call("browser_close_try", {"browser_id": 99999}, to=60)
rec('⑧browser_close_try{99999} → 可行动失败(目标不存在)', e and ("不可用" in t or "已关闭" in t),
    "%.2fs %s" % (d, t[:80]))
health('⑧之后 execute_js 仍快')

print('\n== ⑨ 收尾 ==')
health('⑨收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑨browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
