# -*- coding: utf-8 -*-
"""① 打印 browser_event 报错文案的真实字节(锚点反复不中, 不再猜);
② 修掉两处过期数字(kernel 工具描述 13 项 / collect 描述 12 族);
③ 顺手核对 docs 里的过期数字与死链。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

print('== ① browser_event 报错文案原文 ==')
c = open(os.path.join(SRC, 'MCP_Server_Core.wsv'), 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(c, 1):
    if 'key_press' in ln or '下载_*' in ln or 'focus_*' in ln:
        print('行 %d:' % i)
        print('   %r' % ln.strip())

print('\n== ② 过期数字 ==')
s = open(os.path.join(SRC, 'MCP_Server.wsv'), 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(s, 1):
    if ('13项' in ln or '13 项' in ln or '12族' in ln or '12 族' in ln or '21项' in ln) and '添加工具JSON' in ln:
        k = ln.find('添加工具JSON')
        print('行 %d: %s' % (i, ln[k:k + 150]))

print('\n== ③ docs 过期数字/死链 ==')
D = os.path.join(ROOT, 'docs', 'index.html')
if os.path.exists(D):
    dl = open(D, 'rb').read().decode('utf-8', 'replace').split('\n')
    for i, ln in enumerate(dl, 1):
        if ('开启 10 项' in ln or '10 项' in ln or '使用技能书' in ln or '13项' in ln):
            print('行 %d: %s' % (i, ln.strip()[:200]))
    doc = os.path.join(ROOT, 'docs', '使用技能书.md')
    print('docs/使用技能书.md 存在? %s' % os.path.exists(doc))
else:
    print('docs/index.html 不存在')
