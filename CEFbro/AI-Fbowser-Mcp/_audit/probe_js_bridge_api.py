# -*- coding: utf-8 -*-
"""调研 FBrowser_JS交互_注册/删除: 签名、依赖(是否要回调类)、以及官方例子里怎么用。

价值判断前置: 本项目已有先例 —— 原生回调式 API 在本内核"恒返回空值并被写成字面 null"。
若该通道也依赖回调类且无可验证的返回值, 贸然接线会再造一个"静默失效"的能力。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
EXAMPLE_DIRS = [
    r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\例子",
]

print("== 1) 类库里的 JS交互 相关方法 ==")
for fn in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, fn)
    if not os.path.isfile(p):
        continue
    lines = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
    for i, l in enumerate(lines):
        s = l.strip()
        if ('JS交互' in s or '交互_注册' in s) and re.match(r'(方法|事件|类)\s+', s):
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

print("\n== 2) 相关回调类是否存在 ==")
for fn in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, fn)
    if not os.path.isfile(p):
        continue
    for i, l in enumerate(io.open(p, encoding='utf-8', errors='replace').read().split('\n'), 1):
        s = l.strip()
        if re.match(r'类\s+', s) and ('JS交互' in s or 'JS查询' in s or '交互' in s):
            print('%s:%d  %s' % (fn, i, s[:140]))

print("\n== 3) 官方例子里是否真的用过它 ==")
for d in EXAMPLE_DIRS:
    if not os.path.isdir(d):
        print('   (目录不存在: %s)' % d)
        continue
    hit = 0
    for root, _, files in os.walk(d):
        for f in files:
            if not f.endswith('.wsv'):
                continue
            p = os.path.join(root, f)
            try:
                txt = io.open(p, encoding='utf-8', errors='replace').read()
            except Exception as ex:
                print('   读取失败 %s: %s' % (p, ex))
                continue
            if 'JS交互' in txt:
                hit += 1
                for i, l in enumerate(txt.split('\n'), 1):
                    if 'JS交互' in l:
                        print('   %s:%d  %s' % (os.path.relpath(p, d), i, l.strip()[:140]))
    print('   含 "JS交互" 的例子文件数: %d' % hit)
