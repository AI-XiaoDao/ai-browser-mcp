# -*- coding: utf-8 -*-
r"""修 CRC32 无符号值的两处编译错:
  ① 本项目**不存在** `到长整数 (整数)` —— 只有 `文本到长整数`(见 MCP_Kernel/MCP_Server 的 9 处用法)。
     改为**隐式加宽赋值**(编译器此前只对"长整数→整数"报精度损失, 说明方向敏感, 加宽可用);
  ② `加入整数成员` 收 整数, 传长整数会报精度损失 -> 用已存在的 `加入长整数成员`
     (项目里 3 处在用: MCP_BrowserEvents.wsv:657/759/761)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

OLD = '''                变量 hashCRC无符 <类型 = 长整数>
                hashCRC无符 = 到长整数 (hashCRC)
'''
NEW = '''                变量 hashCRC无符 <类型 = 长整数>
                hashCRC无符 = hashCRC
'''
OLD2 = '                hash结果.加入整数成员 ("crc32_unsigned", hashCRC无符)\n'
NEW2 = '                hash结果.加入长整数成员 ("crc32_unsigned", hashCRC无符)\n'

for old, new, tag in ((OLD, NEW, '加宽赋值'), (OLD2, NEW2, '长整数成员')):
    o = old.replace('\n', nl)
    if text.count(o) != 1:
        print('!! %s 锚点命中 %d 次' % (tag, text.count(o)))
        sys.exit(1)
    text = text.replace(o, new.replace('\n', nl), 1)
    print('   ok %s' % tag)
open(P, 'wb').write(text.encode('utf-8'))
print('已修正, 待编译验证')
