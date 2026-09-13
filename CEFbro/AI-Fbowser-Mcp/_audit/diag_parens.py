# -*- coding: utf-8 -*-
r"""诊断 `MCP_Server.wsv:10243 括号缺失或不匹配`: **剥掉字符串后**再数括号, 并与一条已知良好的同类行对比。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
ls = open(P, 'rb').read().decode('utf-8').split('\n')


def strip_strings(s):
    return re.sub(r'\\"|"(?:[^"\\]|\\.)*"', '""', s)


def analyze(i, label):
    ln = ls[i]
    body = strip_strings(ln)
    print('== %s (第 %d 行) ==' % (label, i + 1))
    print('   剥字符串后: ( = %d, ) = %d, 差 = %d' % (body.count('('), body.count(')'),
                                                      body.count('(') - body.count(')')))
    print('   尾部 160: %s' % body[-160:])
    # 找第一个深度为负的位置
    depth = 0
    for k, ch in enumerate(body):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                print('   ★ 深度在第 %d 字符处变负: ...%s' % (k, body[max(0, k - 60):k + 20]))
                break
    print('   末尾深度 = %d (应为 0)' % depth)
    print()


# 出问题那行
analyze(10242, '出问题的行')

# 一条已知良好的同类注册行(带 多属性Schema文本 + 必填字段)
cands = [i for i, ln in enumerate(ls) if '添加工具JSON' in ln and '多属性Schema文本' in ln
         and '\"action\"' in ln]
if cands:
    analyze(cands[0], '已知良好的对照行')
else:
    print('没找到对照行')
