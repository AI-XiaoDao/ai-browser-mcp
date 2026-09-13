# -*- coding: utf-8 -*-
r"""只读: 取三个新工具实现所需的类库细节
① `JSON解析` 常量取值; ② `类_FBrowser_值` 的可用方法(能否按路径取值);
③ `FBrowser_Parser_` 三个方法的逐字签名; ④ `类_FBrowser_字节集` 判空方法名。
用法: py -3 _audit\_facts_json.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

LIB = r'C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器'


def load(fn):
    return io.open(os.path.join(LIB, fn), encoding='utf-8', errors='replace').read().split('\n')


print('① JSON解析 常量:')
for i, l in enumerate(load('FBroConst.wsv')):
    if l.strip().startswith('类 JSON解析'):
        for j in range(i, min(i + 16, 99999)):
            print('   %d %s' % (j + 1, load('FBroConst.wsv')[j].strip()[:120]))
            if load('FBroConst.wsv')[j].strip() == '}' and j > i:
                break
        break

print('\n② 类_FBrowser_值 的方法:')
t = load('FBroValue.wsv')
for i, l in enumerate(t):
    if l.strip().startswith('类 类_FBrowser_值') or l.strip().startswith('类 FBrowser_值'):
        for j in range(i, min(i + 120, len(t))):
            s = t[j].strip()
            if s.startswith('方法') or s.startswith('类 '):
                print('   %d %s' % (j + 1, s[:120]))
            if s == '}' and j > i + 5:
                break
        break

print('\n③ Parser 方法签名:')
t = load('FBroLib.wsv')
for i, l in enumerate(t):
    m = re.match(r'方法 (FBrowser_Parser_\S+)', l.strip())
    if m:
        print('   --- %s @%d' % (m.group(1), i + 1))
        for j in range(i, min(i + 5, len(t))):
            s = t[j].strip()
            if s.startswith('参数') or s.startswith('方法') or s.startswith('@'):
                print('       %s' % s[:150])

print('\n④ 类_FBrowser_字节集 方法:')
t = load('FBroDataType.wsv')
for i, l in enumerate(t):
    if l.strip().startswith('类 FBrowser_字节集') or l.strip().startswith('类 类_FBrowser_字节集'):
        for j in range(i, min(i + 40, len(t))):
            s = t[j].strip()
            if s.startswith('方法') or s.startswith('类 '):
                print('   %d %s' % (j + 1, s[:120]))
            if s == '}' and j > i + 3:
                break
        break

print('\n⑤ 通过序号取浏览器 签名:')
t = load('FBroLib.wsv')
for i, l in enumerate(t):
    if '通过序号取浏览器' in l and l.strip().startswith('方法'):
        for j in range(i, min(i + 4, len(t))):
            print('   %d %s' % (j + 1, t[j].strip()[:150]))
