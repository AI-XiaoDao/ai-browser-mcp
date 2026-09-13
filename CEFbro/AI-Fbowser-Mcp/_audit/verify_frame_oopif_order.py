# -*- coding: utf-8 -*-
r"""判定: 存在 OOPIF(跨域框架)时的框架匹配是否**会落到错误的框架**上。

构造(顺序关键): 主框架 -> 跨域 iframe(名 xofr) -> 同源 srcdoc iframe(名 frA, #tgt=AAA) -> 同源 srcdoc(名 frB, #tgt=BBB)。
  CEF 清单: [main, xofr, frA, frB]           (4 条)
  CDP 树  : [main,       frA, frB]           (3 条, **OOPIF 不在其中** —— 本机实测)
于是"按序号对齐"会把 CEF 第 2 项(frA) 映射到 CDP 第 2 项(**frB**) -> 静默读到错误的框架。
本探针的判别臂: 按名/按 id 取 frA, 必须得到 AAA(**不得**得到 BBB); 取 frB 必须得到 BBB。
另: OOPIF 自身(按名 xofr / 按 id 8-)在 CDP 侧无对应项, 必须**如实报错**, 不得回落到主框架内容。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR"
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


def js(expr, frame=None, world=None):
    a = {"code": expr}
    if frame is not None:
        a["frame_id"] = frame
    if world is not None:
        a["world"] = world
    e, t = call("browser_execute_js", a)
    return ('ERR:' if e else '') + val(t)


print('== 造页面: 跨域框架**排在同源框架之前**(这正是会触发错位映射的布局) ==')
call("browser_navigate", {"url": "https://example.com/?oopiforder=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.6)
print('   注入: %s' % js("(function(){"
                        "var x=document.createElement('iframe');x.id='x1';x.name='xofr';"
                        "x.src='https://example.org/';document.body.appendChild(x);"
                        "var a=document.createElement('iframe');a.id='a1';a.name='frA';"
                        "a.srcdoc=\"<input id='tgt' value='AAA'>\";document.body.appendChild(a);"
                        "var b=document.createElement('iframe');b.id='b1';b.name='frB';"
                        "b.srcdoc=\"<input id='tgt' value='BBB'>\";document.body.appendChild(b);"
                        "return 'ok'})()"))
time.sleep(3.0)

e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
print('   CEF 清单(%d): %s' % (len(frames), [f.get('name') or '(main)' for f in frames]))
for f in frames:
    print('      id=%-42s name=%r' % (f.get('id'), f.get('name')))
fidA = next((f.get('id') for f in frames if f.get('name') == 'frA'), None)
fidB = next((f.get('id') for f in frames if f.get('name') == 'frB'), None)
fidX = next((f.get('id') for f in frames if f.get('name') == 'xofr'), None)
print('   frA id=%r  frB id=%r  xofr(OOPIF) id=%r' % (fidA, fidB, fidX))

print('\n== A. ★按名取 frA: 必须是 AAA(OOPIF 在前时, 旧的序号对齐会给出 BBB) ==')
e, t = call("browser_dom_query", {"selector": "#tgt", "attribute": "value", "frame_id": 'frA'})
got = val(t)
print('   frame_id=frA -> %s' % got[:120])
rec('★按名 frA 得到 AAA(未错位到 frB)', (not e) and got == 'AAA', got[:160])

print('\n== B. 按名取 frB: 必须是 BBB ==')
e, t = call("browser_dom_query", {"selector": "#tgt", "attribute": "value", "frame_id": 'frB'})
got = val(t)
print('   frame_id=frB -> %s' % got[:120])
rec('按名 frB 得到 BBB', (not e) and got == 'BBB', got[:160])

print('\n== C. 按 id 取 frA / frB: 与按名一致 ==')
for label, fid, want in (('frA', fidA, 'AAA'), ('frB', fidB, 'BBB')):
    if not fid:
        rec('按 id 取 %s' % label, False, '取不到 id')
        continue
    e, t = call("browser_dom_query", {"selector": "#tgt", "attribute": "value", "frame_id": fid})
    got = val(t)
    print('   frame_id=%s -> %s' % (label, got[:100]))
    rec('按 id 取 %s 得到 %s' % (label, want), (not e) and got == want, got[:160])

print('\n== D. ★OOPIF 自身: CDP 侧够不到时必须如实报错, 不得回落到主框架内容 ==')
for label, fid in (('按名 xofr', 'xofr'), ('按 id', fidX)):
    if not fid:
        continue
    e, t = call("browser_dom_query", {"selector": "#tgt", "attribute": "value", "frame_id": fid})
    got = val(t)
    print('   (%s) isError=%s -> %s' % (label, e, got[:150]))
    rec('OOPIF %s: 明确报错且不含主框架内容' % label,
        e and ('MAIN' not in got), 'isError=%s %s' % (e, got[:160]))

print('\n== E. OOPIF 走原生世界(world=main): 跨域框架也应可达 ==')
if fidX:
    got = js("document.title", fidX, 'main')
    if str(got).startswith('ERR:'):
        # world=main 走原生通道, 偶发回调丢失(约 8%); 如实重试一次并标注
        got = js("document.title", fidX, 'main') + '   [需重试一次(原生通道固有抖动)]'
    print('   browser_execute_js{frame_id=OOPIF, world=main} -> %r' % got)
    rec('★world=main 可读取跨域框架的 document.title', 'Example Domain' in str(got), got)
else:
    rec('★world=main 可读取跨域框架', False, '取不到 OOPIF id')

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
