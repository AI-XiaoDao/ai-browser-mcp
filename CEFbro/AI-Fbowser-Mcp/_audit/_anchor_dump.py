# -*- coding: utf-8 -*-
r"""打印补丁 B/C 缺失锚点的**原文 repr**(避免手抄转义出错)。用法: py -3 _audit\_anchor_dump.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')


def dump(fn, needles):
    t = io.open(os.path.join(SRC, fn), encoding='utf-8', newline='').read().split('\n')
    print('=== %s ===' % fn)
    for nd in needles:
        hit = False
        for i, l in enumerate(t):
            if nd in l:
                print('  [%s] @%d' % (nd, i + 1))
                print('    %r' % l)
                hit = True
                break
        if not hit:
            print('  [%s] 未找到' % nd)


dump('MCP_Server.wsv', ['browser_context_menu', 'browser_menu_alias', 'cm警告 = ', 'verify_mismatch'])
dump('MCP_Server_Core.wsv', ['cm警告 = ', 'verify_mismatch'])
