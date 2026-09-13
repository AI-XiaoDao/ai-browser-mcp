# -*- coding: utf-8 -*-
r"""假设检验: `Page.addScriptToEvaluateOnNewDocument` 在本机**需要先 `Page.enable`** 才会真正生效?

已知(实测): 直接注册 → CDP 回 success + identifier, 但导航后哨兵读不到(脚本没执行)。
本探针做**三臂对照**:
  A 臂: 只注册(基线, 复现"不执行")
  B 臂: 先 Page.enable 再注册
  C 臂: 先 Page.enable + 注册两次(不同代码)  —— 看是否与重复/时序有关
每臂都导航到带时间戳的新地址, 读双哨兵(window 变量 + document.title)。

用法: py -3 _audit\probe_preload_pageenable.py
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


def read_sentinels(tag):
    e, t, _ = call("browser_execute_js", {"code": "JSON.stringify([String(window.__plS),String(document.title)])",
                                          "max_ms": 15000})
    print('    %-26s -> %s' % (tag, t[:150]))
    return t


for arm, use_page_enable, double_add in (('A 只注册(基线)', False, False),
                                         ('B 先 Page.enable', True, False),
                                         ('C Page.enable + 注册两次', True, True)):
    print('\n===== %s =====' % arm)
    loop.kill_app()
    if not loop.start_app():
        print('!! 启动失败'); continue
    call("browser_navigate", {"url": "https://example.com/?pe=%d" % int(time.time())})
    if use_page_enable:
        e, t, d = call("browser_cdp_call", {"method": "Page.enable", "params": "{}"}, to=30)
        print('    Page.enable -> isError=%s %.2fs %s' % (e, d, t[:90]))
    e, t, d = call("browser_reverse_preload", {"code": "window.__plS='C1';document.title='PRELOADED';"}, to=60)
    print('    注册 -> isError=%s %.2fs %s' % (e, d, t[:90]))
    if double_add:
        e, t, d = call("browser_reverse_preload", {"code": "window.__plS2='C2';"}, to=60)
        print('    再注册 -> isError=%s %.2fs %s' % (e, d, t[:90]))
    call("browser_navigate", {"url": "https://example.com/?pe2=%d" % int(time.time())})
    time.sleep(0.8)
    read_sentinels('导航后 [哨兵, title]')
