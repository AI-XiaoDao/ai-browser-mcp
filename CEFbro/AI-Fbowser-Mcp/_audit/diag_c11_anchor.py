# -*- coding: utf-8 -*-
"""打印 Core get 回包里 verify_mismatch 附近的确切字节, 好写准 C11 的锚点。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
lines = open(p, 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(lines):
    if 'verify_mismatch' in ln:
        k = ln.find('verify_mismatch')
        print('行 %d, 偏移 %d' % (i + 1, k))
        print('  前文: %r' % ln[max(0, k - 130):k])
        print('  后文: %r' % ln[k:k + 200])
