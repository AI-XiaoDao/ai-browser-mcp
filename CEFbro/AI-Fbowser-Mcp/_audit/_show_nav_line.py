# -*- coding: utf-8 -*-
r"""显示 browser_navigate 的注册行原文(用于校准 schema 补丁)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for i, ln in enumerate(io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')):
    if '添加工具JSON ("browser_navigate"' in ln:
        print('LINE %d' % (i + 1))
        print(ln)
