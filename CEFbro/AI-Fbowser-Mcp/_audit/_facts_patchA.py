# -*- coding: utf-8 -*-
r"""只读: 补丁 A 需要的现状细节
① MCP_Server_VIP.wsv 行尾; ② pixel_ratio 与 touch_cancel 分支现状; ③ 5 个工具的注册行原文。
用法: py -3 _audit\_facts_patchA.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

b = io.open(os.path.join(SRC, 'MCP_Server_VIP.wsv'), 'rb').read()
print('① VIP: CRCRLF=%d CRLF=%d LF=%d' % (b.count(b'\r\r\n'), b.count(b'\r\n'), b.count(b'\n')))

t = io.open(os.path.join(SRC, 'MCP_Server_VIP.wsv'), encoding='utf-8', newline='').read().split('\n')


def show(tag, pat, before=0, after=14):
    for i, l in enumerate(t):
        if pat in l:
            print('\n② %s @%d' % (tag, i + 1))
            for j in range(max(0, i - before), min(len(t), i + after)):
                s = t[j].replace('\r', '')
                if s.strip():
                    print('   %d %s' % (j + 1, s[:150]))
            return
    print('\n② %s: 未找到' % tag)


show('pixel_ratio 分派', 'browser_fingerprint_pixel_ratio')
show('touch_cancel 分派', 'browser_vip_touch_cancel')

print('\n③ 注册行:')
srv = io.open(os.path.join(SRC, 'MCP_Server.wsv'), encoding='utf-8', newline='').read().split('\n')
for name in ('browser_key_event', 'browser_vip_mouse_press', 'browser_vip_mouse_release',
             'browser_vip_touch_cancel', 'browser_vip_mouse_click', 'browser_fingerprint_pixel_ratio',
             'browser_screenshot'):
    hit = False
    for i, l in enumerate(srv):
        if '添加工具JSON ("%s"' % name in l or ('添加工具JSON ("%s"' % name) in l:
            print('   %s @%d: %s' % (name, i + 1, l.strip()[:400]))
            hit = True
    if not hit:
        print('   %s: 未找到注册行' % name)
