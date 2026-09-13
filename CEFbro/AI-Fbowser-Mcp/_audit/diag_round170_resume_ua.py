# -*- coding: utf-8 -*-
r"""第 170 轮诊断:
① browser_debugger_resume 直接复测(看修复为何没拦住);
② browser_fingerprint_ua 后立即连探(定位其引发的重启根因)。
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM


def call(name, args, timeout=20):
    t0 = time.time()
    try:
        r = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                          'params': {'name': name, 'arguments': args}}, timeout)
        return r, time.time() - t0, None
    except Exception as ex:
        return None, time.time() - t0, str(ex)


def text_of(r):
    return ''.join((c.get('text') or '') for c in
                   ((r.get('result') or {}).get('content') or []))

# ① resume 直接复测
r, el, err = call('browser_debugger_resume', {})
print('[resume] el=%.2f err=%s' % (el, err))
print('  ', text_of(r)[:160] if r else r)

# ② fingerprint_ua 后立即连探
r, el, err = call('browser_fingerprint_ua', {})
print('[fingerprint_ua] el=%.2f -> %s' % (el, (text_of(r)[:100] if r else err)))
for i in range(6):
    r2, el2, err2 = call('browser_execute_js', {'code': '1', 'max_ms': 3000}, 8)
    r3, el3, err3 = call('browser_status', {}, 8)
    h, eh, e3 = call('__health__', {}, 8)
    print('  探%d: js el=%.2f %s | status el=%.2f %s | err=%s' % (
        i + 1, el2, (text_of(r2)[:50] if r2 else 'EXC'), el3,
        (text_of(r3)[:80] if r3 else 'EXC'), err2 or err3))
    time.sleep(1.5)
