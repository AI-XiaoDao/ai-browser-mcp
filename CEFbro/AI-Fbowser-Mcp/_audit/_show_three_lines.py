# -*- coding: utf-8 -*-
r"""查看三行现状(修 HINT 位置错误前先看清原文)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')
for i, l in enumerate(t):
    if '添加工具JSON ("browser_debugger_last_paused"' in l or \
       '添加工具JSON ("browser_reverse_scan_crypto"' in l or \
       '添加工具JSON ("browser_reverse_detect_obfuscator"' in l:
        print('LINE %d' % (i + 1))
        print(l.strip()[:520])
        print()
