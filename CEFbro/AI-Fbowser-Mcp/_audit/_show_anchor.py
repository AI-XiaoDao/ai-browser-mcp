# -*- coding: utf-8 -*-
r"""打印 browser_context_menu 注册行的精确缩进(用于校准补丁锚点)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')
for i, ln in enumerate(t):
    if 'browser_context_menu",' in ln:
        print(i + 1, repr(ln[:80]))
    if '命令注册表.置整数值 ("browser_context_menu"' in ln:
        print(i + 1, repr(ln[:80]))
