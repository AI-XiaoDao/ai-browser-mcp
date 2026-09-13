# -*- coding: utf-8 -*-
"""① 确认项目里是否已有 JS交互 通道; ② 取出项目内既有回调类的写法(照抄形态, 不另造)。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

print("== 1) 项目里是否已有 JS交互 / cefQuery ==")
hit = 0
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith('.wsv') or '~vbak' in fn:
        continue
    for i, l in enumerate(io.open(os.path.join(SRC, fn), encoding='utf-8').read().split('\n'), 1):
        if 'JS交互' in l or 'cefQuery' in l or 'FBroHsQueryHandler' in l:
            hit += 1
            print('   %s:%d  %s' % (fn, i, l.strip()[:140]))
print('   命中 %d 处' % hit)

print("\n== 2) 项目内既有回调类的形态(取 MCP_Callbacks.wsv 前 2 个类) ==")
cb = os.path.join(SRC, 'MCP_Callbacks.wsv')
if os.path.exists(cb):
    lines = io.open(cb, encoding='utf-8').read().split('\n')
    shown = 0
    for i, l in enumerate(lines):
        if re.match(r'类\s+', l.strip()) and '基础类' in l:
            shown += 1
            print('--- 类声明 %s:%d ---' % (i + 1, i + 1))
            for j in range(i, min(i + 26, len(lines))):
                print('%5d| %s' % (j + 1, lines[j][:150]))
            print()
            if shown >= 2:
                break
else:
    print('   !! 找不到 %s' % cb)
