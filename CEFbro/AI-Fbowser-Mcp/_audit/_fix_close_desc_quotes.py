# -*- coding: utf-8 -*-
r"""修 line 10760 的编译错误: 我新写的 browser_close 描述里用了 **ASCII 双引号**(火山字符串字面量内非法)。

教训(本项目第 N 次踩): 字符串字面量里只能写 `\"` 转义或中文引号「」; 用 `.replace` 精确替换那两个位置。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

PAIRS = [
    ('本应"先问页面、可被 beforeunload 否决"', '本应「先问页面、可被 beforeunload 否决」'),
    ('没有类库要求的"顶层窗口关闭处理器"', '没有类库要求的「顶层窗口关闭处理器」'),
]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    txt = raw.decode('utf-8')
    out = txt
    for old, new in PAIRS:
        n = out.count(old)
        assert n == 1, '锚点命中 %d 次: %s' % (n, old[:40])
        out = out.replace(old, new)
    # 断言: 目标行不再含裸 ASCII 引号(该行原有 4 个作为 JSON 分隔的引号是必须的, 只查新增的那两处已替换)
    print('两处 ASCII 引号已替换为中文引号')
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
