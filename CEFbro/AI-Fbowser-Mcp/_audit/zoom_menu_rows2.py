# -*- coding: utf-8 -*-
"""重做放大: 上一版从 x=86 起, 而图标栏其实在 x≈58..85(放大镜图标就在那儿), 勾会画在栏里。
这次从 x=36 起, 并把带图标的 "使用图片搜索功能进行搜索" 行一起放进来当**对照**(证明栏的位置)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(ROOT, '_audit', 'shots')

jobs = [
    # 勾选臂: 自建勾选项 行 + 上方 "翻译成中文(简体)" 空栏行 作为空白对照
    ('vis_check_our_crop.png', (36, 430, 306, 556), 'zoom2_check.png'),
    # 禁用臂同区域(灰字对照)
    ('vis_disable_our_crop.png', (36, 430, 306, 556), 'zoom2_disable.png'),
    # 图标栏位置对照: 使用图片搜索 / 发送到您的设备
    ('vis_check_our_crop.png', (36, 262, 306, 368), 'zoom2_icons.png'),
    # 改名臂: 重新加载 那一行
    ('vis_relabel_def_crop.png', (36, 96, 306, 160), 'zoom2_reload.png'),
]
for src, box, out in jobs:
    p = os.path.join(SH, src)
    if not os.path.exists(p):
        print('缺 %s' % p)
        continue
    im = Image.open(p)
    r = im.crop(box)
    r = r.resize((r.width * 3, r.height * 3), Image.LANCZOS)
    r.save(os.path.join(SH, out))
    print('%s %s -> %s (%dx%d)' % (src, box, out, r.width, r.height))
