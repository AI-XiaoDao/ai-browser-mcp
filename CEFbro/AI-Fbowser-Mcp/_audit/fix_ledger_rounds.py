# -*- coding: utf-8 -*-
r"""修复台账里 round 字段为字符串('143+')的历史条目 → 改整数 150, 让 tool_ledger 的 max+1 不再崩溃。
"""
import io
import json
import os

base = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(base, '_tool_ledger.json')
with io.open(LEDGER, encoding='utf-8') as f:
    d = json.load(f)
fixed = 0
for k, v in d.items():
    r = v.get('round')
    if not isinstance(r, int):
        v['round'] = 150
        fixed += 1
        print('fixed round: %s (%r -> 150)' % (k, r))
with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print('done, fixed %d' % fixed)
