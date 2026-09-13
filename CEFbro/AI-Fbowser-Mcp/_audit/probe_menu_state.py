# -*- coding: utf-8 -*-
r"""诊断: arm 之后原生菜单到底是"还开着"还是"已关掉"? —— 用菜单事件族做判据。

判据来源: 项目既有菜单事件 `context_menu_opening` / `context_menu_run` / `context_menu_command` /
`context_menu_dismissed`(需先 browser_collect action=event_menu_enable)。
  · 若 opening 有 N 条、dismissed 也是 N 条 → 菜单**已关**(那 arm#2 失败另有原因);
  · 若 opening 有 N 条、dismissed 只有 N-1 条 → 最后那次菜单**仍开着**(模态阻塞说成立)。

用法: py -3 _audit\probe_menu_state.py
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


def call(n, a=None, to=60):
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


def count_events(kind):
    e, t, _ = call("browser_event", {"event_type": kind, "limit": 200}, to=30)
    if e:
        return -1, t[:80]
    try:
        o = json.loads(t)
    except Exception:
        return -1, t[:80]
    d = o.get("data") if isinstance(o.get("data"), dict) else o
    for key in ("count", "total", "events_count"):
        if isinstance(d.get(key), int):
            return d[key], ""
    evs = d.get("events") if isinstance(d.get("events"), list) else None
    if evs is not None:
        return len(evs), ""
    return -1, json.dumps(d, ensure_ascii=False)[:120]


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?ms=%d" % int(time.time())})
print('开菜单事件监控:', call("browser_collect", {"action": "event_menu_enable"}, to=30)[1][:80])

for i in (1, 2, 3):
    e, t, d = call("browser_menu_probe", {"action": "arm", "x": 240, "y": 170}, to=60)
    got = 'declared_count' in t
    time.sleep(1.0)
    op, _ = count_events("context_menu_opening")
    di, _ = count_events("context_menu_dismissed")
    ru, _ = count_events("context_menu_run")
    print('arm#%d 捕获=%-5s %.2fs | opening=%s run=%s dismissed=%s  %s'
          % (i, got, d, op, ru, di, 'SNAPSHOT' if got else t[:60]))
