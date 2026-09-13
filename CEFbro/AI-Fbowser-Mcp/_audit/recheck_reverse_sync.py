# -*- coding: utf-8 -*-
"""复核: 代码里不再发 functionObjectId, 已有 objectId; 并统计本轮改动落点。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rev = io.open(os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv'), encoding='utf-8').read()

bad = rev.count('加入文本成员 ("functionObjectId"')
good = rev.count('加入文本成员 ("objectId"')
print('代码里仍发 functionObjectId: %d (应为 0)' % bad)
print('代码里发 objectId         : %d (应为 1)' % good)

sync = rev.count('返回 (执行V8CDP命令 (命令ID')
print('\n逆向分派内走同步出口的调用点: %d 处' % sync)

async_left = rev.count('执行逆向CDP命令 (命令ID')
print('逆向分派内仍走异步入口的调用点: %d 处' % async_left)
if async_left:
    for i, l in enumerate(rev.split('\n'), 1):
        if '执行逆向CDP命令 (命令ID' in l:
            print('   行 %-5d %s' % (i, l.strip()[:120]))
