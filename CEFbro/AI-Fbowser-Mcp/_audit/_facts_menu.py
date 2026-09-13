# -*- coding: utf-8 -*-
r"""一次性取几项实现前必须确认的事实(只读):
① MCP_BrowserEvents.wsv 的行尾约定; ② 命令注册表 id 占用情况(挑一个空闲号);
③ FBrowser_文本数组 的可用方法名; ④ 路由器如何决定 browser_* 名进哪个分派类。
用法: py -3 _audit\_facts_menu.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
LIB = r'C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器'

b = io.open(os.path.join(SRC, 'MCP_BrowserEvents.wsv'), 'rb').read()
print('① MCP_BrowserEvents.wsv: CRCRLF=%d CRLF=%d LF=%d' % (b.count(b'\r\r\n'), b.count(b'\r\n'), b.count(b'\n')))

t = io.open(os.path.join(SRC, 'MCP_Server.wsv'), encoding='utf-8', newline='').read()
ids = [int(m.group(1)) for m in re.finditer(r'命令注册表\.置整数值 \("[a-zA-Z0-9_.]+", (\d+)\)', t)]
print('② 注册表 id 共 %d 个, 最大 %d' % (len(ids), max(ids)))
print('   1300 以上已用:', sorted(i for i in ids if i >= 1300))
free = [i for i in range(max(ids) + 1, max(ids) + 8)]
print('   可直接用的空闲号:', free[:4])

s = io.open(os.path.join(LIB, 'FBroDataType.wsv'), encoding='utf-8', errors='replace').read().split('\n')
for i, l in enumerate(s):
    if l.strip().startswith('类 FBrowser_文本数组'):
        print('③ FBrowser_文本数组 @%d:' % (i + 1))
        for j in range(i, min(i + 46, len(s))):
            ls = s[j].strip()
            if ls.startswith('方法') or ls.startswith('类') or ls.startswith('变量'):
                print('   ', j + 1, ls[:120])
            if ls == '}' and j > i + 3:
                break
        break

print('④ 路由器中 browser_ 前缀的分派顺序(取 MCP_Server.wsv 里 分类分派 调用链):')
for m in re.finditer(r'^\s*(?:如果|否则).{0,40}?(MCP_[A-Za-z_\u4e00-\u9fff]+)\.(分类分派_[A-Za-z_\u4e00-\u9fff]+)', t, re.M):
    ln = t[:m.start()].count('\n') + 1
    print('   %d: %s.%s' % (ln, m.group(1), m.group(2)))
