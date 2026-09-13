# -*- coding: utf-8 -*-
r"""第 167 轮诊断: 打印争议工具的真实回包全文 + step_into 前后 paused 状态。
"""
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


for name, args in [('browser_console_eval', {'expression': '1+1'}),
                   ('browser_kernel_ipc_queue', {'action': 'queue'}),
                   ('browser_kernel_ipc_clear', {'action': 'clear'}),
                   ('browser_dom_select', {'selector': 'h1'}),
                   ('browser_status', {}),
                   ('browser_debugger_last_paused', {}),
                   ('browser_debugger_step_into', {}),
                   ('browser_debugger_last_paused', {}),
                   ('browser_execute_js', {'code': '1', 'max_ms': 4000})]:
    st, el, texts = call(name, args)
    print('%-38s %s %.2fs' % (name, st, el))
    for t in texts:
        print('     | ' + t[:220])
    print()
