# -*- coding: utf-8 -*-
"""把 browser_uri_decode 的工具描述改成实测结论(整行替换, 缩进自取)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')
idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_uri_decode"' in ln]
if len(idx) != 1:
    print('!! 定位 %d 行' % len(idx))
    sys.exit(1)
i = idx[0]
ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
new = (ind + '添加工具JSON ("browser_uri_decode", "URI解码(百分号还原)。'
       '实测: 类库解码器在本机**无法还原 ASCII 特殊字符**的转义(%20/%26/%3D 会原样返回, 只还原非 ASCII), '
       '所以当结果仍残留 %HH 时, 本工具会**自动**改用页面内 decodeURIComponent 补齐 —— 一次调用即可拿到完整结果; '
       '回包 data.via 如实说明实际走的路径(lib:… 或 js:decodeURIComponent)。'
       'to_utf8 与 keep_escaped 直接透传给类库(keep_escaped:true 即类库原始行为); 注意 + 不会被当作空格", '
       '多属性Schema文本 (属性项JSON ("data", "text", "要解码的文本") + "," + '
       '属性项JSON ("to_utf8", "boolean", "true(默认)=把解码结果按 UTF-8 解释") + "," + '
       '属性项JSON ("keep_escaped", "boolean", "true(默认)=类库原始行为 / false=类库完全不还原(实测更差, 仅供对照)"), "\\"data\\""))')
if new.replace('\\"', '').count('"') % 2 != 0:
    print('!! 新行引号奇数')
    sys.exit(1)
lines[i] = new
open(P, 'wb').write(nl.join(lines).encode('utf-8'))
print('已改第 %d 行, 新长度 %d' % (i + 1, len(new)))
k = new.find('via')
print('   ...%s...' % new[max(0, k - 60):k + 80])
