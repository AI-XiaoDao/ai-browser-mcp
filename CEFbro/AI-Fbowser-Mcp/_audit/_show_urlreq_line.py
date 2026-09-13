# -*- coding: utf-8 -*-
r"""打印 browser_create_url_request 的注册行原文(供校准补丁锚点)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for i, ln in enumerate(io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')):
    if '添加工具JSON ("browser_create_url_request"' in ln:
        print('LINE %d (len=%d)' % (i + 1, len(ln)))
        print(ln.strip())
