# -*- coding: utf-8 -*-
r"""修 `MCP_Server.wsv` 那一行多出来的一个 `)`。

对比已知良好行: `添加工具JSON ("", "", 多属性Schema文本 (属性项JSON (…) + "" + 属性项JSON (…), ""))`
  —— 必填参数串(`""`)在**多属性Schema文本 调用内部**, 末位是 `,)` 再加 `)` 收 添加工具JSON。
我那行写成 `…属性项JSON ("body", …)), "\"url\""))` —— 在最后一个 属性项JSON 后**提前关了** 多属性Schema文本, 于是多一个 `)`。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

BAD = '"请求体(UTF-8)")), "\\"url\\""))'
GOOD = '"请求体(UTF-8)"), "\\"url\\""))'
n = text.count(BAD)
print('待修行出现 %d 次' % n)
if n != 1:
    # 退一步: 可能转义形态不同, 打印附近原文
    i = text.find('请求体(UTF-8)')
    print('附近原文: %r' % text[i - 30:i + 60])
    sys.exit(1)
text = text.replace(BAD, GOOD, 1)
open(P, 'wb').write(text.encode('utf-8'))
print('已删掉多余的一个右括号')
