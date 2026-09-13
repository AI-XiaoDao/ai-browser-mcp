# -*- coding: utf-8 -*-
r"""定位 C5 锚点: 在 MCP_Server_Core.wsv 里找出 verify_mismatch 附近的**真实片段**。
用法: py -3 _audit\_probe_c5.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
txt = io.open(os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv'), encoding='utf-8', newline='').read()

cands = [
    r'+ "\",\"verify_mismatch\":\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\",\"apply_failed\":\""',
    r'"\",\"verify_mismatch\":\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\","',
    r'\"verify_mismatch\"',
    r'verify_mismatch',
]
for c in cands:
    print('%-3s %s' % ('OK' if c in txt else 'NO', c[:90]))

i = txt.find('verify_mismatch')
print('\n上下文 repr(前后各 260 字符):')
print(repr(txt[max(0, i - 260):i + 260]))
