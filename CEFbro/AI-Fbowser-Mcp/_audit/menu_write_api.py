# -*- coding: utf-8 -*-
"""抽取"菜单写类"方法签名（扩展 browser_context_menu 规格类型所需）。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
WANT = ['删除菜单', '置菜单标签', '置可见状态', '置禁止状态', '选中状态', '设置快捷键',
        '移除快捷键', '存在快捷键', '取数量', '清空菜单', '取菜单标签', '置颜色', '置字体',
        '选中状态_索引', '置颜色_索引', '置字体_索引', '取菜单类型', '取子菜单']

seen = set()
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
        key = (m.group(1), fn, i)
        if key in seen:
            continue
        seen.add(key)
        print('%-34s %s:%d' % (m.group(1), fn, i + 1))
        print('    %s' % s[:150])
        j = i + 1
        while j < len(lines):
            t = lines[j].strip()
            if t.startswith('参数'):
                print('    %s' % t[:130])
                j += 1
                continue
            if t == '' or t.startswith('//') or t.startswith('@'):
                j += 1
                continue
            break
        print()
