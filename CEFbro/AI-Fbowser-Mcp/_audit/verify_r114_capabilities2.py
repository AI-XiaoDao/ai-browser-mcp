# -*- coding: utf-8 -*-
"""本轮验收(修正版探针): URI 解码兜底 / 编码 use_plus / frame_by_id / 事件族名通配 / 回归计数。

上一版探针的三个自坑已修: ① frames 载荷解析; ② urlopen 必须用 Request 才能带 headers; ③ 断言要按
工具**真实输出形态**(数字ID/字段名), 不要假设别名回显。
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


def rpc(method, params=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        b["params"] = params
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))


def call(n, a=None, to=90):
    o = rpc("tools/call", {"name": n, "arguments": a or {}}, to)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def flat(t):
    return t.replace('\\"', '"')


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:320]) if detail else ''))


call("browser_navigate", {"url": "https://example.com/?verify114=1", "wait_for_load": True})
time.sleep(0.5)

print('== ① URI 解码(类库解不开 -> 自动页面兜底) ==')
e, t = call("browser_uri_decode", {"data": "a%20b%26c%3Dd"})
f = flat(t)
rec('★一次调用即得完整解码 "a b&c=d"', (not e) and '"decoded":"a b&c=d"' in f, f)
rec('via 如实说明走了页面兜底', '"via":"js:decodeURIComponent"' in f, f)
e, t = call("browser_uri_decode", {"data": "%E4%B8%AD%E6%96%87%20x"})
rec('非 ASCII + 空格一起还原为 "中文 x"', (not e) and '"decoded":"中文 x"' in flat(t), flat(t))
e, t = call("browser_uri_decode", {"data": "no-escapes-here"})
rec('无转义时走类库路径且不报 warning',
    (not e) and '"via":"lib' in flat(t) and 'warning' not in flat(t), flat(t))
e, t = call("browser_uri_decode", {"data": "bad%zz"})
rec('非法转义不崩且如实说明', (not e) and ('warning' in flat(t) or 'bad%zz' in flat(t)), flat(t))

print('\n== ② 编码 use_plus ==')
e, t = call("browser_uri_encode", {"data": "a b", "use_plus": True})
rec('use_plus:true -> "a+b"', (not e) and '"encoded":"a+b"' in flat(t), flat(t))
e, t = call("browser_uri_encode", {"data": "a b"})
rec('缺省 -> "a%20b"', (not e) and '"encoded":"a%20b"' in flat(t), flat(t))

print('\n== ③ browser_frame_by_id ==')
call("browser_execute_js", {"code": "document.body.insertAdjacentHTML('beforeend','<iframe id=mf srcdoc=\"<p>f1</p>\"></iframe>')"})
time.sleep(1.0)
e, t = call("browser_get_frames")
print('   browser_get_frames 原文前 400: %s' % flat(t)[:400])
fids = []
try:
    d = json.loads(flat(t))
    def walk(o):
        if isinstance(o, dict):
            if 'frame_id' in o:
                fids.append((o.get('frame_id'), o.get('is_main'), o.get('url')))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
except Exception as ex:
    print('   解析异常: %r' % ex)
print('   共取到 %d 个 frame_id: %s' % (len(fids), fids[:5]))
real = next((x for x in fids if x[1] is False), None) or (fids[0] if fids else None)
if real:
    e, t = call("browser_frame_by_id", {"frame_id": real[0]})
    rec('真 frame_id -> found:true + url',
        (not e) and '"found":true' in flat(t) and '"url"' in flat(t), flat(t))
else:
    rec('真 frame_id 用例', False, '探针没取到 frame_id')
e, t = call("browser_frame_by_id", {"frame_id": "no-such-frame"})
rec('假 frame_id -> found:false + hint 且不崩',
    (not e) and '"found":false' in flat(t) and 'hint' in flat(t), flat(t))

print('\n== ④ 事件族名通配 ==')
call("browser_collect", {"action": "event_resource_enable"})
call("browser_navigate", {"url": "https://example.com/?evt2=%d" % int(time.time()), "wait_for_load": True})
time.sleep(1.2)
e1, t1 = call("browser_event", {"event_type": "resource_*"})
e2, t2 = call("browser_event", {"event_type": "load_end"})
rec('★族名 resource_* 查到事件', (not e1) and 'resource_response' in flat(t1), flat(t1)[:200])
rec('精确名仍可用', (not e2) and 'load_end' in flat(t2), flat(t2)[:160])

print('\n== ⑤ 回归 ==')
o = rpc("tools/list")
names = [x.get('name') for x in (o.get('result') or {}).get('tools') or []]
rec('工具数 317 且含 browser_frame_by_id',
    len(names) == 317 and 'browser_frame_by_id' in names, '总数=%d' % len(names))
e, t = call("browser_status")
rec('实例健康(未卡死)', (not e) and '"success":true' in flat(t)[:200] or 'browser_id' in flat(t), flat(t)[:120])

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
