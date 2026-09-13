# -*- coding: utf-8 -*-
"""抽取"元素文本读写"类库方法签名 + 看现有 fill 族工具的实现与注册形态(以便沿用而另造)。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
WANT = ['取元素内文本', '置元素内文本', '取元素外文本', '置元素外文本', '置元素外代码',
        '取元素属性', '置元素属性', '取元素内代码']

print("== 1) 类库签名 ==")
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
        print('%s:%d  %s' % (fn, i + 1, s[:140]))
        j = i + 1
        while j < len(lines):
            t = lines[j].strip()
            if t.startswith('参数'):
                print('      %s' % t[:120])
                j += 1
                continue
            if t == '' or t.startswith('//') or t.startswith('@'):
                j += 1
                continue
            break

print("\n== 2) 现有 fill 族工具注册行(取前 8 条) ==")
srv = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')
n = 0
for i, l in enumerate(srv, 1):
    if '添加工具JSON ("browser_fill_' in l:
        n += 1
        if n <= 8:
            print('%5d| %s' % (i, l.strip()[:190]))
print('   fill 族工具共 %d 个' % n)

print("\n== 3) fill 族分派分支所在 ==")
for fn in ('MCP_Server_Core.wsv', 'MCP_Server_Form.wsv'):
    p = os.path.join(ROOT, 'src', fn)
    if not os.path.exists(p):
        continue
    for i, l in enumerate(io.open(p, encoding='utf-8').read().split('\n'), 1):
        if 'browser_fill_' in l and ('方法名 ==' in l or '规范名 ==' in l):
            print('%s:%d  %s' % (fn, i, l.strip()[:150]))
