# -*- coding: utf-8 -*-
"""收尾本轮的系统性排查: browser_wait 的 `_load_phase` 字段是否真的**只写不读**(死字段)?

以及列出所有"发起导航"的调用点, 确认它们是否都用了**正确的**完成判据
(记录发起时刻 + 载入结束时刻 >= 发起时刻, 或地址已变), 以确认 scrape 是唯一的漏网者。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith('.wsv') and '~vbak' not in fn:
        files[fn] = io.open(os.path.join(SRC, fn), encoding='utf-8').read()

print("== 1) _load_phase 的全部出现 ==")
for fn, t in files.items():
    for i, l in enumerate(t.split('\n'), 1):
        if 'load_phase' in l:
            kind = '写' if ('加入整数成员' in l or '覆盖整数成员' in l) else '其它'
            print('   %-24s:%-6d [%s] %s' % (fn, i, kind, l.strip()[:120]))

print("\n== 2) 所有'发起导航'的调用点 ==")
NAV = re.compile(r'\.(载入地址|重新载入|重新载入_忽略缓存|后退|前进)\s*\(')
for fn, t in files.items():
    for i, l in enumerate(t.split('\n'), 1):
        if NAV.search(l):
            print('   %-24s:%-6d %s' % (fn, i, l.strip()[:130]))

print("\n== 3) 导航完成后使用的判据(供对照) ==")
for fn, t in files.items():
    for i, l in enumerate(t.split('\n'), 1):
        if '取最后载入结束毫秒' in l or '导航发起毫秒' in l or 'nav_start_ms' in l:
            print('   %-24s:%-6d %s' % (fn, i, l.strip()[:130]))
