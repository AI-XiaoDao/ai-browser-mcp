# -*- coding: utf-8 -*-
r"""第 168 轮: browser_key_event CDP 优先修复受控复测(≤10 秒)。
① 页面装 keydown 监听 → ② browser_key_event 派发 A(65, click) → ③ 回读页面捕获到的按键
→ ④ execute_js 活体(通道未被毒化, 无需重启)。
"""
import json
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM


def call(name, args, timeout=20):
    return CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                         'params': {'name': name, 'arguments': args}}, timeout)


def text_of(r):
    return ''.join((c.get('text') or '') for c in
                   ((r.get('result') or {}).get('content') or []))

JS_LISTENER = ("window.__k=[];document.addEventListener('keydown',"
               "function(e){window.__k.push(e.key+'/'+e.keyCode)})")

r = call('browser_execute_js', {'code': JS_LISTENER, 'max_ms': 5000})
print('装监听:', text_of(r)[:60])

t0 = time.time()
r2 = call('browser_key_event', {'key_code': 65, 'type': 'click'})
el = time.time() - t0
print('key_event el=%.2fs -> %s' % (el, text_of(r2)[:120]))

r3 = call('browser_execute_js', {'code': 'JSON.stringify(window.__k)', 'max_ms': 5000})
print('页面捕获:', text_of(r3)[:100])

t1 = time.time()
r4 = call('browser_execute_js', {'code': '1', 'max_ms': 4000})
print('活体 execute_js el=%.2fs -> %s' % (time.time() - t1, text_of(r4)[:60]))

ok = ('A/65' in text_of(r3) or 'a/65' in text_of(r3)) and el < 10 and '"message":"1"' in text_of(r4)
print('== %s ==' % ('PASS(页面真实收到按键 A/65 且通道未毒化)' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
