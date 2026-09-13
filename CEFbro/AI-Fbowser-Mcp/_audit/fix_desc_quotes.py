# -*- coding: utf-8 -*-
"""自纠: 上一步在工具描述里写了 ASCII 双引号 "...", 而 .wsv 的字符串字面量里裸 ASCII 引号会**打断字符串**
(历史上已踩过 4 次, 报错是"发现字符处于无效位置")。改成全角「」。

同时扫一遍本轮改动过的行, 找"描述字面量内部的裸 ASCII 引号"。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
raw = open(p, 'rb').read()
text = raw.decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')

BAD = '实测它返回的是"\u662f\u5426\u53ef\u7528"'      # 实测它返回的是"是否可用"
GOOD = '实测它返回的是\u300c\u662f\u5426\u53ef\u7528\u300d'  # 全角引号
hits = [i for i, ln in enumerate(lines) if BAD in ln]
if len(hits) != 1:
    print('!! 定位 %d 行' % len(hits))
else:
    i = hits[0]
    lines[i] = lines[i].replace(BAD, GOOD, 1)
    open(p, 'wb').write(nl.join(lines).encode('utf-8'))
    print('已换全角引号(第 %d 行)' % (i + 1))

# 复查: browser_context_menu 描述字面量里不应再有"本该是文本引号"的裸 ASCII 引号
lines = open(p, 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(lines):
    if '添加工具JSON ("browser_context_menu"' in ln:
        seg = ln[ln.find('", "') + 3:]
        seg = seg[:seg.find('", 多属性Schema')]
        raw_q = seg.replace('\\"', '').count('"')
        print('描述段内裸 ASCII 引号数 = %d (应为 0)' % raw_q)
        if raw_q:
            k = seg.replace('\\"', '').find('"')
            print('   附近: %r' % seg[max(0, k - 60):k + 60])
        break
