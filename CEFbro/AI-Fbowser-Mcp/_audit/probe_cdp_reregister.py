# -*- coding: utf-8 -*-
r"""关键实验: 截图把 CDP 命令通道弄坏之后, **注销 + 重新注册 CDP 观察者**能不能救回来?

已知实测: 任意截图后, 所有 CDP 命令(原始 Runtime.evaluate / execute_js / debugger_enable / dom_query)
响应**永不到达**, 工具只能靠原生回退在 10~35s 后勉强返回 —— 属"截图静默打死 CDP"这一类高影响缺陷。
项目里已有 `注销CDP观察者 ()` / `确保CDP观察者已注册 ()`(main.wsv 退出路径、VIP 的 devtools 观察者开关都在用)。

本探针做 A/B:
  A: 截图 → 直接 execute_js(预期 30s 级)  → 注销+重挂 → execute_js(看是否回到 0.03s)
  B: 对照: 不截图, 只注销+重挂 → execute_js(确认重挂本身无副作用)

用法: py -3 _audit\probe_cdp_reregister.py
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


def show(tag, n, a=None, to=90):
    e, t, d = call(n, a, to)
    print('    %-34s isError=%-5s %6.2fs %s' % (tag, e, d, t[:100].replace('\n', ' ')))
    return e, t, d


def reregister():
    """用既有 VIP 工具做"注销 + 重挂"(它内部正是这两个方法, 见 MCP_Server_VIP.wsv 的 devtools 观察者分支)。"""
    show('  ① ensure_devtools_observer enable=false', 'browser_vip_enable_devtools_observer', {"enable": False})
    show('  ② ensure_devtools_observer enable=true', 'browser_vip_enable_devtools_observer', {"enable": True})


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?rg=%d" % int(time.time())})

print('== A: 截图 → CDP 坏 → 重挂观察者 ==')
show('基线 execute_js', 'browser_execute_js', {"code": "1+1"})
show('截图', 'browser_screenshot', {"format": "png", "width": 600, "height": 400})
show('截图后 execute_js(应很慢)', 'browser_execute_js', {"code": "2+2"})
print('  -- 重挂观察者 --')
reregister()
show('重挂后 execute_js(希望 0.03s)', 'browser_execute_js', {"code": "3+3"})
show('重挂后原始 CDP evaluate', 'browser_cdp_call',
     {"method": "Runtime.evaluate", "params": "{\"expression\":\"9+9\",\"returnByValue\":true}"})

print('\n== B: 对照臂(不截图, 只重挂) ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?rg2=%d" % int(time.time())})
show('基线 execute_js', 'browser_execute_js', {"code": "1+1"})
reregister()
show('重挂后 execute_js', 'browser_execute_js', {"code": "4+4"})
