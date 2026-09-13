# -*- coding: utf-8 -*-
"""核对: browser_dom_get_html 在 MCP_Server.wsv 里出现的每一处属于哪张表/哪个用途。

我上一轮说它"不在白名单、只回回执", 但复核显示有 5 处提及 —— 必须查清, 否则报告里的
"原本不是同步的"这句就可能不准确。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')


def owner(idx):
    """往上找最近的方法声明"""
    for i in range(idx, -1, -1):
        m = re.match(r'\s*方法\s+(\S+)', L[i])
        if m:
            return m.group(1), i + 1
    return '?', 0


for name in ('browser_dom_get_html', 'browser_dom_set_html'):
    print('== %s ==' % name)
    for i, l in enumerate(L):
        if '规范名 == "%s"' % name in l or '方法名 == "%s"' % name in l:
            meth, ln = owner(i)
            print('   行 %-6d 所属方法 %-24s (声明于 %d)' % (i + 1, meth, ln))
            print('        %s' % l.strip()[:150])
    print()
