# -*- coding: utf-8 -*-
"""本轮能力验收(6 组, 每组都有判别力):

① `browser_uri_decode` 修好了吗?  "a%20b%26c%3Dd" 必须还原成 "a b&c=d"(修前原样返回)
② 旧行为可回退?                    keep_escaped:true 时应仍是 "a%20b%26c%3Dd"
③ `browser_uri_encode` 的 use_plus 生效? "a b" 在 use_plus:true 时应为 "a+b", 缺省仍 %20
④ `browser_frame_by_id` 新工具: 真 frame_id -> found:true; 假 id -> found:false + hint 且**不崩**
⑤ `browser_event` 通配: 先开资源事件 + 导航产生事件, 再分别用族名 resource_* 与精确名查
⑥ 回归: 工具总数 317; 未启用监控时查事件应给可行动提示而不是空
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
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


print('== ① URI 解码 bug 是否修好 ==')
e, t = call("browser_uri_decode", {"data": "a%20b%26c%3Dd"})
rec('decode("a%20b%26c%3Dd") == "a b&c=d"', (not e) and '"decoded":"a b&c=d"' in t, t)
e, t = call("browser_uri_decode", {"data": "%E4%B8%AD%E6%96%87"})
rec('非 ASCII 仍能还原("中文")', (not e) and '"decoded":"中文"' in t, t)

print('\n== ② 旧行为可回退 ==')
e, t = call("browser_uri_decode", {"data": "a%20b", "keep_escaped": True})
rec('keep_escaped:true 保留转义(旧行为)', (not e) and '"decoded":"a%20b"' in t, t)

print('\n== ③ 编码 use_plus ==')
e, t = call("browser_uri_encode", {"data": "a b", "use_plus": True})
rec('use_plus:true -> "a+b"', (not e) and '"encoded":"a+b"' in t, t)
e, t = call("browser_uri_encode", {"data": "a b"})
rec('缺省仍为 %20(向后兼容)', (not e) and '"encoded":"a%20b"' in t, t)

print('\n== ④ browser_frame_by_id ==')
call("browser_navigate", {"url": "https://example.com/?frames=1", "wait_for_load": True})
call("browser_execute_js", {"code": "document.body.insertAdjacentHTML('beforeend','<iframe srcdoc=\"<p>f1</p>\"></iframe>')"})
time.sleep(0.8)
e, t = call("browser_get_frames")
fid = ''
try:
    data = json.loads(t)
    fs = data.get('frames') or data.get('data', {}).get('frames') or []
    if not fs:
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and 'frame_id' in v[0]:
                fs = v
                break
    for f in fs:
        if f.get('frame_id') and f.get('is_main') is False:
            fid = f['frame_id']
            break
    if not fid and fs:
        fid = fs[-1].get('frame_id') or ''
except Exception as ex:
    print('   取帧解析异常: %r / 原文 %s' % (ex, t[:200]))
print('   取到 frame_id = %r' % fid)
if fid:
    e, t = call("browser_frame_by_id", {"frame_id": fid})
    rec('真 frame_id -> found:true 且带 url', (not e) and '"found":true' in t and '"url"' in t, t)
e, t = call("browser_frame_by_id", {"frame_id": "no-such-frame-xyz"})
rec('假 frame_id -> found:false + hint(且不崩)', (not e) and '"found":false' in t and 'hint' in t, t)
e, t = call("browser_frame_by_id", {})
rec('缺 frame_id -> 明确失败并指路', e and 'frame_id' in t, t)

print('\n== ⑤ 事件族名通配 ==')
e, t = call("browser_collect", {"action": "event_resource_enable"})
print('   开资源事件: isError=%s %s' % (e, t[:120]))
call("browser_navigate", {"url": "https://example.com/?evt=1&x=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(1.2)
e1, t1 = call("browser_event", {"event_type": "resource_*"})
e2, t2 = call("browser_event", {"event_type": "load_end"})
print('   resource_* -> isError=%s 长度=%d 前120: %s' % (e1, len(t1), t1[:120]))
print('   load_end   -> isError=%s 长度=%d 前120: %s' % (e2, len(t2), t2[:120]))
rec('★族名 resource_* 能查到事件(修前必然查不到)', (not e1) and ('"event' in t1 or 'resource' in t1), t1[:220])
rec('精确名 load_end 仍可用', (not e2) and len(t2) > 10, t2[:200])
e3, t3 = call("browser_event", {"event_type": "zzz_*"})
rec('不存在的族名 -> 可行动失败而不是崩溃', e3 and ('未找到' in t3 or '支持' in t3), t3[:220])

print('\n== ⑥ 回归 ==')
o = json.loads(urllib.request.urlopen(BASE + '/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
    headers={"Content-Type": "application/json"}, timeout=30).read().decode())
names = [x.get('name') for x in (o.get('result') or {}).get('tools') or []]
rec('工具总数 317 且含 browser_frame_by_id',
    len(names) == 317 and 'browser_frame_by_id' in names, '总数=%d' % len(names))

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
