# -*- coding: utf-8 -*-
"""抽取实现 browser_context_menu 所需的类库方法签名（逐字，含参数顺序与默认值）。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
WANT = ['添加菜单', '添加子菜单', '添加分隔栏', '添加Check菜单', '添加Radio菜单',
        '选中状态', '置可见状态', '置禁止状态', '设置快捷键', '清空菜单', '取数量',
        '置颜色', '置字体']

for fn in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, fn)
    if not os.path.isfile(p):
        continue
    lines = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
    for i, l in enumerate(lines):
        s = l.strip()
        m = re.match(r'方法\s+(\S+)', s)
        if not m or m.group(1) not in WANT:
            continue
        print('%-46s %s:%d' % (s[:46], fn, i + 1))
        print('      %s' % s)
        j = i + 1
        while j < len(lines):
            t = lines[j].strip()
            if t.startswith('参数'):
                print('      %s' % t)
                j += 1
                continue
            if t == '' or t.startswith('//') or t.startswith('@'):
                j += 1
                continue
            break
        print()
