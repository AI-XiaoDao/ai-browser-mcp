# -*- coding: utf-8 -*-
r"""修: 新写的截图描述里误用 ASCII 双引号(火山要求字符串内部用「」)。
编译报错原文: `<MCP_Server.wsv>, 11754: 错误: 发现字符处于无效位置`。
用法: py -3 _audit\_fix_round141M.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

OLD = '''为假时类库截的是"窗口可见区"且**宽高/缩放全被忽略**'''
NEW = '''为假时类库截的是「窗口可见区」且**宽高/缩放全被忽略**'''


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    if OLD not in txt:
        print('· 未找到(可能已修)')
        return
    assert txt.count(OLD) == 1, '命中 %d 次' % txt.count(OLD)
    txt = txt.replace(OLD, NEW, 1)
    print('· 已把 ASCII 引号改为「」')
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
