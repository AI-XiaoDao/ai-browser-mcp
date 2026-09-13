# -*- coding: utf-8 -*-
"""定位"类 MCP命令服务器 消失"的根因: 删死方法后花括号是否失衡?

做法: 对比当前文件与备份(删除死方法-写入前)的
  ① 行数  ② 非 `@` 行的 { } 计数  ③ 类/方法能否仍被 vlib 识别  ④ 逐行前缀和首次跌到 0 的位置
`@` 开头是内嵌 C++, 花括号不属于火山语法, 必须排除。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import vlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUR = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '删除死方法-写入前', 'MCP_Server.wsv')


def stats(p, label):
    lines = open(p, 'rb').read().decode('utf-8').split('\n')
    o = c = 0
    depth = 0
    first_zero = None
    for i, ln in enumerate(lines, 1):
        s = ln.lstrip()
        if s.startswith('@'):
            continue
        # 去掉字符串与行注释再数(粗粒度足够定位结构问题)
        body = re.sub(r'"[^"]*"', '""', ln)
        body = body.split('//')[0]
        o += body.count('{')
        c += body.count('}')
        depth += body.count('{') - body.count('}')
        if depth <= 0 and first_zero is None and i > 100:
            first_zero = (i, ln.strip()[:70])
    print('%-28s 行数=%-6d "{"=%-6d "}"=%-6d 差=%-5d 首次归零@%s'
          % (label, len(lines), o, c, o - c, first_zero))
    return lines


cur = stats(CUR, '当前 src/MCP_Server.wsv')
bak = stats(BAK, '备份(删除死方法前)')

print('\nvlib 能否识别关键符号:')
for name, fn in (('类 MCP命令服务器', 'find_classes'),
                 ('方法 应用菜单规格', 'find_methods')):
    f = getattr(vlib, fn)
    try:
        got = [r[1] for r in f('MCP_Server.wsv')]
        hit = name.split()[-1] in got
        print('   %-18s -> %s (共 %d 个)' % (name, '有' if hit else '**没有**', len(got)))
    except Exception as e:
        print('   %-18s -> 异常 %r' % (name, e))

print('\n备份里同两项:')
vlib.SRC = os.path.join(ROOT, '备份', '删除死方法-写入前')
for name, fn in (('类 MCP命令服务器', 'find_classes'),
                 ('方法 应用菜单规格', 'find_methods')):
    f = getattr(vlib, fn)
    try:
        got = [r[1] for r in f('MCP_Server.wsv')]
        hit = name.split()[-1] in got
        print('   %-18s -> %s (共 %d 个)' % (name, '有' if hit else '**没有**', len(got)))
    except Exception as e:
        print('   %-18s -> 异常 %r' % (name, e))
