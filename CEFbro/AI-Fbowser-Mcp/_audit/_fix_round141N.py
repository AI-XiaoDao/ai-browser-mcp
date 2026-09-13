# -*- coding: utf-8 -*-
r"""修: `取CDP结果对象` 里的局部变量名 `空对象` 与火山关键字冲突
(编译报错原文: 不能将成员"空对象"的名称设置为关键字名称)。改名为 `无结果对象`。
用法: py -3 _audit\_fix_round141N.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

OLD = '''        变量 空对象 <类型 = YYJSON只读对象类>
        如果 (外层.创建自文本 (同步结果JSON) == 假)
        {
            返回 (空对象)
        }'''
NEW = '''        变量 无结果对象 <类型 = YYJSON只读对象类>
        如果 (外层.创建自文本 (同步结果JSON) == 假)
        {
            返回 (无结果对象)
        }'''
OLD2 = '''        返回 (空对象)
    }

    # 类库 `值类型` 常量 → 可读名'''
NEW2 = '''        返回 (无结果对象)
    }

    # 类库 `值类型` 常量 → 可读名'''


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    n = 0
    for old, new in ((OLD, NEW), (OLD2, NEW2)):
        if old in txt:
            assert txt.count(old) == 1, '命中 %d 次' % txt.count(old)
            txt = txt.replace(old, new, 1)
            n += 1
    print('· 已替换 %d 处' % n)
    if APPLY and n:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    elif not APPLY:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
