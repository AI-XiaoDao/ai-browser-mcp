# -*- coding: utf-8 -*-
"""修掉编译报错的两处类库名大小写: `字节集到Base64文本` -> `字节集到BASE64文本`。

依据: 技能书 `资料\类库\视窗基本类\w_bin_p.wsv:582`
  `方法 字节集到BASE64文本 <公开 静态 类型 = 文本型 注释 = "返回本字节集数据所对应的BASE64编码格式文本内容">`
(相邻的 `BASE64文本到字节集` 在 :590, 同样是大写 BASE64)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

BAD = '字节集到Base64文本'
GOOD = '字节集到BASE64文本'
n = text.count(BAD)
print('错误写法出现 %d 处' % n)
if n == 0:
    print('无需修改(可能已修)')
    sys.exit(0)
lines = text.split('\n')
for i, ln in enumerate(lines, 1):
    if BAD in ln:
        print('   行 %d: %s' % (i, ln.strip()[:110]))
text = text.replace(BAD, GOOD)
open(P, 'wb').write(text.encode('utf-8'))
print('已替换为 %s' % GOOD)

# 顺带核对同类大小写风险: 这些名字在本项目里出现过吗
for name in ('BASE64文本到字节集', '字节集到BASE64文本', '字节集到十六进制文本', '十六进制文本到字节集'):
    c = text.count(name)
    print('   %-22s 在 Core 里出现 %d 次' % (name, c))
