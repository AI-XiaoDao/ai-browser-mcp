# -*- coding: utf-8 -*-
r"""验证第137轮: 装上插装后, 本会话的 JS 通道**仍可继续使用**(实施 §156 的验收标准)。

判据(§156.4, 缺一不算完成):
  ① install(confirm:true) 成功;
  ② 随后 browser_execute_js **成功且 < 5s**(修改前实测: 60s 超时失败);
  ③ **连续 3 次** execute_js 都成功(证明可连续使用, 而不是只能跑一次);
  ④ dom_query 也恢复可用(<5s);
  ⑤ action=remove 后通道回到 0.03s 级;
  ⑥ 全程实例健康(browser_status 可用)。

用法: py -3 _audit\verify_round137.py
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
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?iv=%d" % int(time.time())})
_e, _t, d0 = call("browser_execute_js", {"code": "1+1"})
print('   基线 execute_js: %.2fs' % d0)

print('\n== ① install(带 confirm) ==')
e1, t1, d1 = call("browser_reverse_instrument_script",
                  {"action": "install", "confirm": True, "event": "beforeScriptExecution"}, to=90)
rec("install 成功", not e1, "%.2fs %s" % (d1, t1[:70]))

print('\n== ②③ 装上后 JS 通道是否仍可用(关键) ==')
times = []
for i in (1, 2, 3):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    times.append(d)
    rec("第%d次 execute_js 成功且 <5s" % i, (not e) and d < 5.0 and ("2" in t), "%.2fs %s" % (d, t[:40]))
e4, t4, d4 = call("browser_dom_query", {"selector": "h1"}, to=60)
rec("dom_query 同样恢复(<5s)", (not e4) and d4 < 5.0, "%.2fs %s" % (d4, t4[:50]))

print('\n== ⑤ remove 后通道回到 0.03s 级 ==')
e5, t5, d5 = call("browser_reverse_instrument_script", {"action": "remove"}, to=60)
rec("remove 调用完成", not e5, "%.2fs %s" % (d5, t5[:60]))
time.sleep(0.5)
e6, t6, d6 = call("browser_execute_js", {"code": "1+1"}, to=60)
rec("remove 后 execute_js 快(<1s)", (not e6) and d6 < 1.0, "%.2fs" % d6)

print('\n== ⑥ 实例健康 ==')
e7, t7, d7 = call("browser_status", {}, to=60)
rec("browser_status 可用", (not e7), "%.2fs %s" % (d7, t7[:50]))

print('\n   (install 后三次耗时: %s)' % [round(x, 2) for x in times])
bad = [x for x, o in RES if not o]
print('结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
