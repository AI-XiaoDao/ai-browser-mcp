# -*- coding: utf-8 -*-
r"""第152轮: 新工具 browser_by_id + browser_count 受控验收(每工具独立断言)。

判据:
  A. browser_count: 基线=1 → 建后台浏览器后=2(id_list 含新id) → 关闭后=1
  B. browser_by_id: id=1 详情(url/tag/is_closed/hwnd); id=新后台(有 tag) 详情;
     不存在 id → 可行动失败
  C. 全程健康
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


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return {}
    for _ in range(5):
        if isinstance(o, dict):
            if "count" in o or "browser_id" in o or "isError" in o:
                return o
            nxt = o.get("data") or o.get("result")
            if isinstance(nxt, str):
                try:
                    nxt = json.loads(nxt)
                except Exception:
                    return {}
            o = nxt
        else:
            return {}
    return o if isinstance(o, dict) else {}


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r152byid=%d" % int(time.time())})
health('⓪execute_js 快')

print('\n== A. browser_count ==')
e, t, d = call("browser_count", {}, to=60)
p = payload(t)
rec('A①基线 count=1', (not e) and p.get("count") == 1, p)
e, t, d = call("browser_create", {"url": "https://example.com/?bgbyid=1",
                                  "background": True, "tag": "byid_probe_152"}, to=90)
rec('A②创建后台浏览器成功', not e, "%.2fs" % d)
e, t, d = call("browser_count", {}, to=60)
p = payload(t)
rec('A②count=2 且 id_list 含 2', (not e) and p.get("count") == 2 and "2" in (p.get("id_list") or ""), p)

print('\n== B. browser_by_id ==')
e, t, d = call("browser_by_id", {"browser_id": 1}, to=60)
p = payload(t)
rec('B①id=1 详情(含 url/hwnd/is_closed)', (not e) and p.get("browser_id") == 1 and ("url" in p) and ("hwnd" in p) and ("is_closed" in p), p)
e, t, d = call("browser_by_id", {"browser_id": 2}, to=60)
p = payload(t)
rec('B②id=2 详情(tag=byid_probe_152)', (not e) and p.get("browser_id") == 2 and p.get("tag") == "byid_probe_152", p)
e, t, d = call("browser_by_id", {"browser_id": 99999}, to=60)
rec('B③不存在 id → 可行动失败', e and ("不存在" in t or "已关闭" in t), t[:80])
e, t, d = call("browser_by_id", {}, to=60)
rec('B④缺 browser_id → 拒绝', e and ("browser_id" in t), t[:70])
health('B之后 execute_js 仍快')

print('\n== C. 关闭后台后 count 回落 ==')
e, t, d = call("browser_close", {"browser_id": 2}, to=60)
rec('C①关闭后台浏览器(回读确认)', (not e) and ("回读确认" in t), "%.2fs" % d)
e, t, d = call("browser_count", {}, to=60)
p = payload(t)
rec('C②count 回落到 1', (not e) and p.get("count") == 1, p)
e, t, d = call("browser_by_id", {"browser_id": 2}, to=60)
rec('C③id=2 现在 → 可行动失败(已关闭)', e, t[:70])

print('\n== 收尾 ==')
health('收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
