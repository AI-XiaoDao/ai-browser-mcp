# -*- coding: utf-8 -*-
"""核对删除的 8 段在备份里到底长什么样: 是否恰好从方法行到**配对的收尾大括号**, 有没有多删/少删。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAK = os.path.join(ROOT, '备份', '删除死方法-写入前', 'MCP_Server.wsv')
ls = open(BAK, 'rb').read().decode('utf-8').split('\n')

# 删除脚本打印的原行号范围(1-based)与行数
DEL = [
    ("发送CORS500响应", 9413, 11),
    ("规范化URL", 7945, 21),
    ("记录网络日志项", 7652, 16),
    ("解析匹配模式", 7083, 20),
    ("分派网络日志命令", 5225, 47),
    ("CDP获取脚本源", 3606, 44),
    ("尝试导航欢迎页", 163, 8),
    ("尝试恢复欢迎页导航", 124, 8),
]
for name, start, n in DEL:
    seg = ls[start - 1:start - 1 + n]
    before = ls[start - 2] if start >= 2 else ''
    after = ls[start - 1 + n] if start - 1 + n < len(ls) else ''
    print('=' * 92)
    print('%s  备份行 %d..%d (%d 行)' % (name, start, start + n - 1, n))
    print('   前一行: %r' % before[:70])
    print('   首行  : %r' % seg[0][:70])
    print('   末行  : %r' % seg[-1][:70])
    print('   后一行: %r' % after[:70])
    # block 内花括号是否配平
    b = sum(l.count('{') for l in seg if not l.lstrip().startswith('@'))
    e = sum(l.count('}') for l in seg if not l.lstrip().startswith('@'))
    print('   段内 { = %d, } = %d  %s' % (b, e, '配平 OK' if b == e else '★不配平'))
