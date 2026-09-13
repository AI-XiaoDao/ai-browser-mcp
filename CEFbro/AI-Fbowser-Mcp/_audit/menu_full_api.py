# -*- coding: utf-8 -*-
"""抽取 类_FBrowser_菜单模式 全部 36 个方法的完整签名（含参数），用于设计"菜单快照"回读。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
n = 0
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
            inside = (m.group(1) == '类_FBrowser_菜单模式')
            continue
        if not inside:
            continue
        mm = re.match(r'方法\s+(\S+)(.*)', s)
        if not mm:
            continue
        n += 1
        name = mm.group(1)
        ret = ''
        r2 = re.search(r'类型\s*=\s*(\S+)', mm.group(2))
        if r2:
            ret = r2.group(1)
        params = []
        j = i + 1
        while j < len(lines):
            t = lines[j].strip()
            if t.startswith('参数'):
                pn = re.match(r'参数\s+(\S+)', t)
                pt = re.search(r'类型\s*=\s*(\S+)', t)
                opt = '@默认值' in t
                params.append('%s:%s%s' % (pn.group(1) if pn else '?',
                                           pt.group(1) if pt else '?',
                                           '(可选)' if opt else ''))
                j += 1
                continue
            if t == '' or t.startswith('//') or t.startswith('@') or t.startswith('#') or t.startswith('注释'):
                j += 1
                continue
            break
        print('%2d. %-22s -> %-22s (%s)' % (n, name, ret or '无返回', ', '.join(params) or '无参数'))
print('\n合计 %d 个方法' % n)
