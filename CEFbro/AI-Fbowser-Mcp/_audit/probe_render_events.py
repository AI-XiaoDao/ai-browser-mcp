# -*- coding: utf-8 -*-
r"""判定: `渲染_*`(app_render_*/app_v8_*) 事件到底会不会被派发到本项目。

背景: 项目里有两处**互相矛盾**的文案 ——
  · `MCP_Server_Core.wsv:3862/3867`(工具回包): "经真机验证, 这些事件不会被派发到本项目的事件覆盖上, 因此 app_render_* 不会产生任何记录";
  · `main.wsv:846-855`: "补 `获取默认事件` 后事件就能到"。
至少一处陈旧。本脚本开渲染族监控 → 触发导航 → 查 app_render_*/app_v8_* 是否有记录(带对照臂: 同时开一个**已知会触发**的族)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def ev(event_type, limit=40):
    e, t = call("browser_event", {"event_type": event_type, "limit": limit})
    n = 0
    try:
        d = json.loads(t)
        rows = d.get("data") if isinstance(d, dict) else d
        n = len(rows) if isinstance(rows, list) else 0
    except Exception:
        n = -1
    return e, n, t[:220]


print('== 0. 开启渲染族 / 应用族 / 生命周期族监控 ==')
for act in ("event_render_enable", "event_renderws_enable", "event_app_enable", "event_lifecycle_enable"):
    e, t = call("browser_collect", {"action": act})
    print('   %-24s isError=%s %s' % (act, e, t[:90]))

print('\n== 1. 触发一次导航(会产生 load/生命周期事件) ==')
e, t = call("browser_navigate", {"url": "https://example.com/?renderevt=%d" % int(time.time()),
                                 "wait_for_load": True})
print('   navigate isError=%s %s' % (e, t[:100]))
time.sleep(3.0)
call("browser_reload", {"wait_for_load": True})
time.sleep(3.0)

print('\n== 2. 各族事件条数(对照臂: load/生命周期应 >0) ==')
for et in ("app_render_*", "app_v8_*", "app_startup_*", "app_render_load_end",
           "load_end", "browser_created", "title_changed"):
    e, n, raw = ev(et)
    print('   %-22s isError=%-5s 条数=%s | %s' % (et, e, n, raw.replace('\n', ' ')[:150]))

print('\n== 3. 时间线里是否出现过任何 app_render_/app_v8_ 记录 ==')
e, t = call("browser_event", {"limit": 200})
hit = []
for k in ("app_render", "app_v8", "app_render_ws"):
    if k in t:
        hit.append(k)
print('   时间线命中: %s' % (hit or '（无）'))
print('   判读: %s' % ('渲染族确实有派发' if hit else '渲染族在本次实测中**未产生任何记录**(与 MCP_Server_Core.wsv:3862 的口径一致)'))
