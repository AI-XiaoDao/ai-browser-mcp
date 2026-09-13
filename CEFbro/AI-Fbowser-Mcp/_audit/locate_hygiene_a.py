# -*- coding: utf-8 -*-
"""按**内容**定位 29 条待清理备注的当前行号, 并打印上下文(前1行/本行/后1行)。

为什么不用报告里的行号: 报告快照取自第98轮, 之后源码已变动
(MCP_Server.wsv 加过 5 行、MCP_Server_Core.wsv 加过约 49 行又删过 38 行),
行号已漂移 —— 按行号删会删错行。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
doc = io.open(os.path.join(ROOT, '_audit', '_hygiene_r98.md'), encoding='utf-8').read()

secs = list(re.finditer(r'^#{2,4}.*$', doc, re.M))
body = ''
for i, m in enumerate(secs):
    if '(a)' in m.group(0):
        end = secs[i + 1].start() if i + 1 < len(secs) else len(doc)
        body = doc[m.end():end]
        break

# 表格行: | `file:line` | `原文片段` | ...
rows = []
for line in body.split('\n'):
    m = re.match(r'\|\s*`([A-Za-z0-9_]+\.wsv):(\d+)`\s*\|\s*`(.+?)`\s*\|', line)
    if m:
        rows.append({'file': m.group(1), 'old_line': int(m.group(2)),
                     'snip': m.group(3).strip()})
print('解析出待清理条目 %d 条\n' % len(rows))

cache = {}
for r in rows:
    p = os.path.join(SRC, r['file'])
    if p not in cache:
        cache[p] = io.open(p, encoding='utf-8').read().split('\n')
    lines = cache[p]
    # 用片段的前 40 字符做唯一匹配(报告里的片段可能被截断或含省略号)
    key = r['snip'][:40].replace('…', '').replace('...', '')
    hits = [i for i, l in enumerate(lines) if key and key in l]
    r['now'] = [i + 1 for i in hits]
    print('=== %s  报告行 %d  实now=%s' % (r['file'], r['old_line'], r['now']))
    print('    片段: %s' % r['snip'][:110])
    if len(hits) == 1:
        i = hits[0]
        for k in (i - 1, i, i + 1):
            if 0 <= k < len(lines):
                mark = '>>' if k == i else '  '
                print('   %s %5d| %s' % (mark, k + 1, lines[k].rstrip()[:150]))
    elif len(hits) > 1:
        print('    !! 多处命中, 需人工判定')
    else:
        print('    !! 未命中(片段可能已被改动或被截断)')
    print()
