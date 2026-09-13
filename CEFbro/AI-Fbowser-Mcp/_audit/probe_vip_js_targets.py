# -*- coding: utf-8 -*-
"""调研 browser_vip_execute_js_context 的现状 + 类库的三个"按框架执行JS"方法签名。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"

print("== 1) 类库签名 ==")
WANT = ['高级_执行JS_主框架', '高级_执行JS_全部框架', '高级_执行JS_框架序号', '高级_执行JS']
for fn in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, fn)
    if not os.path.isfile(p):
        continue
    lines = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
    for i, l in enumerate(lines):
        s = l.strip()
        m = re.match(r'方法\s+(\S+)', s)
        if not m or m.group(1) not in WANT:
            continue
        print('%s:%d  %s' % (fn, i + 1, s[:150]))
        j = i + 1
        while j < len(lines):
            t = lines[j].strip()
            if t.startswith('参数'):
                print('      %s' % t[:130])
                j += 1
                continue
            if t == '' or t.startswith('//') or t.startswith('@'):
                j += 1
                continue
            break

print("\n== 2) 现有工具: 注册行 ==")
srv = io.open(os.path.join(SRC, 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')
for i, l in enumerate(srv, 1):
    if 'browser_vip_execute_js_context' in l and '添加工具JSON' in l:
        print('%5d| %s' % (i, l.strip()[:260]))

print("\n== 3) 现有实现: 分派分支位置 ==")
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith('.wsv') or '~vbak' in fn:
        continue
    for i, l in enumerate(io.open(os.path.join(SRC, fn), encoding='utf-8').read().split('\n'), 1):
        if 'browser_vip_execute_js_context' in l:
            print('   %s:%d  %s' % (fn, i, l.strip()[:150]))
