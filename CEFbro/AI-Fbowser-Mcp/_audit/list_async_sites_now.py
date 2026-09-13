# -*- coding: utf-8 -*-
"""列出逆向分派/Core 里仍走异步入口的调用点原文(用于精确替换)。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

TARGETS = {
    'MCP_Server_Reverse.wsv': [
        'DOMDebugger.setXHRBreakpoint', 'DOMDebugger.setEventListenerBreakpoint',
        'DOMDebugger.setInstrumentationBreakpoint', 'Debugger.setBreakpointOnFunctionCall',
        'Page.addScriptToEvaluateOnNewDocument', 'Network.enable',
        'HeapProfiler.takeHeapSnapshot', 'HeapProfiler.startSampling',
    ],
    'MCP_Server_Core.wsv': ['browser_cdp'],  # 该工具本身是通用 CDP 直通
}

for fn, keys in TARGETS.items():
    p = os.path.join(SRC, fn)
    lines = io.open(p, encoding='utf-8').read().split('\n')
    print('== %s ==' % fn)
    for i, l in enumerate(lines, 1):
        if '执行逆向CDP命令' not in l and '执行CDP命令_带参数' not in l:
            continue
        m = re.search(r'"([A-Za-z]+\.[A-Za-z]+)"', l)
        meth = m.group(1) if m else ''
        if keys == ['browser_cdp'] or meth in keys:
            print('   行 %-5d [%s]' % (i, meth))
            print('      %s' % l.rstrip())
    # browser_cdp 的工具分支
    if keys == ['browser_cdp']:
        for i, l in enumerate(lines, 1):
            if re.search(r'方法名 == "browser_cdp"', l):
                print('   browser_cdp 分支起始行: %d' % i)
                for j in range(i, min(i + 26, len(lines))):
                    print('      %s' % lines[j].rstrip()[:150])
                break
    print()
