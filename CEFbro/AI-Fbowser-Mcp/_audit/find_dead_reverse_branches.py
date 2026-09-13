# -*- coding: utf-8 -*-
"""找出 Core 里**仍然存在**的 browser_reverse_* 死分支(与逆向分派的活分支重复)。

可达性论证(与上一轮删 6 个分支时相同, 已核实):
  主路由器: 否则 (是否以 (方法名, "browser_reverse_")) -> 交 逆向分派
  只有逆向分派返回**空串**时才会继续走回退链, 而回退链**不含**逆向分派;
  逆向分派的每个 browser_reverse_* 分支都以 返回(...) 结束(必返回非空)
  => Core 里同名分支永不可达。

本脚本只做**静态枚举与核对**, 不删任何东西; 删除由单独的脚本带前置校验执行。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')


def branches(path):
    """返回 {工具名: 出现行号列表}"""
    out = {}
    lines = io.open(path, encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines, 1):
        m = re.search(r'否则 \(方法名 == "([a-z0-9_.]+)"', l)
        if not m:
            m2 = re.search(r'如果 \(方法名 == "([a-z0-9_.]+)"', l)
            m = m2
        if m:
            out.setdefault(m.group(1), []).append(i)
    return out, lines


core, core_lines = branches(os.path.join(SRC, 'MCP_Server_Core.wsv'))
rev, rev_lines = branches(os.path.join(SRC, 'MCP_Server_Reverse.wsv'))

core_rev = {k: v for k, v in core.items() if k.startswith('browser_reverse_')}
rev_rev = {k: v for k, v in rev.items() if k.startswith('browser_reverse_')}

print('== Core 里的 browser_reverse_* 分支: %d 个 ==' % len(core_rev))
for k in sorted(core_rev):
    dup = '重复出现 %d 次' % len(core_rev[k]) if len(core_rev[k]) > 1 else ''
    live = '逆向分派**有**活分支 -> 死代码' if k in rev_rev else '逆向分派**无**此分支 -> 可能是活回退!'
    print('   %-44s Core行 %-14s %-12s %s' % (k, core_rev[k], dup, live))

print('\n== 逆向分派里的 browser_reverse_* 分支: %d 个 ==' % len(rev_rev))
only_core = sorted(set(core_rev) - set(rev_rev))
print('   只在 Core 里有的(需人工确认是否真活): %s' % (only_core or '无'))
only_rev = sorted(set(rev_rev) - set(core_rev))
print('   只在逆向分派里有的: %d 个(正常)' % len(only_rev))

print('\n== 汇总 ==')
dead = sorted(k for k in core_rev if k in rev_rev)
print('   可判定为死代码的 Core 分支 %d 个:' % len(dead))
for k in dead:
    print('      %-44s Core:%s   (活实现在 MCP_Server_Reverse.wsv:%s)'
          % (k, core_rev[k], rev_rev[k]))
