# -*- coding: utf-8 -*-
r"""补做 `browser_hash` 的**工具登记行**(上一版把描述串的收尾引号漏了, 被自检拦下)。

现状: 注册表项 `命令注册表.置整数值 ("browser_hash", 1328)` 与 Core 分派分支**已写入**,
只差 `添加工具JSON (...)` 这一行 —— 没有它工具不会出现在 tools/list 里(可路由但不可发现)。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '哈希工具-写入前')

text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')

if '添加工具JSON ("browser_hash"' in text:
    print('已存在工具登记行, 无需补做')
    sys.exit(0)

DESC = ('哈希/摘要: MD5(文本) / MD5(文件, 支持大文件) / XXH128 / CRC32。'
        '实现走仰望模块 加密解密库(本机实测头文件在册: md5_.h/.cpp、xxhash.hpp); '
        '文件摘要会**先校验文件存在** —— 否则类库会把读不到文件退化成空字节集, 从而静默返回空文件的 MD5。'
        '说明: data 按 UTF-8 取字节; 输出默认小写, uppercase:true 切大写')
SCHEMA = ('多属性Schema文本 (属性项JSON ("action", "text", '
          '"md5(文本摘要) / md5_file(文件摘要, 支持大文件) / xxhash(XXH128) / crc32") + "," + '
          '属性项JSON ("data", "text", "要摘要的文本(md5/xxhash/crc32 用)") + "," + '
          '属性项JSON ("path", "text", "文件完整路径(md5_file 用)") + "," + '
          '属性项JSON ("uppercase", "boolean", "true=摘要用大写输出(默认 false 小写)"), "\\"action\\"")')
NEW = '添加工具JSON ("browser_hash", "%s", %s)' % (DESC, SCHEMA)
if NEW.replace('\\"', '').count('"') % 2 != 0:
    print('!! 新行引号奇数: %r' % NEW[:120])
    sys.exit(1)

idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_time_convert"' in ln]
if len(idx) != 1:
    print('!! 锚点定位 %d 行' % len(idx))
    sys.exit(1)
i = idx[0]
ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
lines[i + 1:i + 1] = [ind + NEW]

os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, 'MCP_Server.wsv')
if not os.path.exists(dst):
    shutil.copy2(P, dst)
open(P, 'wb').write(nl.join(lines).encode('utf-8'))
print('已插入工具登记行(第 %d 行后), 长度 %d' % (i + 1, len(NEW)))
