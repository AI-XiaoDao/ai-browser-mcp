# -*- coding: utf-8 -*-
r"""第137轮归因探针: 装上 Debugger 插装断点后, JS 通道**真实的**耗时构成是什么?

背景: 装了 `Debugger.setInstrumentationBreakpoint`(beforeScriptExecution)后, 每一次
`Runtime.evaluate` 都会在脚本执行前命中一次暂停 —— 于是一条"派发 → 等结果"的同步命令会
先超时, 再靠 `执行CDP并同步等待` 里的"卡死自救"(resume + 重试)兜住, 每次 ~6-10s。

本探针**不改源码**, 只用**原始 CDP 通道**(`browser_cdp_call` 派发 + `mcp_result` 按命令ID取结果)
把耗时构成量出来, 以便决定自救路径该怎么改:

  A 基线: 未装插装时, 原始 Runtime.evaluate 多久出结果?           (期望 0.03s 级)
  B 装插装后**不 resume**: 结果会不会自己到?                       (期望: 永远不到 → 证明"暂停"是根因)
  C **决定性测量**: 派发 → 等 1s → resume → **继续等同一个任务ID**
    结果是否在 resume 之后立刻到达?  (若到达 ⇒ 正确修法是"在同一任务ID上继续等",
    而不是"重新派发一次", 因为重新派发会再命中一次同样的插装暂停, 于是又要再 resume 一次)
  D 对照: 派发 → 等 1s → resume → **重新派发** → 再等 → 要花多久?  (复现当前实现的 ~6s)

用法: py -3 _audit\probe_iv_timing.py
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
_rid = [8000]


def call(n, a=None, to=90, rid=None):
    """返回 (is_error, text, 耗时秒, 本次实际用的 JSON-RPC id)"""
    if rid is None:
        _rid[0] += 1
        rid = _rid[0]
    b = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                              headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0, rid
    rr = o.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
    return bool(rr.get("isError")), txt, time.time() - t0, rid


def raw_eval(expr="1+1"):
    """派发一条**原始** Runtime.evaluate, 返回该次调用的 JSON-RPC id(结果按命令ID入库)。"""
    p = json.dumps({"expression": expr, "returnByValue": True}, ensure_ascii=False)
    e, t, d, rid = call("browser_cdp_call", {"method": "Runtime.evaluate", "params": p}, to=30)
    return rid, e, t, d


def poll_result(rid, budget=20.0):
    """轮询 mcp_result, 返回 (是否拿到结果, 耗时秒, 文本)。"""
    t0 = time.time()
    while time.time() - t0 < budget:
        e, t, d, _ = call("mcp_result", {"request_id": str(rid)}, to=20)
        if (not e) and t and ("未找到" not in t) and ("等待中" not in t):
            return True, time.time() - t0, t
        time.sleep(0.1)
    return False, time.time() - t0, ""


def line(tag, txt):
    print('  %-46s %s' % (tag, txt))


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
ts = int(time.time())
call("browser_navigate", {"url": "https://example.com/?ivt=%d" % ts})
time.sleep(0.4)

print('\n== A 基线(未装插装): 原始 Runtime.evaluate ==')
rid, e, t, d = raw_eval()
ok, pd, pt = poll_result(rid, 15)
line('A 派发回执', '%.2fs %s' % (d, t[:60]))
line('A 结果到达', '%s %.2fs %s' % ('拿到' if ok else '超时', pd, pt[:70]))
base = pd

print('\n== ① 装插装 ==')
e1, t1, d1, _ = call("browser_reverse_instrument_script",
                     {"action": "install", "confirm": True, "event": "beforeScriptExecution"}, to=90)
line('install', '%s %.2fs %s' % ('ERR' if e1 else 'OK', d1, t1[:70]))

print('\n== B 装插装后**不 resume**: 结果会不会自己到? ==')
rid_b, e, t, d = raw_eval()
line('B 派发回执', '%.2fs %s' % (d, t[:60]))
ok_b, pdb, ptb = poll_result(rid_b, 12)
line('B 结果到达', '%s %.2fs %s' % ('拿到' if ok_b else '不到(暂停中)', pdb, ptb[:70]))

print('\n== C 决定性: 同一任务ID上 resume 后**继续等** ==')
e, t, d, _ = call("browser_debugger_resume", {}, to=30)
line('resume 本身', '%s %.2fs %s' % ('ERR' if e else 'OK', d, t[:70]))
ok_c, pdc, ptc = poll_result(rid_b, 12)
line('C 原任务ID 在 resume 后', '%s %.2fs %s' % ('拿到' if ok_c else '仍不到', pdc, ptc[:70]))

print('\n== D 对照: 派发 → 1s → resume → **重新派发** ==')
t0 = time.time()
rid_d1, e, t, d = raw_eval()
time.sleep(1.0)
_e, _t, _d, _ = call("browser_debugger_resume", {}, to=30)
rid_d2, e2, t2, d2 = raw_eval()
ok_d, pdd, ptd = poll_result(rid_d2, 20)
line('D 重派发后结果', '%s %.2fs (总 %.2fs) %s' % ('拿到' if ok_d else '不到', pdd, time.time() - t0, ptd[:50]))

print('\n== ② 收尾: remove 插装 ==')
e2, t2b, d2b, _ = call("browser_reverse_instrument_script", {"action": "remove"}, to=60)
line('remove', '%s %.2fs %s' % ('ERR' if e2 else 'OK', d2b, t2b[:70]))
rid_z, e, t, d = raw_eval()
ok_z, pdz, ptz = poll_result(rid_z, 10)
line('remove 后原始 evaluate', '%s %.2fs' % ('拿到' if ok_z else '不到', pdz))

print('\n== 汇总 ==')
line('A 基线 结果延迟', '%.2fs' % base)
line('B 不 resume 结果延迟', '%.2fs' % pdb)
line('C resume 后同一任务ID', '%.2fs' % pdc)
line('D 重派发路径', '%.2fs' % pdd)
line('remove 后 结果延迟', '%.2fs' % pdz)
