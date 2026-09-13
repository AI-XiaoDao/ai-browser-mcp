# -*- coding: utf-8 -*-
"""修复 add_context_menu.py 的锚点失误。

事故: 上一脚本用的是**行前缀**锚点 `添加工具JSON ("browser_intercept", `,
替换后把 browser_intercept 那行的"前缀"吃掉、把其余部分(描述+schema)留在了下一行成为孤立片段
-> 编译报 `<MCP_Server.wsv>, 9999: 错误: 括号缺失或不匹配`。
修法: 给该孤立片段补回前缀。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '修复intercept注册行-写入前')

FRAG = '"资源拦截/篡改(手写ResponseFilter过滤器, 不依赖VIP'
PREFIX = '添加工具JSON ("browser_intercept", '

lines = io.open(SRC, encoding='utf-8').read().split('\n')
hits = [i for i, l in enumerate(lines) if l.startswith(FRAG)]
print('孤立片段命中 %d 行(应为1): %s' % (len(hits), [i + 1 for i in hits]))
if len(hits) != 1:
    print('!! 中止')
    sys.exit(1)
i = hits[0]
print('改前: %s' % lines[i][:80])
lines[i] = PREFIX + lines[i]
print('改后: %s' % lines[i][:80])

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server.wsv'))
open(SRC, 'wb').write('\n'.join(lines).encode('utf-8'))
print('已修复; 备份 -> %s' % BAK)

# 自检: browser_intercept 与 browser_context_menu 各应恰好 1 处注册
t = io.open(SRC, encoding='utf-8').read()
print('browser_intercept 注册行: %d (应为1)' % t.count('添加工具JSON ("browser_intercept"'))
print('browser_context_menu 注册行: %d (应为1)' % t.count('添加工具JSON ("browser_context_menu"'))
