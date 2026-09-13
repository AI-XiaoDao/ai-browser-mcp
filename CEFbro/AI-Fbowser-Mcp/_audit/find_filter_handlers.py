# -*- coding: utf-8 -*-
"""定位 MCP_BrowserEvents.wsv 里 3 处"手写过滤器"应用点各自的**所属方法**, 判断 CEF 是否会调用它们。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_BrowserEvents.wsv')
L = io.open(P, encoding='utf-8').read().split('\n')


def owner(idx):
    for i in range(idx, -1, -1):
        m = re.match(r'\s*方法\s+(\S+)(.*)', L[i])
        if m:
            return m.group(1), m.group(2).strip()[:90], i + 1
    return '?', '', 0


for ln in (113, 354, 392, 440):
    name, sig, at = owner(ln - 1)
    print('行 %-5d 所属方法: %s   (声明于 %d)' % (ln, name, at))
    print('   签名: %s' % sig)
    print('   该行: %s' % L[ln - 1].strip()[:130])
    print()

print('== 这些方法是否带 @虚拟方法 = 可覆盖 (即 CEF 回调) ==')
for target in (113, 354, 392):
    name, sig, at = owner(target - 1)
    print('   %-28s @虚拟方法=%s' % (name, '可覆盖' in sig))
