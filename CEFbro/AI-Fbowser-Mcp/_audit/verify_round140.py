# -*- coding: utf-8 -*-
r"""第140轮验收: ①预注入真生效 ②inject handler 诚实拒绝 ③启动期事件可观测。

修前实测(可复现):
  · `browser_reverse_preload` 注册回 success+identifier, 但导航后哨兵 `undefined`(脚本永不执行);
    三臂对照证明"先 Page.enable 再注册"才生效(A undefined / B、C 都是 C1)。
  · `browser_inject {persist:true,type:handler}` 的代码被当普通页面 JS 执行(哨兵可读) —— 与它承诺的"原生 handler 桥"不符。
  · `app_startup_cmdline` / `app_startup_request_context_ready` 查不到(监控开关默认假 + DB 未就绪时被丢弃)。

用法: py -3 _audit\verify_round140.py
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


def call(n, a=None, to=60):
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


def payload(txt):
    try:
        o = json.loads(txt)
    except Exception:
        return {}
    d = o.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return o if isinstance(o, dict) else {}


def event_count(kind):
    """返回 (条数, 错误文本)。⚠ 回包形态不止一种: data 可能是**列表**(直接是事件数组)、
    也可能是**对象**(含 count/events)。首版只处理对象, 于是"明明有记录"被读成 -1 ——
    探针解析器本身也要当被测对象(与上一轮 payload() 只认字符串同一类错误)。"""
    e, t, _ = call("browser_event", {"event_type": kind, "limit": 50}, to=30)
    if e:
        return -1, t[:70]
    try:
        o = json.loads(t)
    except Exception:
        return -1, t[:70]
    d = o.get("data")
    if isinstance(d, list):
        return len(d), ""
    if isinstance(d, dict):
        for k in ("count", "total", "events_count"):
            if isinstance(d.get(k), int):
                return d[k], ""
        evs = d.get("events")
        if isinstance(evs, list):
            return len(evs), ""
        return -1, json.dumps(d, ensure_ascii=False)[:90]
    return -1, t[:90]


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


print('== 干净实例(启动期事件在重启后立刻查) ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)

print('\n== ③ 启动期事件必须可查(修前两者都是 0/查不到) ==')
for kind in ("app_startup_cmdline", "app_startup_request_context_ready"):
    c, err = event_count(kind)
    rec("%s 有记录(≥1)" % kind, isinstance(c, int) and c >= 1, "count=%s %s" % (c, err))

call("browser_navigate", {"url": "https://example.com/?r140=%d" % int(time.time())})

print('\n== ① 预注入必须真生效(修前哨兵 undefined) ==')
e1, t1, d1 = call("browser_reverse_preload",
                  {"code": "window.__plS140='C1';"}, to=60)
p1 = payload(t1)
rec("preload 调用成功", not e1, "%.2fs" % d1)
rec("回包带 auto_prepared 说明 Page 域自动启用", "Page" in str(p1.get("auto_prepared") or t1), str(p1.get("auto_prepared"))[:60])
call("browser_navigate", {"url": "https://example.com/?r140b=%d" % int(time.time())})
time.sleep(0.6)
e2, t2, _ = call("browser_execute_js", {"code": "String(window.__plS140)", "max_ms": 15000})
rec("新文档里哨兵可读(C1) —— 预注入真的执行了", ("C1" in t2), t2[:90])

print('\n== ①b 预注入不拖慢 JS 通道(修前已测 0.03s, 回归确认) ==')
e3, t3, d3 = call("browser_execute_js", {"code": "1+1"})
rec("execute_js 仍 0.03s 级", (not e3) and d3 < 1.0, "%.2fs" % d3)

print('\n== ② persist:js 仍有效(回归) ==')
call("browser_inject", {"type": "js", "persist": True,
                        "code": "window.__injS140='I1';", "inject_id": "r140"})
call("browser_navigate", {"url": "https://example.com/?r140c=%d" % int(time.time())})
time.sleep(0.5)
e4, t4, _ = call("browser_execute_js", {"code": "String(window.__injS140)", "max_ms": 15000})
rec("persist:js 哨兵可读(I1)", ("I1" in t4), t4[:90])

print('\n== ②b persist:handler 必须**可行动拒绝**(修前静默当普通 JS 跑) ==')
e5, t5, d5 = call("browser_inject", {"type": "handler", "persist": True,
                                     "code": "window.__hS140='H1';", "inject_id": "r140h"})
rec("handler 模式被明确拒绝", e5, "%.2fs %s" % (d5, t5[:80]))
missing = [k for k in ("type:js", "browser_reverse_preload", "browser_execute_js") if k not in t5]
rec("拒绝文案给出替代(type=js / reverse_preload / execute_js)", not missing,
    "缺失=%s | 全文长度=%d" % (missing, len(t5)))
if missing:
    print('      拒绝文案全文: %s' % t5)
call("browser_reload", {"ignore_cache": True})
time.sleep(0.5)
e6, t6, _ = call("browser_execute_js", {"code": "String(window.__hS140)", "max_ms": 15000})
rec("handler 的代码确实没有被注入(哨兵 undefined)", ("undefined" in t6), t6[:80])

print('\n== ④ 收尾健康 ==')
e7, t7, d7 = call("browser_status", {}, to=30)
rec("browser_status 可用", (not e7), "%.2fs" % d7)
e8, t8, _ = call("browser_event", {"limit": 5}, to=30)
rec("事件时间线可读", (not e8) and len(t8) > 10, t8[:60])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
