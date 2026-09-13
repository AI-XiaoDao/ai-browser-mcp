# -*- coding: utf-8 -*-
"""FBroLib.v 是容器格式(有二进制头)。先看头部结构, 再尝试按偏移定位文本区。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

P = r'E:\HSPC\plugins\vprj_win\classlib\sys\FBrowser\FBroLib.v'
raw = open(P, 'rb').read()
print('大小 = %d' % len(raw))
print('头 64 字节 hex: %s' % raw[:64].hex(' '))
print('头 64 字节 repr: %r' % raw[:64])

# 找一个已知的中文片段(菜单) 在 utf-8 / gbk 下的字节, 定位文本区
for enc in ('utf-8', 'gbk'):
    for word in ('菜单模型', '是否禁止', '菜单'):
        b = word.encode(enc)
        idx = raw.find(b)
        print('%-6s %-8s -> %s' % (enc, word, idx))
