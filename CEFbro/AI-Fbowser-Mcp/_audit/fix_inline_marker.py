# -*- coding: utf-8 -*-
r"""修启动开关补丁的**唯一结构缺陷**: 标记注释被并到了上一行行尾。

现场(补丁后 MCP_Server.wsv 第 388 行):
    变量 是否自动关闭JS对话框 <... @输出名 = "IsAutoCloseJSDialog">    # ==== 启动期开关通道v1: ...
火山里 `#` 是**行首注释**, 放行尾不是注释 -> 该行成为非法记号 -> **整类编译不出来**,
而编译器只报别处的级联错("没有找到 MCP命令服务器"), 不指向本文件 —— 与上一轮"花括号失衡"同一类
"类整体消失"现象。本轮脚本自己的 A9 曾报 `块标记增量 = 2 (期望 1)`, 那正是这个信号的提示。

修法: 把行尾那段标记**拆成独立的一行 `#` 注释**, 其余部分逐字保留。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '启动开关通道-写入前', 'MCP_Server.wsv')

text = open(SRC, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')

MARK = '# ==== 启动期开关通道v1'
fixed = 0
for i, ln in enumerate(lines):
    if MARK in ln and not ln.lstrip().startswith('#'):
        head, _, tail = ln.partition(MARK)
        head = head.rstrip()
        indent = re.match(r'\s*', lines[i]).group(0)
        lines[i:i + 1] = [head, indent + tail]
        fixed += 1
        print('已拆分第 %d 行:' % (i + 1))
        print('   保留: %s' % head[:100])
        print('   独立: %s' % (indent + tail)[:100])
if fixed == 0:
    print('没有"行尾标记"需要拆分(可能已修)')

# 与备份核对: 被还原的那一行是否与补丁前逐字一致
if os.path.exists(BAK):
    bak = open(BAK, 'rb').read().decode('utf-8').split('\n')
    for i, ln in enumerate(lines):
        if '是否自动关闭JS对话框 <' in ln:
            same = (ln == bak[387] if len(bak) > 387 else None)
            print('\n第 %d 行与备份第 388 行逐字一致? %s' % (i + 1, same))
            if not same and len(bak) > 387:
                print('   现: %r' % ln[:120])
                print('   备: %r' % bak[387][:120])
            break
open(SRC, 'wb').write(nl.join(lines).encode('utf-8'))
print('\n已写回 src/MCP_Server.wsv (拆分 %d 处)' % fixed)

# 顺手核对 main.wsv 的补丁标记是否也有"行尾"问题
M = os.path.join(ROOT, 'src', 'main.wsv')
ml = open(M, 'rb').read().decode('utf-8').split('\n')
bad = [i + 1 for i, ln in enumerate(ml) if MARK in ln and not ln.lstrip().startswith('#')
       and not ln.lstrip().startswith('//')]
print('main.wsv 行尾标记问题: %s' % (bad if bad else '无'))
