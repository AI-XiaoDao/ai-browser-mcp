# -*- coding: utf-8 -*-
"""核对编解码计划的关键前提: 它依赖的类库模块是否**已在项目模块表**里(零新模块的前提)。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'AI-Fbowser-Mcp.vprj')
raw = open(p, 'rb').read()
for enc in ('utf-8', 'gbk', 'utf-16'):
    try:
        t = raw.decode(enc)
        break
    except Exception:
        t = None
if t is None:
    print('!! 无法解码 .vprj')
    sys.exit(1)

mods = re.findall(r'模块名称\s*=\s*"([^"]+)"', t)
if not mods:
    mods = re.findall(r'"([^"]*支持库[^"]*|[^"]*基本类[^"]*|[^"]*模块[^"]*)"', t)
print('模块数 = %d' % len(mods))
for m in mods:
    print('   %s' % m)
print()
for key in ('视窗基本类', '仰望', 'yyJSON', 'FBrowser'):
    hit = [m for m in mods if key in m]
    print('含 %-10s : %s' % (key, hit if hit else '**无**'))
