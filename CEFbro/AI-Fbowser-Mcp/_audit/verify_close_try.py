# -*- coding: utf-8 -*-
r"""第138轮验收 B: `browser_close_try` 是否**真的能关闭**(而不是"显示出来却恒失败")。

判据:
  ① 不带 confirm 针对主窗口 → **可行动的拒绝**(提到 confirm:true 与替代), 不再是旧 ⛔ 文案;
  ② 传后台浏览器 id → **真的关掉它**(用 browser_list 前后对照做回读, 不能只看回执);
  ③ 传不存在的 id → 明确失败(可行动), 不得静默成功;
  ④ 带 confirm:true → **真的退出程序**(轮询 browser_status 直到端口不可用, 这是功能证明);
  ⑤ 重启后实例健康; 且 tools/list 里该工具 schema 三个参数都在(改 schema 必须运行期复核)。

用法: py -3 _audit\verify_close_try.py
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


def call(n, a=None, to=60, quiet=False):
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
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:112]))


def browser_ids():
    e, t, _ = call("browser_list", {})
    if e:
        return []
    try:
        o = json.loads(t)
    except Exception:
        return []
    d = o.get("data") if isinstance(o.get("data"), dict) else o
    lst = d.get("browsers") or d.get("list") or d.get("ids") or []
    out = []
    for it in lst:
        if isinstance(it, dict):
            v = it.get("id", it.get("browser_id"))
            if isinstance(v, int):
                out.append(v)
        elif isinstance(it, int):
            out.append(it)
    return out


print('== tools/list: 三个参数必须都声明 ==')
try:
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode(),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    tool = [x for x in ((o.get("result") or {}).get("tools") or []) if x.get("name") == "browser_close_try"]
    props = ((tool[0].get("inputSchema") or {}).get("properties") or {}) if tool else {}
    rec("browser_close_try 已注册且 schema 有 browser_id/confirm/delay_seconds",
        set(props) >= {"browser_id", "confirm", "delay_seconds"}, "props=%s" % sorted(props))
    rec("描述已不再是「已废弃/恒失败」", bool(tool) and "已废弃" not in tool[0].get("description", ""),
        (tool[0].get("description", "")[:60] if tool else ""))
except Exception as ex:
    rec("tools/list 读取", False, repr(ex))

print('\n== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?ct=%d" % int(time.time())})

print('\n== ① 不带 confirm 关主窗口 → 可行动的拒绝 ==')
e1, t1, d1 = call("browser_close_try", {})
rec("失败但可行动(提到 confirm:true)", e1 and ("confirm" in t1), "%.2fs %s" % (d1, t1[:100]))
rec("不再是旧的 ⛔『刻意不实现』文案", "刻意不实现" not in t1, "")

print('\n== ② 传后台浏览器 id → 必须真的关掉(回读对照) ==')
before = browser_ids()
call("browser_create", {"url": "https://example.com/?bg=%d" % int(time.time()), "background": True})
time.sleep(1.0)
mid = browser_ids()
new_ids = [x for x in mid if x not in before]
rec("后台浏览器已创建(用于被测目标)", len(new_ids) == 1, "before=%s mid=%s" % (before, mid))
if new_ids:
    tid = new_ids[0]
    e2, t2, d2 = call("browser_close_try", {"browser_id": tid}, to=60)
    time.sleep(0.8)
    after = browser_ids()
    rec("close_try 回执成功", (not e2), "%.2fs %s" % (d2, t2[:80]))
    rec("回读: 该浏览器已从 browser_list 消失", tid not in after, "after=%s" % (after,))
else:
    rec("close_try 回执成功", False, "未能造出后台浏览器")
    rec("回读: 该浏览器已从 browser_list 消失", False, "")

print('\n== ③ 不存在的 id → 明确失败, 不得静默成功 ==')
e3, t3, d3 = call("browser_close_try", {"browser_id": 987654}, to=30)
rec("无效 id 明确失败", e3 and ("不可用" in t3 or "已关闭" in t3), "%.2fs %s" % (d3, t3[:80]))

print('\n== ④ 带 confirm:true → 必须真的退出程序 ==')
e4, t4, d4 = call("browser_close_try", {"confirm": True, "delay_seconds": 1}, to=30)
rec("close_try(confirm) 回执成功", (not e4) and ("关闭" in t4), "%.2fs %s" % (d4, t4[:90]))
t0 = time.time()
died = False
while time.time() - t0 < 15:
    e, t, _ = call("browser_status", {}, to=3)
    if e and ("EXC" in t):
        died = True
        break
    time.sleep(0.5)
rec("回读: 进程真的退出了(端口不再可用)", died, "耗时 %.1fs" % (time.time() - t0))

print('\n== ⑤ 重启后实例健康 ==')
if not loop.start_app():
    rec("重启实例", False, "启动失败")
else:
    e5, t5, d5 = call("browser_status", {}, to=30)
    rec("重启后 browser_status 可用", (not e5), "%.2fs" % d5)
    e6, t6, d6 = call("browser_execute_js", {"code": "1+1"}, to=30)
    rec("重启后 execute_js 可用", (not e6), "%.2fs %s" % (d6, t6[:40]))

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
