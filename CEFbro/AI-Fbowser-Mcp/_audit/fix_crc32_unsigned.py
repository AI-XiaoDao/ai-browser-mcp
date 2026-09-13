# -*- coding: utf-8 -*-
r"""CRC32 同时给出**无符号值**: 类库 `取数据摘要_CRC32` 返回 `整数`(int32), 于是
`crc32("123456789")` 得到 -873187034, 而 CRC-32/ISO-HDLC 的标准校验值是 0xCBF43926 = **3421780262**。
两者是同一组 32 位, 但用户拿标准值对照时会以为算错 —— 故回包同时给 `crc32`(类库原样, 有符号)
与 `crc32_unsigned`(加 2^32 归一)。纯算术实现, 不引入位运算语义风险。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '哈希工具-写入前')

text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

OLD = '''            否则 (hash动作 == "crc32")
            {
                hash结果.加入整数成员 ("crc32", CRC校验类_.取数据摘要_CRC32 (hash字节, 0))
                hash结果.加入文本成员 ("algorithm", "CRC32")
            }
'''
NEW = '''            否则 (hash动作 == "crc32")
            {
                // 类库返回 整数(int32): `crc32("123456789")` = -873187034, 而 CRC-32/ISO-HDLC 的标准校验值
                // 是 0xCBF43926 = 3421780262 —— 同一组 32 位, 但拿标准值对照会以为算错。故两种表示都给。
                变量 hashCRC <类型 = 整数>
                hashCRC = CRC校验类_.取数据摘要_CRC32 (hash字节, 0)
                变量 hashCRC无符 <类型 = 长整数>
                hashCRC无符 = 到长整数 (hashCRC)
                如果 (hashCRC < 0)
                {
                    hashCRC无符 = hashCRC无符 + 4294967296
                }
                hash结果.加入整数成员 ("crc32", hashCRC)
                hash结果.加入整数成员 ("crc32_unsigned", hashCRC无符)
                hash结果.加入文本成员 ("algorithm", "CRC32 (标准校验值请用 crc32_unsigned: 123456789 -> 3421780262 / 0xCBF43926)")
            }
'''
if text.count(OLD.replace('\n', nl)) != 1:
    print('!! 锚点命中 %d 次, 未改' % text.count(OLD.replace('\n', nl)))
    sys.exit(1)
text = text.replace(OLD.replace('\n', nl), NEW.replace('\n', nl), 1)
os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, 'MCP_Server_Core.wsv')
if not os.path.exists(dst):
    shutil.copy2(P, dst)
open(P, 'wb').write(text.encode('utf-8'))
print('已加 crc32_unsigned')

# 工具描述同步
S = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
s = open(S, 'rb').read().decode('utf-8')
old2 = 'CRC32。实现走仰望模块'
new2 = 'CRC32(同时给有符号 crc32 与标准无符号 crc32_unsigned)。实现走仰望模块'
if s.count(old2) == 1:
    open(S, 'wb').write(s.replace(old2, new2, 1).encode('utf-8'))
    print('工具描述已同步')
else:
    print('!! 工具描述锚点命中 %d 次(可忽略, 不影响功能)' % s.count(old2))
