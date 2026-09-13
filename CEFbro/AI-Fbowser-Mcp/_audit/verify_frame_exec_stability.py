# -*- coding: utf-8 -*-
r"""稳定性量测: browser_execute_js {frame_id} 连续多次调用是否**每次都成功**。

用户的首要要求是"一次调用就稳定成功"。故此脚本不测能力, 只测**重复性**:
  · 同一 frame_id(按 id / 按名 / 按序号)各连续调用 6 次, 逐次记录值与耗时;
  · 任何一次失败都必须打印**原始回包**, 便于判断是原生回调丢失、框架解析失败还是同步等待超时。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
N = 6
R = []


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


BUILD = '''(function(){
  document.body.insertAdjacentHTML('beforeend',"<input id='tgt' value='MAIN'>");
  var f1=document.createElement('iframe');
  f1.id='fr1'; f1.name='mcpfr';
  f1.srcdoc="<input id='tgt' value='IFRAME1'><iframe id='fr2' name='mcpfr2' srcdoc=\\"<input id='tgt' value='IFRAME2'>\\"></iframe>";
  document.body.appendChild(f1);
  return 'built';
})()'''

print('== 造页面 ==')
call("browser_navigate", {"url": "https://example.com/?stab=%d" % int(time.time()),
                          "wait_for_load": True})
call("browser_execute_js", {"code": BUILD})
time.sleep(1.5)
e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
out_f = next((f for f in frames if f.get('name') == 'mcpfr'), None)
nest_f = next((f for f in frames if f.get('name') == 'mcpfr2'), None)
print('   外层 id=%r 嵌套 id=%r' % ((out_f or {}).get('id'), (nest_f or {}).get('id')))

CASES = [
    ('外层/按id', (out_f or {}).get('id'), 'IFRAME1'),
    ('外层/按名', 'mcpfr', 'IFRAME1'),
    ('嵌套/按id', (nest_f or {}).get('id'), 'IFRAME2'),
    ('嵌套/按序号', '2', 'IFRAME2'),
    ('外层/world=main', (out_f or {}).get('id'), 'IFRAME1'),
]
for c in CASES:
    if not c[1]:
        print('   [SKIP] %s' % c[0])
CASES = [c for c in CASES if c[1]]

for label, fid, expect in CASES:
    okn = 0
    times = []
    use_main = 'world=main' in label
    for i in range(N):
        a = {"code": "document.querySelector('#tgt').value"}
        if fid is not None:
            a["frame_id"] = fid
        if use_main:
            a["world"] = "main"
        t0 = time.time()
        e, t = call("browser_execute_js", a)
        dt = time.time() - t0
        times.append(dt)
        got = val(t)
        good = (not e) and got == expect
        okn += 1 if good else 0
        if not good:
            print('      ✗ 第%d次 %.2fs isError=%s 原始回包: %s' % (i + 1, dt, e, t[:300]))
    R.append((label, okn == N))
    print('   [%s] %-16s %d/%d 通过, 耗时 %.2f~%.2fs (均 %.2fs)'
          % ('PASS' if okn == N else 'FAIL', label, okn, N, min(times), max(times),
             sum(times) / len(times)))

print('\n==== 稳定性: %d/%d 组全绿(缺省/隔离世界应全绿; world=main 走原生通道, 见回包注记) ===='
      % (sum(1 for _, v in R if v), len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
