# -*- coding: utf-8 -*-
"""交叉核对"幽灵注册 16 项": 它们真的没有实现, 还是扫描器只认精确分支名而漏掉了前缀路由?

判据: 台账里这 16 个工具的真机实测状态 ——
  · pass            -> 有实现(扫描器误报), 不能删注册项
  · fail + 未知命令  -> 真幽灵, 需补实现或删注册
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LED = os.path.join(ROOT, '_audit', '_tool_ledger.json')

GHOSTS = [
    'browser_aliases', 'browser_batch', 'browser_create_tab', 'browser_debugger_pause',
    'browser_fingerprint_languages', 'browser_fingerprint_webgl_vendor',
    'browser_font_randomize', 'browser_reverse_cookie_cdp', 'browser_reverse_css_coverage',
    'browser_reverse_detect_traps', 'browser_reverse_emulate_focus',
    'browser_reverse_input_cdp', 'browser_reverse_layer_tree',
    'browser_reverse_network_conditions', 'browser_reverse_trace',
    'browser_task_runner_post',
]

d = json.load(open(LED, encoding='utf-8'))
print('台账条目 %d' % len(d))
print('%-38s %-8s %-10s %s' % ('工具', '状态', '性质', '备注'))
print('-' * 118)
ok = bad = miss = 0
for g in GHOSTS:
    r = d.get(g)
    if not r:
        miss += 1
        print('%-38s %-8s %-10s %s' % (g, '(未记录)', '', ''))
        continue
    st = r.get('status', '')
    if st == 'pass':
        ok += 1
    else:
        bad += 1
    print('%-38s %-8s %-10s %s' % (g, st, r.get('kind', ''), (r.get('note') or '')[:60]))
print('-' * 118)
print('pass=%d  fail=%d  未记录=%d' % (ok, bad, miss))
