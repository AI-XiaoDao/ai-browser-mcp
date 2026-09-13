# -*- coding: utf-8 -*-
r"""列出所有"用户给的路径被安全守卫拒绝"时的**报错文案**, 判断是否可行动(是否说清允许的目录与改法)。

用法: py -3 _audit\_show_path_guard_msgs.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['MCP_Server.wsv', 'MCP_Server_Core.wsv', 'MCP_Server_Reverse.wsv',
         'MCP_Server_VIP.wsv', 'MCP_BrowserEvents.wsv', 'MCP_Server_Form.wsv',
         'MCP_Server_System.wsv', 'MCP_Kernel.wsv']
for fn in FILES:
    lines = io.open(os.path.join(ROOT, 'src', fn), encoding='utf-8').read().split('\n')
    for i, ln in enumerate(lines):
        if '验证安全路径 (' in ln and '方法 ' not in ln:
            # 往下找 6 行内的报错文案
            msg = ''
            for j in range(i, min(i + 7, len(lines))):
                if '命令失败' in lines[j] or '错误_' in lines[j]:
                    msg = lines[j].strip()
                    break
            print('%s:%d' % (fn, i + 1))
            print('   守卫: %s' % ln.strip()[:110])
            print('   文案: %s' % (msg[:200] if msg else '(后续 6 行内没有报错文案 —— 可能是静默跳过)'))
