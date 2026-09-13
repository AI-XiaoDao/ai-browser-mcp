# -*- coding: utf-8 -*-
r"""第 170 轮: 复现 sweep 里 browser_debugger_resume 的 CDP 错误序列。
① debugger_pause(制造暂停) → ② 立即 resume → ③ 再 resume(第二次) → ④ last_paused 状态。
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM


def call(name, args, timeout=25):
    t0 = time.time()
    r = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                      'params': {'name': name, 'arguments': args}}, timeout)
    return r, time.time() - t0


def text_of(r):
    return ''.join((c.get('text') or '') for c in
                   ((r.get('result') or {}).get('content') or []))


r, el = call('browser_debugger_pause', {})
print('pause el=%.2f -> %s' % (el, text_of(r)[:140]))

r, el = call('browser_debugger_resume', {})
print('resume#1 el=%.2f -> %s' % (el, text_of(r)[:160]))

r, el = call('browser_debugger_resume', {})
print('resume#2 el=%.2f -> %s' % (el, text_of(r)[:160]))

r, el = call('browser_debugger_last_paused', {})
print('last_paused -> %s' % text_of(r)[:160])

r, el = call('browser_execute_js', {'code': '1', 'max_ms': 5000})
print('execute_js el=%.2f -> %s' % (el, text_of(r)[:60]))
