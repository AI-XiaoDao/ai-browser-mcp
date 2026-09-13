# -*- coding: utf-8 -*-
r"""判定: world=main 偶发失败到底是"回调**丢失**"还是"回调**迟到**"(决定该给多长预算、以及是否该自动重试)。

方法: 同一表达式连续调用, 只改 max_ms(5000 / 30000 / 60000), 统计成功率与耗时分布。
判读:
  · 若长预算下成功率升到 100% 且耗时明显变大 -> 是"迟到", 用足够预算即可稳定(不必自动重试, 避免副作用跑两遍);
  · 若长预算下仍失败 -> 是"丢失", 只能如实报错 + 明确提示"该段代码可能已执行也可能没执行", 不能盲目重跑。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
N = 8


def call(n, a=None, to=180):
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


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


call("browser_navigate", {"url": "https://example.com/?budget=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.8)
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"bfr\" name=\"budgetfr\" srcdoc=\"<div id=t>BUDGET_FRAME</div>\"></iframe>');'ok'"})
time.sleep(1.2)
e, t = call("browser_get_frames", {})
sub = next((f for f in (json.loads(t).get("frames") or []) if f.get('name') == 'budgetfr'), None)
fid = (sub or {}).get('id')
print('子框架 id=%r' % fid)

for budget in (5000, 30000, 60000):
    ok = 0
    ts = []
    fails = []
    for i in range(N):
        t0 = time.time()
        e, t = call("browser_execute_js",
                    {"code": "document.getElementById('t').textContent",
                     "frame_id": fid, "world": "main", "max_ms": budget})
        dt = time.time() - t0
        ts.append(dt)
        got = val(t)
        if (not e) and got == 'BUDGET_FRAME':
            ok += 1
        else:
            fails.append((i + 1, round(dt, 2), got[:90]))
    print('   max_ms=%-6d %d/%d 成功 | 耗时 %.2f~%.2fs' % (budget, ok, N, min(ts), max(ts)))
    for f in fails:
        print('        ✗ 第%d次 %.2fs %s' % f)
