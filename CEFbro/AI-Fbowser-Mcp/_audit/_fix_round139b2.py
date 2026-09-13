# -*- coding: utf-8 -*-
r"""修第139轮补丁 B 写入时的**转义丢失**(补丁脚本里 `\"` 被 Python 当普通引号吞掉):
  · `项明细 = 项明细 + "{"index":" + ...` 应为 `"{\"index\":"`
  · `,"has_accel":true"` 应为 `",\"has_accel\":true"`
  · `菜单快照JSON = "{"success":true,...` 整行需要 \\" 转义
  · `字符` 是火山关键字 → 改名 扫描字符
用法: py -3 _audit\_fix_round139b2.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

FIXES = [
    ('            变量 字符 <类型 = 文本型>\n            字符 = 取文本中间 (快捷键原文, 扫描位 - 1, 1)\n            如果 (寻找文本 ("0123456789", 字符, 0, 假) != -1)\n            {\n                键码文本 = 键码文本 + 字符\n            }',
     '            变量 扫描字符 <类型 = 文本型>\n            扫描字符 = 取文本中间 (快捷键原文, 扫描位 - 1, 1)\n            如果 (寻找文本 ("0123456789", 扫描字符, 0, 假) != -1)\n            {\n                键码文本 = 键码文本 + 扫描字符\n            }'),
    ('            项明细 = 项明细 + "{"index":" + 到文本 (已读)',
     '            项明细 = 项明细 + "{\\"index\\":" + 到文本 (已读)'),
    ('                项明细 = 项明细 + ","has_accel":true"',
     '                项明细 = 项明细 + ",\\"has_accel\\":true"'),
    ('                项明细 = 项明细 + ","has_accel":false"',
     '                项明细 = 项明细 + ",\\"has_accel\\":false"'),
    ('        项明细 = 项明细 + "}"',
     '            项明细 = 项明细 + "}"'),
]

# 整行替换: 菜单快照JSON 那一行(含 note 文本)按正确转义重写
SNAP_OLD_START = '        菜单快照JSON = "{"success":true,"declared_count":"'
SNAP_NEW = ('        菜单快照JSON = "{\\"success\\":true,\\"declared_count\\":" + 到文本 (总项数) + ",\\"read_count\\":" + 到文本 (已读) + '
            '",\\"items\\":" + 项明细 + ",\\"note\\":\\"这是**浏览器默认菜单**的实况(每次右键都是全新默认模型, 索引仅本次有效) | '
            '可读范围: 条目数 + 每项是否带快捷键提示(其余只读 getter 只收命令ID, 对默认项读不到) | '
            '若同时预置了 browser_context_menu 规格, 本快照反映的是**施加之前**的状态\\"}"')


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    for old, new in FIXES:
        if old not in txt:
            print('· 未找到(可能已修): %s' % old.strip().split('\n')[0][:70])
            continue
        assert txt.count(old) == 1, '锚点命中 %d 次: %s' % (txt.count(old), old[:60])
        txt = txt.replace(old, new, 1)
        print('· 已修: %s' % old.strip().split('\n')[0][:70])
    # 快照JSON 整行
    lines = txt.split('\n')
    hit = 0
    for i, l in enumerate(lines):
        if l.startswith(SNAP_OLD_START):
            lines[i] = SNAP_NEW
            hit += 1
    print('· 菜单快照JSON 行重写: %d 处' % hit)
    txt = '\n'.join(lines)
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
