# -*- coding: utf-8 -*-
r"""browser_evaluate 超时诊断: ① 复测(不同 max_ms/传法) ② 看 /health 的 async_tasks ③ 台账旧记录对照。
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM


def call(name, args, timeout=40):
    t0 = time.time()
    try:
        r = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                          'params': {'name': name, 'arguments': args}}, timeout)
        el = time.time() - t0
        res = r.get('result') or {}
        texts = [(c.get('text') or '') for c in (res.get('content') or [])]
        return ('OK' if not res.get('isError') else 'ERR'), el, texts
    except Exception as ex:
        return 'EXC', time.time() - t0, [str(ex)]


h = CM.http_get('/health', timeout=5)
print('health: async_tasks=%s tool_calls=%s db_async_results=%s' % (
    h.get('async_tasks'), h.get('tool_calls_total'), h.get('db_async_results')))

for args in [{'expression': '1', 'sync_wait': True, 'max_ms': 10000},
             {'code': '1', 'sync_wait': True, 'max_ms': 10000},
             {'expression': '1+1', 'sync_wait': False}]:
    st, el, texts = call('browser_evaluate', args)
    print('args=%s -> %s %.2fs' % (json.dumps(args, ensure_ascii=False), st, el))
    for t in texts:
        print('     | ' + t[:200])

# 台账旧记录
led = json.load(io.open(os.path.join(HERE, '_tool_ledger.json'), encoding='utf-8'))
e = led.get('browser_evaluate') or {}
print('台账旧记录: status=%s cls=%s elapsed=%s args=%s note=%s' % (
    e.get('status'), e.get('cls'), e.get('elapsed'), json.dumps(e.get('args'), ensure_ascii=False)[:120],
    (e.get('note') or '')[:120]))
