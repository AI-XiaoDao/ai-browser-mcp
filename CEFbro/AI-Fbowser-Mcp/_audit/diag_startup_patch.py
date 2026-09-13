# -*- coding: utf-8 -*-
r"""诊断: 启动开关补丁后 `类 MCP命令服务器` 为何编译不出来。

上一轮同类事故(删行少删一行导致花括号失衡)的教训: 先比花括号, 再看插入点上下文。
本脚本对比 `src/MCP_Server.wsv` 与 `备份/启动开关通道-写入前/MCP_Server.wsv`,
定位**首次深度异常**的位置, 并打印两处插入点前后各 6 行。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUR = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '启动开关通道-写入前', 'MCP_Server.wsv')


def scan(p, label):
    ls = open(p, 'rb').read().decode('utf-8').split('\n')
    depth = 0
    minv = 0
    first_neg = None
    for i, ln in enumerate(ls, 1):
        s = ln.lstrip()
        if s.startswith(('@', '//', '#')):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        d = body.count('{') - body.count('}')
        depth += d
        if depth < minv:
            minv = depth
        if depth < 0 and first_neg is None:
            first_neg = (i, ln.strip()[:80])
    print('%-34s 行=%-6d 末深度=%-4d 最小深度=%-4d 首次为负=%s'
          % (label, len(ls), depth, minv, first_neg))
    return ls


cur = scan(CUR, '当前 src/MCP_Server.wsv')
bak = scan(BAK, '备份(补丁前)')

print('\n== 插入点上下文(当前文件) ==')
for needle in ('启动开关_启用摄像头 <公开', '配置解析.取逻辑值 ("disable_gpu")', 'auto_dismiss_js_dialog'):
    idx = [i for i, ln in enumerate(cur) if needle in ln]
    print('锚点 %r -> %s' % (needle[:34], [i + 1 for i in idx]))
    for i in idx[:1]:
        for k in range(max(0, i - 6), min(len(cur), i + 8)):
            mark = '>>' if k == i else '  '
            print('   %s %5d | %s' % (mark, k + 1, cur[k][:110]))
        print()
