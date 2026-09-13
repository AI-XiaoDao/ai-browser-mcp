# -*- coding: utf-8 -*-
"""读出两个工具在台账里的完整备注(状态输出会截断)。"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, '_audit', '_tool_ledger.json')
d = json.load(io.open(P, encoding='utf-8'))
print("顶层类型: %s ; 键: %s" % (type(d).__name__,
                                list(d.keys())[:10] if isinstance(d, dict) else 'N/A'))

want = ('browser_reverse_return_value', 'browser_reverse_set_variable')


def walk(o, path=''):
    if isinstance(o, dict):
        name = o.get('name') or o.get('tool')
        if name in want:
            print("\n--- %s ---" % name)
            for k in ('verdict', 'status', 'kind', 'note', 'detail', 'message', 'error'):
                if k in o:
                    print("   %-8s %s" % (k, str(o[k])[:500]))
        for k, v in o.items():
            walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + '[%d]' % i)


walk(d)
