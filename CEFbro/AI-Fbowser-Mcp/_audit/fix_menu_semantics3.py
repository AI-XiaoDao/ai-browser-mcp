# -*- coding: utf-8 -*-
"""C11 补做: 上一版锚点漏了值尾部的 \\" 转义引号。这次整行替换(整行才好做引号奇偶校验)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
raw = open(p, 'rb').read()
text = raw.decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')

NEEDLE = 'MCP命令服务器.菜单回读不一致)'
OLD_FRAG = '不一致) + "\\",\\"last_apply_time\\":\\""'
NEW_FRAG = ('不一致) + "\\",\\"apply_failed\\":\\"" + MCP_响应构建.JSON转义文本 '
            '(MCP命令服务器.菜单施加失败) + "\\",\\"last_apply_time\\":\\""')

hits = [i for i, ln in enumerate(lines) if NEEDLE in ln and 'last_apply_time' in ln]
if len(hits) != 1:
    print('!! 定位到 %d 行(应 1)' % len(hits))
    sys.exit(1)
i = hits[0]
ln = lines[i]
if ln.count(OLD_FRAG) != 1:
    print('!! 行内片段命中 %d 次' % ln.count(OLD_FRAG))
    print('   %r' % ln[max(0, ln.find('不一致)') - 20):ln.find('不一致)') + 120])
    sys.exit(1)
new_ln = ln.replace(OLD_FRAG, NEW_FRAG, 1)
if new_ln.replace('\\"', '').count('"') % 2 != 0:
    print('!! 新整行引号奇数')
    sys.exit(1)
lines[i] = new_ln
open(p, 'wb').write(nl.join(lines).encode('utf-8'))
print('C11 完成: 第 %d 行已插入 apply_failed' % (i + 1))
k = new_ln.find('apply_failed')
print('   %s' % new_ln[max(0, k - 60):k + 150])
