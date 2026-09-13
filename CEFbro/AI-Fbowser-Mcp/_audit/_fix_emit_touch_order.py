# -*- coding: utf-8 -*-
r"""修正 _apply_emit_touch_cdp 的插入顺序: 新增块尾部误带了一行 `如果 (vipTouch.是否为空 () == 假)`,
而它出现在 `变量 vipTouch ...` 声明**之前** -> 编译报"没有找到所指定的常量/变量/参数名称 vipTouch"。
本脚本删掉那一行重复守卫(原代码里紧跟声明之后本来就有同样的守卫)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')

BAD = [
    '            如果 (vipTouch.是否为空 () == 假)',
    '            变量 vipTouch <类型 = 类_FBrowserVIP_控制器>',
]
GOOD = [
    '            变量 vipTouch <类型 = 类_FBrowserVIP_控制器>',
]


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == [x.strip() for x in block]]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    lines = raw.decode('utf-8').split('\n')
    hits = find_block(lines, BAD)
    assert len(hits) == 1, '锚点命中 %d 次(期望 1)' % len(hits)
    s = hits[0]
    out = lines[:s] + GOOD + lines[s + len(BAD):]
    # 断言: 修完后 vipTouch 声明之前不再有对它的引用
    decl = [i for i, l in enumerate(out) if l.strip().startswith('变量 vipTouch')][0]
    for i in range(max(0, decl - 12), decl):
        assert 'vipTouch.' not in out[i], '声明前仍有 vipTouch 引用: %s' % out[i]
    print('已删除锚点 @%d 处的重复守卫; 行数 %d -> %d' % (s + 1, len(lines), len(out)))
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
