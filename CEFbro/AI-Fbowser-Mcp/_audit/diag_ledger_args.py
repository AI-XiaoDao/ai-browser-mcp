# -*- coding: utf-8 -*-
r"""分诊: `browser_collect` / `browser_network` 的台账复测为何从 pass 变 fail —— 是产品缺陷还是探针没传参?
用法: py -3 _audit\diag_ledger_args.py
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, '_audit', '_tool_ledger.json')
PROBE = os.path.join(ROOT, '_audit', 'mass_probe.py')

d = json.load(io.open(LEDGER, encoding='utf-8'))
for name in ('browser_collect', 'browser_network', 'browser_event'):
    e = d.get(name) or {}
    print('== %s' % name)
    print('   cls=%s status=%s note=%s' % (e.get('cls'), e.get('status'), str(e.get('note'))[:150]))
    print('   args=%s' % json.dumps(e.get('args'), ensure_ascii=False))

t = io.open(PROBE, encoding='utf-8', newline='').read()
print('\n== mass_probe 里与这两个工具相关的片段 ==')
for m in re.finditer(r'^(?:def |TOOL_ARG_OVERRIDES|DYNAMIC_ARGS|LETHAL|MUTATING_SKIP).*$', t, re.M):
    ln = t[:m.start()].count('\n') + 1
    if any(k in m.group(0) for k in ('browser_collect', 'browser_network', 'browser_event')):
        print('   %d: %s' % (ln, m.group(0)[:160]))
for m in re.finditer(r'browser_(collect|network|event)', t):
    ln = t[:m.start()].count('\n') + 1
    line = t.split('\n')[ln - 1]
    if 'browser_collect' in line or 'browser_network' in line or 'browser_event' in line:
        print('   %d: %s' % (ln, line.strip()[:160]))
