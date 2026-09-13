# -*- coding: utf-8 -*-
"""枚举 MCP_Server_Reverse.wsv 里所有"带方法名"的执行逆向CDP命令调用点。

目的: 该入口发完命令**不等 CDP 响应**就回 _async 成功, 于是参数错也报 success。
需要把"内核会立即返回结果"的设置类命令改用同步入口, 但**不能**一刀切
(有些命令本身是长驻/流式语义)。本脚本先给清单, 便于逐个判断。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')

PAT = re.compile(r'执行逆向CDP命令 \(([^,]+),\s*"([^"]+)"')
# 判定: 这些方法是"设置/使能"类, 内核立即返回 -> 适合改同步
IMMEDIATE = re.compile(r'^[A-Za-z]+\.(enable|disable|set|add|remove|start|stop|'
                       r'override|clear|emulate|compile|collect|take|profile|'
                       r'instrument|blackbox|skip|pause)', re.I)
# 这些是长驻/流式语义, 保留异步
STREAMING = re.compile(r'^(Runtime\.evaluate|Runtime\.callFunctionOn|Runtime\.awaitPromise|'
                       r'Debugger\.setInstrumentation|DOMDebugger\.setInstrumentation)', re.I)

lines = io.open(SRC, encoding='utf-8').read().split('\n')
rows = []
for i, l in enumerate(lines, 1):
    for m in PAT.finditer(l):
        rows.append((i, m.group(2), m.group(1).strip()))

print('== 带方法名的调用点共 %d 处 ==' % len(rows))
print('%-6s %-44s %s' % ('行号', 'CDP 方法', '用途/上下文'))
print('-' * 100)
for i, meth, ctx in rows:
    tag = 'SET?'
    if IMMEDIATE.match(meth):
        tag = 'SET '
    if STREAMING.match(meth):
        tag = 'STRM'
    print('%-6d %-44s [%s] %s' % (i, meth, tag, ctx[:36]))

from collections import Counter
c = Counter(m for _, m, _ in rows)
dups = {k: v for k, v in c.items() if v > 1}
print('\n重复调用的方法: %s' % (dups or '无'))
