# -*- coding: utf-8 -*-
"""打印其余"发起导航"处的判据(看是否也有"只看终态"的竞态)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

REGIONS = [
    ('MCP_Server_Core.wsv', 192, 34, '后退/前进/重新载入'),
    ('MCP_Server_Core.wsv', 5236, 26, '自动导航(autoNav)'),
    ('MCP_Server.wsv', 3972, 26, 'MCP_Server 内 载入地址(navUrl)'),
    ('MCP_BrowserEvents.wsv', 1276, 22, '重定向处理'),
]
for fn, start, n, tag in REGIONS:
    L = io.open(os.path.join(SRC, fn), encoding='utf-8').read().split('\n')
    print('===== %s : %s (行 %d 起) =====' % (fn, tag, start))
    for i in range(start - 1, min(start - 1 + n, len(L))):
        print('%5d| %s' % (i + 1, L[i][:140]))
    print()
