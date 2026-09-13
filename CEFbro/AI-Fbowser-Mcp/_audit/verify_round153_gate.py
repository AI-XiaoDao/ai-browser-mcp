# -*- coding: utf-8 -*-
r"""第153轮: 事件族双闸假成功修复验收(用 browser_event 两支提示文案做 oracle)。

判据:
  ① 基线: browser_event{event_type:"app_extension_created"} → 返回"开关未开启"提示(总闸默认假, 对照臂)
  ② browser_collect action=event_extension_enable → 成功且回执含"总闸"说明
  ③ 修复后: 同查询 → 返回"已开启但无记录"(总闸已开, 诚实可行动) —— 证明族开关现在会同时打开总闸
  ④ 全程健康; 收尾 status
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
call("browser_navigate", {"url": "https://example.com/?r153gate=%d" % int(time.time())})
health('①execute_js 快')

print('\n== ① 对照臂: 基线查询提示可行动(含应用事件说明) ==')
e, t, d = call("browser_event", {"event_type": "app_extension_created"}, to=60)
rec('①基线查询 → 可行动提示(含 应用事件)', e and ("应用事件" in t), t[:100])

print('\n== ② 开扩展族(修复后应同时开总闸) ==')
e, t, d = call("browser_collect", {"action": "event_extension_enable"}, to=60)
rec('②event_extension_enable 成功且回执含"总闸"', (not e) and ("总闸" in t), "%.2fs %s" % (d, t[:80]))

print('\n== ③ 修复后同查询 → 提示"已开启但无记录"(诚实) ==')
e, t, d = call("browser_event", {"event_type": "app_extension_created"}, to=60)
rec('③查询转为"已开启但该事件无记录"(总闸已开)', e and ("已开启" in t or "无记录" in t), t[:100])
health('③之后 execute_js 仍快')

print('\n== ④ 收尾 ==')
health('④收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('④browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
