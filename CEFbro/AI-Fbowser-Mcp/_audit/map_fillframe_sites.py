# -*- coding: utf-8 -*-
r"""为 G1 做准备: 列出 `取主填表框架 ()` 每个调用点**所属的工具名**与所在方法, 判断能否直接接 `frame_id`。

判据: 该调用点所在的**分派方法**里必须能拿到 `参数JSON`(回调类里没有), 否则跳过。
输出: 文件:行 | 工具名 | 是否可分派(能读参数) | 所在方法
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
FILES = ["MCP_Server_Form.wsv", "MCP_Server_Core.wsv", "MCP_Callbacks.wsv",
         "MCP_Server_VIP.wsv", "MCP_Server_System.wsv"]

TARGET = '取主填表框架 ()'
rows = []
for f in FILES:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    ls = open(p, 'rb').read().decode('utf-8').split('\n')
    # 预扫描: 每个方法的起点与其是否含 参数JSON 形参
    methods = []
    for i, ln in enumerate(ls):
        m = re.match(r'\s*方法\s+(\S+)', ln)
        if m:
            methods.append((i, m.group(1)))
    for i, ln in enumerate(ls):
        if TARGET not in ln:
            continue
        # 所属方法
        owner = None
        for (mi, mn) in methods:
            if mi <= i:
                owner = (mi, mn)
            else:
                break
        # 该方法的签名区(方法行到下个方法行)是否含 参数JSON
        sig_has_json = False
        if owner:
            mi = owner[0]
            for k in range(mi, min(mi + 25, len(ls))):
                if re.match(r'\s*方法\s+', ls[k]) and k != mi:
                    break
                if '参数JSON' in ls[k]:
                    sig_has_json = True
                    break
        # 向上找最近的 方法名 == "工具名"
        tool = None
        for k in range(i, max(0, i - 400), -1):
            m2 = re.search(r'方法名 == "([a-z0-9_]+)"', ls[k])
            if m2:
                tool = m2.group(1)
                break
        rows.append((f, i + 1, tool or '(未找到分支)', sig_has_json, owner[1] if owner else '?'))

print('%-22s %-6s %-34s %-10s %s' % ('文件', '行', '工具名', '可接frame', '所属方法'))
for r in rows:
    print('%-22s %-6d %-34s %-10s %s' % (r[0], r[1], r[2], '是' if r[3] else '否(跳过)', r[4]))
ok = [r for r in rows if r[3] and r[2] != '(未找到分支)']
print('\n可分派且能定位工具的调用点 = %d / %d' % (len(ok), len(rows)))
tools = sorted({r[2] for r in ok})
print('涉及工具 %d 个:' % len(tools))
for t in tools:
    print('   %s' % t)
