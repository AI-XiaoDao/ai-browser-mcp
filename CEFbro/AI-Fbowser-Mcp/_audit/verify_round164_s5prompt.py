# -*- coding: utf-8 -*-
r"""第164轮: browser_set_proxy 第4参(close_s5_error_prompt)验收。

判据:
  ① 基线健康
  ② tools/list: schema 含 close_s5_error_prompt
  ③ set_proxy {address, close_s5_error_prompt:true} → 成功且回执含该参数
  ④ 立即 clear_proxy 恢复(不留死代理)
  ⑤ 守卫: address 为空 → 拒绝
  ⑥ 收尾健康
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
    print('  [%s] %-58s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r164s5=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ② schema ==')
try:
    b = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
    props = []
    for t in (o.get("result") or {}).get("tools") or []:
        if t.get("name") == "browser_set_proxy":
            props = list(t.get("inputSchema", {}).get("properties", {}).keys())
    rec('②schema 含 close_s5_error_prompt', "close_s5_error_prompt" in props, props)
except Exception as ex:
    rec('②tools/list', False, repr(ex))

print('\n== ③④ set(第4参) → clear 恢复 ==')
e, t, d = call("browser_set_proxy", {"address": "127.0.0.1:1", "close_s5_error_prompt": True}, to=60)
rec('③set_proxy 成功且回执含 close_s5_error_prompt', (not e) and ("close_s5_error_prompt" in t), "%.2fs %s" % (d, t[:90]))
e, t, d = call("browser_clear_proxy", {}, to=60)
rec('④clear_proxy 成功(不留死代理)', not e, "%.2fs %s" % (d, t[:70]))
# 死代理态下清空后的**首次** CDP 调用实测有一次 ~12s 延迟(非持久毒化); 第二次必须恢复 ≤2s。
e1, t1, d1 = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('④清空后首调用(容忍 ≤15s)', (not e1) and d1 <= 15.0, "%.2fs" % d1)
e2, t2, d2 = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('④清空后次调用恢复 ≤2s(非持久毒化)', (not e2) and d2 <= 2.0, "%.2fs" % d2)

print('\n== ⑤ 守卫 ==')
e, t, d = call("browser_set_proxy", {}, to=60)
rec('⑤address 为空 → 拒绝', e and ("address" in t), t[:70])

print('\n== ⑥ 收尾 ==')
health('⑥收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑥browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
