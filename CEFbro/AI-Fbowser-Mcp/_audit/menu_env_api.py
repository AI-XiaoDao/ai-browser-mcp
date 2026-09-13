# -*- coding: utf-8 -*-
"""抽取 类_FBrowser_菜单环境 的全部方法签名（实现"右键上下文"消费所需）。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
TARGET = '类_FBrowser_菜单环境'

for fn in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, fn)
    if not os.path.isfile(p):
        continue
    lines = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
    inside = False
    for i, l in enumerate(lines):
        s = l.strip()
        m = re.match(r'类\s+(\S+)', s)
        if m:
            inside = (m.group(1) == TARGET)
            if inside:
                print('== %s 定义于 %s:%d ==' % (TARGET, fn, i + 1))
            continue
        if not inside:
            continue
        mm = re.match(r'方法\s+(\S+)(.*)', s)
        if mm:
            print('\n%s' % s[:150])
            j = i + 1
            while j < len(lines):
                t = lines[j].strip()
                if t.startswith('参数'):
                    print('   %s' % t[:130])
                    j += 1
                    continue
                if t == '' or t.startswith('//') or t.startswith('@'):
                    j += 1
                    continue
                break
