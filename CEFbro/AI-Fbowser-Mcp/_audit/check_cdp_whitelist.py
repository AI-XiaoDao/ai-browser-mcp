# -*- coding: utf-8 -*-
"""核对 MCP_Server.wsv 里 browser_cdp 是否已进两张表(应同步等待 / 取同步等待毫秒)。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
lines = io.open(p, encoding='utf-8').read().split('\n')

print('== 含 "browser_cdp" 的行 ==')
for i, l in enumerate(lines, 1):
    if re.search(r'"browser_cdp"', l):
        print('  行 %-6d %s' % (i, l.strip()[:170]))

# 确认两张表各自都含 browser_cdp
t = '\n'.join(lines)
need = ['browser_cdp_call" || 规范名 == "browser_cdp"']
print('\n两张表都含 browser_cdp: %d 处 (应为 2)' % len(re.findall(re.escape(need[0]), t)))
