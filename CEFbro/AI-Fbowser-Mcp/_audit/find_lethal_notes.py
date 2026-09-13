# -*- coding: utf-8 -*-
"""找出 6 个致命工具在报告里已有的**人工实测**记录, 以便补记进台账。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = io.open(os.path.join(ROOT, 'MCP工具可用性检测报告.md'), encoding='utf-8').read()

for nm in ['browser_close', 'browser_close_try', 'browser_shutdown',
           'browser_set_s5_proxy', 'browser_set_preference', 'browser_reverse_patch']:
    idx = [m.start() for m in re.finditer(re.escape(nm), T)]
    print('== %s : %d 处 ==' % (nm, len(idx)))
    for i in idx[:2]:
        seg = T[max(0, i - 320):i + 340].replace('\n', ' | ')
        print('   ...' + seg)
    print()
