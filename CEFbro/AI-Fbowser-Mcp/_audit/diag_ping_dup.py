# -*- coding: utf-8 -*-
"""ping 重复分支定死: 找出 9787 / 11014 / System:111 各自属于哪个方法, 以及谁调用谁。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')


def enclosing(fn, line):
    ls = open(os.path.join(SRC, fn), 'rb').read().decode('utf-8').split('\n')
    for i in range(line - 1, -1, -1):
        if re.match(r'\s*方法\s+\S+', ls[i]):
            return i + 1, ls[i].strip()
    return None, None


for fn, ln in (('MCP_Server.wsv', 9787), ('MCP_Server.wsv', 11014),
               ('MCP_Server_System.wsv', 111)):
    i, sig = enclosing(fn, ln)
    print('%-22s:%-6d 属于方法(第 %s 行): %s' % (fn, ln, i, (sig or '')[:110]))

# 谁调用了这两个分派方法?
ls = open(os.path.join(SRC, 'MCP_Server.wsv'), 'rb').read().decode('utf-8').split('\n')
for name in ('分类分派_系统操作', '分派系统工具'):
    hits = [(i + 1, ls[i].strip()[:90]) for i, l in enumerate(ls) if name in l]
    print('\n引用 %s: %d 处' % (name, len(hits)))
    for h in hits[:6]:
        print('   %d: %s' % h)
