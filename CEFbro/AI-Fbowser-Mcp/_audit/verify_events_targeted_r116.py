# -*- coding: utf-8 -*-
"""定向验证: URL请求事件族(3 个) + DevTools 分离事件 —— 用**能真正触发它们的路径**。

背景: 上一轮把 12 个事件全部接线后, 只有 `devtools_attached` 有记录。原因是其余 11 个**不是靠普通导航触发的**:
  · `urlreq_*` 只在**本服务自己创建 URL 请求**时回调 —— 即 `browser_create_url_request`(Core 里走
    `FBrowser_创建URL请求 (请求, , URL请求回调, …)`)。
  · `devtools_detached` 需要 CDP 客户端**分离**(上一轮只 attach 没 detach)。
  · `offscreen_*` 需要离屏渲染(本项目窗口内嵌, 文档已注明不触发);
    `urlreq_auth` 需要客户端证书质询; `drag_enter` 需要 OS 级拖拽; `devtools_popup` 需要真的弹出 DevTools 窗口;
    `media_access_change` 需要**真的拿到**媒体设备(需启动期开关, 尚未做)。
  本脚本只验证**可触发**的那几个, 其余如实记录为"本环境不可达", 不谎报。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=90):
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


def count_ev(name):
    e, t = call("browser_event", {"event_type": name}, 40)
    return len(t.split('"event":"%s"' % name)) - 1, t


print('== A. URL 请求事件族(用 browser_create_url_request 真正创建请求) ==')
e, t = call("browser_collect", {"action": "event_urlreq_enable"})
print('   新的 event_urlreq_enable 分支: isError=%s %s' % (e, t[:140]))
e, t = call("browser_create_url_request", {"url": "https://example.com/?urlreq=1", "method": "GET"}, 60)
print('   create_url_request: isError=%s %s' % (e, t[:200]))
time.sleep(3.0)
for nm in ("urlreq_start", "urlreq_download", "urlreq_auth"):
    n, t = count_ev(nm)
    print('   [%s] %-18s %d 条' % ('有记录' if n else '无记录', nm, n))
    if not n:
        print('        %s' % t[:150])

print('\n== B. DevTools 分离事件 ==')
for tool in ("browser_debugger_disable", "browser_debugger_stop"):
    e, t = call(tool, {}, 40)
    print('   %s: isError=%s %s' % (tool, e, t[:110]))
time.sleep(1.5)
for nm in ("devtools_attached", "devtools_detached"):
    n, t = count_ev(nm)
    print('   [%s] %-18s %d 条' % ('有记录' if n else '无记录', nm, n))

print('\n== C. 拖拽(试 CDP 派发拖拽事件, 看是否触发 drag_enter) ==')
call("browser_cdp_call", {"method": "Input.setInterceptDrags", "params": {"enabled": True}}, 30)
e, t = call("browser_cdp_call", {"method": "Input.dispatchDragEvent",
                                 "params": {"type": "dragEnter", "x": 200, "y": 200,
                                            "data": {"items": [], "dragOperationsMask": 1}}}, 30)
print('   dispatchDragEvent: isError=%s %s' % (e, t[:160]))
time.sleep(1.5)
n, t = count_ev("drag_enter")
print('   [%s] drag_enter %d 条' % ('有记录' if n else '无记录', n))

print('\n== D. 本环境不可达的项(如实记录, 不谎报) ==')
for nm, why in (("offscreen_get_root_rect", "离屏渲染族: 本项目窗口内嵌渲染, 文档已注明不触发"),
                ("offscreen_get_view_rect", "同上"),
                ("offscreen_popup_size", "同上"),
                ("devtools_popup", "需要真的弹出 DevTools 窗口(F12/菜单检查), 本环境无法用 CDP 触发原生菜单项"),
                ("media_access_change", "需要真的取得摄像头/麦克风(需启动期 --enable-media-stream, 尚未实现)"),
                ("urlreq_auth", "需要客户端证书质询的站点"),
                ("ipc_from_renderer_ext", "需要宿主主动向渲染进程发消息, 本项目从不发")):
    n, _ = count_ev(nm)
    print('   %-24s %d 条 | %s' % (nm, n, why))

call("browser_collect", {"action": "event_urlreq_disable"})
