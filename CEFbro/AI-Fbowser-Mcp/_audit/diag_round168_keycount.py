# -*- coding: utf-8 -*-
r"""第 168 轮补充: 按键派发计数诊断(是否重复派发) + 修正后的判定。
① 装 keydown/keyup 计数监听 → ② type=keydown → ③ 读计数 → ④ type=keyup → ⑤ 读计数 → ⑥ 活体。
"""
import os
import sys
import time

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


JS = ("window.__kd=0;window.__ku=0;"
      "document.addEventListener('keydown',function(e){window.__kd++});"
      "document.addEventListener('keyup',function(e){window.__ku++})")
print('装监听:', text_of(call('browser_execute_js', {'code': JS, 'max_ms': 5000}))[:60])

t0 = time.time()
print('keydown ->', text_of(call('browser_key_event', {'key_code': 65, 'type': 'keydown'}))[:80],
      '%.2fs' % (time.time() - t0))
print('计数:', text_of(call('browser_execute_js',
                          {'code': 'window.__kd+"|"+window.__ku', 'max_ms': 5000}))[:80])

t0 = time.time()
print('keyup ->', text_of(call('browser_key_event', {'key_code': 65, 'type': 'keyup'}))[:80],
      '%.2fs' % (time.time() - t0))
print('计数:', text_of(call('browser_execute_js',
                          {'code': 'window.__kd+"|"+window.__ku', 'max_ms': 5000}))[:80])

t0 = time.time()
live = text_of(call('browser_execute_js', {'code': '1', 'max_ms': 4000}))
print('活体 execute_js %.2fs -> %s' % (time.time() - t0, live[:60]))
print('== %s ==' % ('PASS(通道未毒化)' if '"message":"1"' in live else 'FAIL'))
