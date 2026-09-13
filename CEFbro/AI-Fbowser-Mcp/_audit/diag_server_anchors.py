# -*- coding: utf-8 -*-
"""查 Server 侧 4 个锚点的真实缩进/原文(不靠肉眼数空格)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
lines = open(p, 'rb').read().decode('utf-8').split('\n')
NEEDLES = ['置整数值 ("browser_frame_by_name"', '添加工具JSON ("browser_frame_by_name"',
           '添加工具JSON ("browser_uri_encode"', '添加工具JSON ("browser_uri_decode"']
for nd in NEEDLES:
    hits = [i for i, ln in enumerate(lines) if nd in ln]
    print('needle %r -> %d 行' % (nd[:46], len(hits)))
    for i in hits:
        ind = len(lines[i]) - len(lines[i].lstrip(' '))
        print('   行 %d 缩进=%d 原文前90: %r' % (i + 1, ind, lines[i][:90]))
