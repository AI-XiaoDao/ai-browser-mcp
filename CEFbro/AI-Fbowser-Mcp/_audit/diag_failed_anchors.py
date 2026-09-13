# -*- coding: utf-8 -*-
"""查清 7 个未命中锚点的真实空白/文本(不再靠肉眼数空格)。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

NEEDLES = {
    'MCP_Server.wsv': [
        '目标模型.添加菜单 (条目命令ID, 条目标签)',
        '目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本)',
    ],
    'MCP_Server_Core.wsv': [
        '行是修改类(',
        '菜单最近施加条数 = 0',
        'note\\":\\"规格已暂存',
        'verify_mismatch',
        'note\\":\\"apply_count=右键次数',
    ],
}

for fn, needles in NEEDLES.items():
    p = os.path.join(SRC, fn)
    lines = open(p, 'rb').read().decode('utf-8').split('\n')
    print('=== %s ===' % fn)
    for nd in needles:
        hits = [i for i, ln in enumerate(lines) if nd in ln]
        print('  needle %r -> %d 行: %s' % (nd[:46], len(hits), [h + 1 for h in hits]))
        for i in hits[:3]:
            print('     %d: %r' % (i + 1, lines[i][:150]))
