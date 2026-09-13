# -*- coding: utf-8 -*-
r"""实测: `browser_inject {persist:true, type:"js"}` 的持久注入到底生效不生效?

背景: 源码里注释说它由 `渲染_即将创建V8环境` 注入 —— 而该事件在主进程**不派发**(只写注释不接线);
实际接线是 `浏览器_载入开始` → `应用持久V8到框架 (框架)` → `框架.执行JS代码 (code)`。
后者在"载入开始"时执行的是**即将被替换的旧文档**上下文, 故"是否真的在新页面里生效"必须实测。

判据: 设置哨兵 → 重载/导航 → 在新页面读哨兵。

用法: py -3 _audit\probe_persist_inject.py
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
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?pj=%d" % int(time.time())})

print('\n[1] 提交持久 JS 注入(哨兵 window.__mcpPersist)')
e, t, d = call("browser_inject", {"type": "js", "persist": True,
                                  "code": "window.__mcpPersist='P1'", "inject_id": "probe139"})
print('    inject -> isError=%s %.2fs %s' % (e, d, t[:160]))

print('\n[2] 普通重载后读哨兵')
call("browser_reload", {"ignore_cache": True})
time.sleep(0.5)
e, t, d = call("browser_execute_js", {"code": "String(window.__mcpPersist)"})
print('    reload 后 -> isError=%s %s' % (e, t[:120]))

print('\n[3] 导航到新地址后读哨兵')
call("browser_navigate", {"url": "https://example.com/?pj2=%d" % int(time.time())})
time.sleep(0.5)
e, t, d = call("browser_execute_js", {"code": "String(window.__mcpPersist)"})
print('    navigate 后 -> isError=%s %s' % (e, t[:120]))

print('\n[4] 对照: 同一实例里用 CDP 预注入(browser_reverse_preload)做同型哨兵')
e, t, d = call("browser_reverse_preload", {"action": "add", "code": "window.__cdpPreload='C1'"})
print('    preload add -> isError=%s %.2fs %s' % (e, d, t[:140]))
call("browser_navigate", {"url": "https://example.com/?pj3=%d" % int(time.time())})
time.sleep(0.5)
e, t, d = call("browser_execute_js", {"code": "String(window.__cdpPreload)"})
print('    navigate 后读 CDP 哨兵 -> isError=%s %s' % (e, t[:120]))

print('\n[5] handler 模式: 是否被当成普通 JS 执行(而不是原生桥)')
e, t, d = call("browser_inject", {"type": "handler", "persist": True,
                                  "code": "window.__mcpHandlerRan='H1'", "inject_id": "probe139h"})
print('    inject handler -> isError=%s %.2fs %s' % (e, d, t[:160]))
call("browser_reload", {"ignore_cache": True})
time.sleep(0.5)
e, t, d = call("browser_execute_js", {"code": "String(window.__mcpHandlerRan)"})
print('    reload 后读 handler 哨兵 -> isError=%s %s' % (e, t[:120]))
