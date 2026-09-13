# -*- coding: utf-8 -*-
r"""把**保存下来的补丁版** MCP_Server.wsv 修好(拆掉行尾标记)后再装回 src/。

前一步搞错了对象: 二分时我把 src/MCP_Server.wsv 还原成了补丁前版本, 于是"拆行尾标记"没东西可拆。
真正的缺陷文件是 `_audit/_patched_MCP_Server.wsv`。

缺陷: 补丁把标记 `# ==== 启动期开关通道v1 …` 并到了**已有成员声明的行尾**;
火山里 `#` 只在行首当注释, 行尾会变成非法记号 -> 整类编译不出来(只报别处的级联错)。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCHED = os.path.join(ROOT, '_audit', '_patched_MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '启动开关通道-写入前', 'MCP_Server.wsv')
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
MARK = '# ==== 启动期开关通道v1'

text = open(PATCHED, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')

fixed = 0
for i, ln in enumerate(lines):
    if MARK in ln and not ln.lstrip().startswith('#'):
        head, _, tail = ln.partition(MARK)
        indent = re.match(r'\s*', lines[i]).group(0)
        lines[i:i + 1] = [head.rstrip(), indent + tail]
        fixed += 1
        print('拆分第 %d 行:' % (i + 1))
        print('   保留: %s' % head.rstrip()[:110])
        print('   独立: %s' % (indent + tail)[:110])
print('拆分 %d 处' % fixed)

# 与备份核对被"还原"的那一行
bak = open(BAK, 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(lines):
    if '是否自动关闭JS对话框 <' in ln:
        print('第 %d 行 vs 备份第 388 行: %s' % (i + 1, ln == bak[387]))
        if ln != bak[387]:
            print('   现: %r' % ln[:140])
            print('   备: %r' % bak[387][:140])
            sys.exit(1)
        break

# 引号奇偶复检(与备份同类缺陷)
odd = [i + 1 for i, ln in enumerate(lines)
       if not ln.strip().startswith(('@', '#', '//'))
       and ln.replace('\\"', '').count('"') % 2 != 0]


def braces(ls):
    o = c = 0
    for ln in ls:
        if ln.lstrip().startswith(('@', '#', '//')):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        o += body.count('{')
        c += body.count('}')
    return o, c


print('引号奇数行: %d 条 (与备份同为 14 条属正常)' % len(odd))
print('花括号: 补丁版 %s vs 备份 %s' % (braces(lines), braces(bak)))

os.makedirs(os.path.dirname(BAK), exist_ok=True)
shutil.copy2(PATCHED, os.path.join(ROOT, '_audit', '_patched_MCP_Server.orig.wsv'))
open(SRC, 'wb').write(nl.join(lines).encode('utf-8'))
print('\n已把修好的补丁版装回 src/MCP_Server.wsv')
