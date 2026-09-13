# -*- coding: utf-8 -*-
"""从 _audit/_hygiene_r98.md 里抽出"(a) 应删"类操作备注的 file:line 清单, 供清理脚本使用。

只读解析; 不改报告。输出也写到 _audit/_hygiene_delete_list.json, 让清理脚本有据可依
(而不是我凭记忆挑行 —— 那样容易误删 (b) 类知识注释)。
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
doc = os.path.join(ROOT, '_audit', '_hygiene_r98.md')
text = io.open(doc, encoding='utf-8').read()

print('报告长度 %d 字符' % len(text))
# 找出所有 (a) 相关小节标题
for m in re.finditer(r'^#{2,4}.*$', text, re.M):
    h = m.group(0)
    if '(a)' in h or '应删' in h or '操作备注' in h:
        print('  小节: %s' % h.strip()[:110])

# 抽形如 `MCP_Server.wsv:9806` 的行内代码引用, 仅取 (a) 小节内
secs = list(re.finditer(r'^#{2,4}.*$', text, re.M))
items = []
for i, m in enumerate(secs):
    h = m.group(0)
    if not (('(a)' in h) or ('应删' in h)):
        continue
    end = secs[i + 1].start() if i + 1 < len(secs) else len(text)
    body = text[m.end():end]
    for r in re.finditer(r'`([A-Za-z0-9_]+\.wsv):(\d+)`', body):
        items.append({'file': r.group(1), 'line': int(r.group(2)),
                      'section': h.strip()[:80]})

print('\n从 (a) 小节抽到 %d 条 file:line' % len(items))
seen = set()
uniq = []
for it in items:
    k = (it['file'], it['line'])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(it)
print('去重后 %d 条' % len(uniq))
for it in uniq:
    print('   %s:%d' % (it['file'], it['line']))

out = os.path.join(ROOT, '_audit', '_hygiene_delete_list.json')
io.open(out, 'w', encoding='utf-8').write(json.dumps(uniq, ensure_ascii=False, indent=1))
print('\n已写出 %s' % out)
