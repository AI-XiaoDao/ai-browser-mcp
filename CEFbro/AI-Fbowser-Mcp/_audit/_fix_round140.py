# -*- coding: utf-8 -*-
r"""修: `清空文本数组_就地` 是我臆造的方法名(编译报错原文: 没有找到所指定的方法名称)。
改为项目既有做法 —— 循环 删除成员(0)(见 `清空持久V8扩展` 的实现)。
用法: py -3 _audit\_fix_round140.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

OLD = '            清空文本数组_就地 (启动期事件缓冲)'
NEW = ('            // 清空缓冲: 文本数组类没有"清空()", 项目既有做法是循环 删除成员(0) (见 清空持久V8扩展)\n'
       '            判断循环 (启动期事件缓冲.取成员数 () > 0)\n'
       '            {\n'
       '                启动期事件缓冲.删除成员 (0)\n'
       '            }')


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    if OLD not in txt:
        print('· 未找到(可能已修)')
        return
    assert txt.count(OLD) == 1, '命中 %d 次' % txt.count(OLD)
    txt = txt.replace(OLD, NEW, 1)
    print('· 已改为 循环 删除成员(0)')
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
