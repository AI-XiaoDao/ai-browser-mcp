# -*- coding: utf-8 -*-
r"""查 MCP_Server 补丁里到底哪一行把类弄坏了: 逐行**引号奇偶** + 与备份的逐行差异。

思路: 编译器只报级联错误、不指向本文件 —— 这类"类整体消失"通常来自
  · 多/少一个引号(字符串跨行, 后续行被吞)
  · 多/少一个花括号(结构断裂)
  · 在类外插入了成员
先做最便宜的: 引号奇偶(剥掉 `\"` 后数裸引号), 只报奇数行; 再打印插入块的完整原文。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCHED = os.path.join(ROOT, '_audit', '_patched_MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '启动开关通道-写入前', 'MCP_Server.wsv')

for label, p in (('补丁后', PATCHED), ('备份(补丁前)', BAK)):
    ls = open(p, 'rb').read().decode('utf-8').split('\n')
    odd = []
    for i, ln in enumerate(ls, 1):
        s = ln.strip()
        if s.startswith(('@', '#', '//')):
            continue
        raw = ln.replace('\\"', '')
        if raw.count('"') % 2 != 0:
            odd.append((i, ln.strip()[:120]))
    print('== %s: 引号奇数行 %d 条 ==' % (label, len(odd)))
    for i, s in odd[:6]:
        print('   %d: %s' % (i, s))

# 花括号: 逐行深度, 报首次"深度为 0 之后又出现成员声明"的位置(即在类外声明成员)
ls = open(PATCHED, 'rb').read().decode('utf-8').split('\n')
depth = 0
cls_start = None
for i, ln in enumerate(ls, 1):
    s = ln.strip()
    if s.startswith('类 MCP命令服务器'):
        cls_start = i
    if s.startswith(('@', '#', '//')):
        continue
    body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
    d = body.count('{') - body.count('}')
    prev = depth
    depth += d
    if cls_start and depth == 0 and prev > 0:
        print('\n== 类 MCP命令服务器 (起 %s) 在**第 %d 行**闭合 ==' % (cls_start, i))
        print('   第 %d 行: %s' % (i, ln.strip()[:100]))
        for k in range(i, min(i + 8, len(ls))):
            print('      %5d | %s' % (k + 1, ls[k].strip()[:100]))
        break

print('\n== 插入块 1 (类变量区) ==')
for i in range(387, 400):
    print('   %5d | %s' % (i + 1, ls[i][:160]))
print('\n== 插入块 2 (加载MCP配置 内) ==')
for i in range(630, 665):
    print('   %5d | %s' % (i + 1, ls[i][:150]))
