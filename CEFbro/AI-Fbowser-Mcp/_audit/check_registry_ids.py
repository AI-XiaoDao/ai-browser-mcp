# -*- coding: utf-8 -*-
"""查命令注册表: 条目数 / ID 范围 / 是否有重复 ID / 下一个可用 ID（新工具要用它）。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), 'rb').read().decode('utf-8')
pairs = re.findall(r'置整数值 \("([a-z0-9_]+)", (\d+)\)', t)
ids = [int(v) for _, v in pairs]
print('注册表条目 %d, ID 范围 %d..%d' % (len(ids), min(ids), max(ids)))
dup = sorted({i for i in ids if ids.count(i) > 1})
print('重复 ID: %s' % (dup[:12] if dup else '无'))
print('最大 6 个 ID: %s' % sorted(ids)[-6:])
print('下一个可用 ID = %d' % (max(ids) + 1))
for name in ('browser_frame_by_name', 'browser_uri_encode', 'browser_uri_decode'):
    hit = [v for k, v in pairs if k == name]
    print('  %-26s ID=%s' % (name, hit))
