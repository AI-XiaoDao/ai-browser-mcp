# -*- coding: utf-8 -*-
"""核对: 项目重写的这几个"资源处理器/过滤器"虚拟方法名, 是否与类库声明的名字**逐字一致**?

`@虚拟方法 = 可覆盖` 只是标注; 若方法名与基类不一致, 编译器不报错, 而 CEF 永远不会调用它
—— 这正是"规则存进去了、也报成功, 但页面上什么都没发生"的典型成因。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"

if not os.path.isdir(LIB):
    print('!! 类库目录不存在: %s' % LIB)
    sys.exit(1)

print("== 类库里所有含'资源'的 方法/事件 名 ==")
seen = set()
for fn in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, fn)
    if not os.path.isfile(p):
        continue
    for i, l in enumerate(io.open(p, encoding='utf-8', errors='replace').read().split('\n'), 1):
        s = l.strip()
        m = re.match(r'(方法|事件)\s+(\S+)', s)
        if m and '资源' in m.group(2):
            key = m.group(2)
            if key in seen:
                continue
            seen.add(key)
            print('   %-40s %s:%d  %s' % (key, fn, i, ('@虚拟方法' in s and '[可覆盖]' or '')))

print("\n== 项目里重写的相关方法 ==")
P = os.path.join(ROOT, 'src', 'MCP_BrowserEvents.wsv')
for i, l in enumerate(io.open(P, encoding='utf-8').read().split('\n'), 1):
    s = l.strip()
    m = re.match(r'方法\s+(\S+)', s)
    if m and ('资源' in m.group(1)):
        print('   %-40s MCP_BrowserEvents.wsv:%d  %s' % (m.group(1), i, s[:110]))

print("\n== 结论判据 ==")
print("   若项目的名字不在上面'类库'清单里 -> 该重写永远不会被 CEF 调用(静默失效)")
