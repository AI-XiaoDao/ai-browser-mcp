# -*- coding: utf-8 -*-
"""重取 .vprj 模块表(上一版正则把多行块也吞了): 按 `name = X` 行抓, 只保留非空短名。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = open(os.path.join(ROOT, 'AI-Fbowser-Mcp.vprj'), 'rb').read()
t = None
for enc in ('utf-8', 'gbk', 'utf-16'):
    try:
        t = raw.decode(enc)
        break
    except Exception:
        pass
if t is None:
    print('!! 解码失败')
    sys.exit(1)

names = re.findall(r'^\s*name\s*=\s*(.+?)\s*$', t, re.M)
mods = [n for n in names if n and len(n) < 40]
print('候选模块名 %d 个:' % len(mods))
for m in mods:
    print('   %r' % m)
print()
for key in ('视窗基本类', '仰望', 'yyJSON', 'FBrowser', 'MFC界面基本类'):
    hit = [m for m in mods if key in m]
    print('含 %-14s : %s' % (key, hit if hit else '**无**'))
