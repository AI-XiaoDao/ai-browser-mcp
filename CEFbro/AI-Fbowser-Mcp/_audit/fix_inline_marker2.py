# -*- coding: utf-8 -*-
r"""正确拆分行尾标记: 新行的**行首必须保留 `#`**。

上一版把 MARK(`# ==== 启动期开关通道v1`)整段当分隔符, 结果拆出来的新行以 `: 启动期…` 开头,
**没有 `#` 前缀**, 依旧非法(所以错误数没变)。
正确做法: head = 原行去掉标记后的部分; 新行 = 缩进 + MARK + tail。
以 `_audit/_patched_MCP_Server.orig.wsv`(脚本保存的原始补丁版)为输入。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_IN = os.path.join(ROOT, '_audit', '_patched_MCP_Server.orig.wsv')
BAK = os.path.join(ROOT, '备份', '启动开关通道-写入前', 'MCP_Server.wsv')
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
MARK = '# ==== 启动期开关通道v1'

text = open(SRC_IN, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')

fixed = 0
for i, ln in enumerate(lines):
    if MARK in ln and not ln.lstrip().startswith('#'):
        head, _, tail = ln.partition(MARK)
        indent = re.match(r'\s*', ln).group(0)
        newline = indent + MARK + tail          # ★ 行首保留 `#`
        lines[i:i + 1] = [head.rstrip(), newline]
        fixed += 1
        print('拆分第 %d 行:' % (i + 1))
        print('   保留: %s' % head.rstrip()[:110])
        print('   独立: %s' % newline[:110])
print('拆分 %d 处' % fixed)

bak = open(BAK, 'rb').read().decode('utf-8').split('\n')
for i, ln in enumerate(lines):
    if '是否自动关闭JS对话框 <' in ln:
        ok = (ln == bak[387])
        print('第 %d 行 vs 备份第 388 行: %s' % (i + 1, ok))
        if not ok:
            print('   现: %r' % ln[:150])
            print('   备: %r' % bak[387][:150])
            sys.exit(1)
        break

# 全文件复检: 不允许出现"行尾 #"(即非行首的 #)
bad = [i + 1 for i, ln in enumerate(lines)
       if ln.lstrip().startswith(('@',))
       and '#' in ln]
print('以 @ 开头的行里含 # 的: %s' % (bad if bad else '无'))


def braces(ls):
    o = c = 0
    for ln in ls:
        if ln.lstrip().startswith(('@', '#', '//')):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        o += body.count('{')
        c += body.count('}')
    return o, c


print('花括号: 修后 %s vs 备份 %s' % (braces(lines), braces(bak)))
odd = [i + 1 for i, ln in enumerate(lines)
       if not ln.strip().startswith(('@', '#', '//'))
       and ln.replace('\\"', '').count('"') % 2 != 0]
print('引号奇数行 %d 条(备份同为 14 条属正常)' % len(odd))
open(SRC, 'wb').write(nl.join(lines).encode('utf-8'))
print('\n已写回 src/MCP_Server.wsv')
