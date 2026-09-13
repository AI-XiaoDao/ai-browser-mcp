# -*- coding: utf-8 -*-
r"""删除回退后遗留的常量 `HTTP请求体安全上限`(按行内容定位, 幂等)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONST = os.path.join(ROOT, 'src', 'MCP_Constants.wsv')
lines = io.open(CONST, encoding='utf-8').read().split('\n')
out = []
removed = 0
for ln in lines:
    # 该常量的两行注释(含"第126轮实测"/"故取 1,000,000 字节")与常量本体一起删
    if ('HTTP请求体安全上限' in ln) or ln.strip().startswith('// 第126轮实测: MCP **HTTP** 通道') \
       or ln.strip().startswith('// 故取 1,000,000 字节') or ln.strip().startswith('// 超出即在读正文前拒绝'):
        removed += 1
        continue
    out.append(ln)
res = '\n'.join(out)
assert 'HTTP请求体安全上限' not in res, '仍残留'
assert 'WS最大消息字节' in res, '误删了相邻常量'
io.open(CONST, 'w', encoding='utf-8', newline='\n').write(res)
print('MCP_Constants.wsv: 删除 %d 行(行数 %d -> %d)' % (removed, len(lines), len(out)))
