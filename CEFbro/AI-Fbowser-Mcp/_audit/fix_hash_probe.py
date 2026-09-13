# -*- coding: utf-8 -*-
r"""给台账探针补 `browser_hash` 的参数(否则每次都会被正确拒绝: 探针只给 action 不给 data)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, '_audit', 'mass_probe.py')
src = open(P, 'rb').read().decode('utf-8')

if '"browser_hash"' in src:
    print('已存在 browser_hash 覆盖, 跳过')
    sys.exit(0)
anchor = 'TOOL_ARG_OVERRIDES.update({'
if src.count(anchor) < 1:
    print('!! 找不到 TOOL_ARG_OVERRIDES.update({')
    sys.exit(1)
add = (anchor + '\n'
       '    # 哈希工具: 探针必须同时给 action 与 data, 否则会被"空串摘要无意义"守卫正确拒绝\n'
       '    "browser_hash": {"action": "md5", "data": "mcp_probe"},')
src = src.replace(anchor, add, 1)
open(P, 'wb').write(src.encode('utf-8'))
print('已加 browser_hash 探针参数')
