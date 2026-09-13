# -*- coding: utf-8 -*-
r"""第143轮 每轮一测: browser_close(受控环境, 绝不关主实例)。

判据:
  ① 干净基线: execute_js 快 + status 可用
  ② browser_create{background:true, tag} → 成功, 拿新浏览器 id(≠1)
  ③ browser_close{browser_id:新id} → 成功且回包含该 id
  ④ browser_list 回读: 该 id 已消失(真关了)
  ⑤ 主实例不受影响: execute_js 快 + status 可用
  ⑥ 负控: browser_close{browser_id:99999} → 可行动失败(目标不存在, 允许类)
  ⑦ 收尾健康
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
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


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
call("browser_navigate", {"url": "https://example.com/?r143close=%d" % int(time.time())})
health('①基线 execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)

print('\n== ② 创建后台第二浏览器 ==')
e, t, d = call("browser_create", {"url": "https://example.com/?bgclose=1",
                                  "background": True, "tag": "close_probe_143"}, to=90)
rec('②browser_create(background) 成功', not e, "%.2fs %s" % (d, t[:70]))
e, t, ids0 = list_ids()
new_ids = [i for i in ids0 if i != 1]
rec('②browser_list 可见新 id(≠1)', len(new_ids) >= 1, "ids=%s" % ids0)
nid = new_ids[0] if new_ids else 0

print('\n== ③ 关闭目标浏览器 ==')
if nid:
    e, t, d = call("browser_close", {"browser_id": nid}, to=60)
    rec('③browser_close 成功且回含 id+回读确认', (not e) and (str(nid) in t) and ("回读确认" in t), "%.2fs %s" % (d, t[:70]))

    print('\n== ④ browser_list 回读: 已真关 ==')
    e, t, ids1 = list_ids()
    rec('④目标 id 已从列表消失', nid not in ids1, "ids=%s (原 %s)" % (ids1, ids0))

    print('\n== ⑤ 主实例不受影响 ==')
    health('⑤execute_js 仍快')
    e, t, d = call("browser_status", {})
    rec('⑤browser_status 可用', not e, "%.2fs" % d)
else:
    rec('③browser_close 成功且回包含 id', False, '未取到新 id')
    rec('④目标 id 已从列表消失', False, '')
    rec('⑤execute_js 仍快', False, '')

print('\n== ⑥ 负控: 关不存在的 id ==')
e, t, d = call("browser_close", {"browser_id": 99999}, to=60)
rec('⑥browser_close{99999} → 可行动失败(目标不存在)', e and ("不可用" in t or "已关闭" in t), "%.2fs %s" % (d, t[:80]))
health('⑥之后 execute_js 仍快')

print('\n== ⑦ 收尾 ==')
health('⑦收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑦browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
