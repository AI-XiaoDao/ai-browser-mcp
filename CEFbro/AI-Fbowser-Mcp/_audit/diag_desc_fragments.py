# -*- coding: utf-8 -*-
"""先看一眼 browser_context_menu 工具描述里所有"修改类/别名/默认项"措辞的确切原文, 再决定替换锚点。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
lines = open(p, 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(lines):
    if '添加工具JSON ("browser_context_menu"' in ln:
        print('行 %d 长度 %d' % (i + 1, len(ln)))
        for kw in ('修改类', '别名', '默认菜单项', 'mark(', '26500'):
            k = 0
            while True:
                k = ln.find(kw, k)
                if k == -1:
                    break
                print('  [%s @%d] ...%s...' % (kw, k, ln[max(0, k - 45):k + 70]))
                k += 1
        break
