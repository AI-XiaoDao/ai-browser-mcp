# -*- coding: utf-8 -*-
"""在类库源码里找菜单状态的 getter/setter 的**真实英文绑定**, 判定 是否禁止 到底读的是什么。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

P = r'E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\FBroLib.v'
raw = open(P, 'rb').read()
for enc in ('utf-8', 'gbk', 'utf-16'):
    try:
        txt = raw.decode(enc)
        print('编码 = %s, 行数 = %d' % (enc, txt.count('\n') + 1))
        break
    except Exception as e:
        print('  %s 失败: %s' % (enc, e))
else:
    sys.exit(1)

KEYS = ['是否禁止', '置禁止状态', '是否选中', '选中状态', '是否可见', '置可见状态',
        'IsEnabled', 'SetEnabled', 'IsChecked', 'SetChecked', 'IsVisible',
        'SetVisible', 'MenuModel']
lines = txt.split('\n')
hits = 0
for i, ln in enumerate(lines):
    for k in KEYS:
        if k in ln:
            hits += 1
            print('%6d: %s' % (i + 1, ln.strip()[:220]))
            break
print('总命中 %d 行' % hits)

print('\n== 菜单模型类定义位置 ==')
for i, ln in enumerate(lines):
    if re.search(r'类\s+\S*菜单\S*', ln):
        print('%6d: %s' % (i + 1, ln.strip()[:160]))
