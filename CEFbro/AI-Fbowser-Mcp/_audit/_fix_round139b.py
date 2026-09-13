# -*- coding: utf-8 -*-
r"""修第139轮补丁 B 的两个编译错误(实测报错原文):
  · `不能将成员"字符"的名称设置为关键字名称` —— `字符` 是火山关键字(字符型), 不能当变量名;
  · `没有找到所指定的方法名称"大写"` —— 正确命令是 `到大写`。
用法: py -3 _audit\_fix_round139b.py [--apply]
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
    ('        变量 字符 <类型 = 文本型>\n        字符 = 取文本中间 (快捷键原文, 扫描位 - 1, 1)\n        如果 (寻找文本 ("0123456789", 字符, 0, 假) != -1)\n        {\n            键码文本 = 键码文本 + 字符\n        }',
     '        变量 扫描字符 <类型 = 文本型>\n        扫描字符 = 取文本中间 (快捷键原文, 扫描位 - 1, 1)\n        如果 (寻找文本 ("0123456789", 扫描字符, 0, 假) != -1)\n        {\n            键码文本 = 键码文本 + 扫描字符\n        }'),
    ('        高值 = 寻找文本 (十六进制表, 大写 (高字符), 0, 假)', '        高值 = 寻找文本 (十六进制表, 到大写 (高字符), 0, 假)'),
    ('        低值 = 寻找文本 (十六进制表, 大写 (低字符), 0, 假)', '        低值 = 寻找文本 (十六进制表, 到大写 (低字符), 0, 假)'),
]


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    for old, new in FIXES:
        if old not in txt:
            print('· 未找到(可能已修): %s' % old.split('\n')[0][:60])
            continue
        assert txt.count(old) == 1, '锚点命中 %d 次' % txt.count(old)
        txt = txt.replace(old, new, 1)
        print('· 已修: %s' % old.split('\n')[0].strip()[:60])
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
