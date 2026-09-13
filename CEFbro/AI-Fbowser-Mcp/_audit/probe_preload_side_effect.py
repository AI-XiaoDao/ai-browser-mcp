# -*- coding: utf-8 -*-
r"""实测: 注册 `Page.addScriptToEvaluateOnNewDocument` 之后, `browser_execute_js` 是否还正常?
(上一轮探针里, 注册 preload 之后连续两次 execute_js 都返回"⏱ 操作超时(5s)" —— 必须查清是
 "预注入脚本没执行" 还是 "注册动作本身把 JS 通道搞慢了/搞坏了", 两者结论完全不同。)

步骤: ①基线 execute_js ②注册 preload ③不导航直接再 execute_js ④导航后 execute_js ⑤对照臂: 不注册 preload 的新实例走同样节奏。

用法: py -3 _audit\probe_preload_side_effect.py
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


def step(tag, name, args=None):
    e, t, d = call(name, args)
    print('    %-34s isError=%-5s %5.2fs %s' % (tag, e, d, t[:110].replace('\n', ' ')))
    return e, t, d


def run(with_preload):
    print('\n===== %s =====' % ('注册 preload 组' if with_preload else '对照臂(不注册 preload)'))
    loop.kill_app()
    if not loop.start_app():
        print('!! 启动失败'); return
    call("browser_navigate", {"url": "https://example.com/?ps=%d" % int(time.time())})
    step('①基线 execute_js', 'browser_execute_js', {"code": "1+1"})
    if with_preload:
        step('②注册 preload', 'browser_reverse_preload',
             {"code": "window.__plS='C1';document.title='PRELOADED';"})
        step('③注册后(不导航) execute_js', 'browser_execute_js', {"code": "2+2"})
    step('④导航', 'browser_navigate', {"url": "https://example.com/?ps2=%d" % int(time.time())})
    e, t, d = step('⑤导航后 execute_js', 'browser_execute_js', {"code": "3+3"})
    if with_preload:
        e, t, d = step('⑥哨兵读回(带 max_ms=15000)', 'browser_execute_js',
                       {"code": "String(window.__plS)", "max_ms": 15000})
        step('⑦title', 'browser_get_title')


run(False)
run(True)
