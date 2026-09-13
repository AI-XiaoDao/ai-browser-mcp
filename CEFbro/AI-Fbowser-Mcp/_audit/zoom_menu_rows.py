# -*- coding: utf-8 -*-
"""放大勾选臂的图标栏, 确认到底有没有勾(细勾在整屏缩放下可能看不见)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(ROOT, '_audit', 'shots')

# 裁剪图里 "自建勾选项" 大约在 y=533, 图标栏 x 从 88 起
jobs = [
    ('vis_check_our_crop.png', (86, 512, 306, 556), 'zoom_check_row.png'),
    ('vis_disable_our_crop.png', (86, 512, 306, 556), 'zoom_disable_row.png'),
    ('vis_relabel_def_crop.png', (86, 96, 306, 140), 'zoom_reload_row.png'),
]
for src, box, out in jobs:
    p = os.path.join(SH, src)
    if not os.path.exists(p):
        print('缺 %s' % p)
        continue
    im = Image.open(p)
    r = im.crop(box)
    r = r.resize((r.width * 4, r.height * 4), Image.LANCZOS)
    r.save(os.path.join(SH, out))
    print('%s %s -> %s (%dx%d)' % (src, box, out, r.width, r.height))
