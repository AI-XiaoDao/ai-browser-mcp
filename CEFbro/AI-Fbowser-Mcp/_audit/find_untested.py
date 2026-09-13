# -*- coding: utf-8 -*-
r"""找出台账里所有**未逐一真机测试**的工具(每轮测试一个的候选清单)。
分类口径:
  - manual:true / cls=OK_MANUAL  → 人工核对, 未真机实测
  - cls 含 GUARD / 守卫 → 只测到守卫, 实现未测
  - 其它非 pass cls → 列出
输出: 候选清单(按类分), 每个工具: 名称 + cls + 备注。
"""
import json
import os

base = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base, '_tool_ledger.json'), encoding='utf-8') as f:
    ledger = json.load(f)

manual = []
guard = []
other = []
for name, v in sorted(ledger.items()):
    cls = v.get('cls') or ''
    if v.get('manual'):
        manual.append((name, cls, (v.get('notes') or v.get('note') or '')[:80]))
    elif 'GUARD' in cls.upper() or '守卫' in cls:
        guard.append((name, cls, (v.get('notes') or v.get('note') or '')[:80]))
    elif v.get('status') != 'pass':
        other.append((name, cls, (v.get('status') or '')[:80]))
    else:
        # pass 但想看看有没有"参数非法通过"类的弱通过
        if any(k in cls for k in ('PARAM', 'NOTARGET', 'UNSUPPORTED', 'ILLEGAL')):
            other.append((name, cls, (v.get('notes') or '')[:80]))

print('台账总数:', len(ledger))
print('\n== 人工核对(未真机实测) %d ==' % len(manual))
for n, c, t in manual:
    print('  %-46s %s %s' % (n, c, t))
print('\n== 只测到守卫 %d ==' % len(guard))
for n, c, t in guard:
    print('  %-46s %s %s' % (n, c, t))
print('\n== 其它(弱通过/未通过) %d ==' % len(other))
for n, c, t in other:
    print('  %-46s %s %s' % (n, c, t))
print('\n候选总数(每轮测一个):', len(manual) + len(guard) + len(other))
