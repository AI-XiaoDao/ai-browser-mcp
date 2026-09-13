# -*- coding: utf-8 -*-
"""修复 MCP_Server_Utils.wsv: 上一版清理脚本的换行盲点把两行粘在了一起。

事故经过:
  该文件是 **CRLF**, 而那两条"备注"是**行尾 C++ 注释**(`else out.clear();  // 修复: ...`)。
  脚本按 `old + '\n'` 判断可整行删除, 在 CRLF 文件里恰好匹配到 `\r\n` 的 `\n`,
  于是只删掉了 `\n` 而把 `\r` 留下 -> 下一行被粘到本行 -> 注入的 C++ 里出现裸 `@`
  -> 编译报 `error C2018: 未知字符 '0x40'`(这正是本次构建暴露的问题)。

正确做法(本脚本):
  1. 先从备份恢复该文件;
  2. 只**改写注释文本本身**(不动行结构), 把"修复: X"的历史口吻改成"为什么必须 X"的约束陈述;
  3. 严格保留原行尾(CRLF)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Utils.wsv')
BAK = os.path.join(ROOT, '备份', '过程性备注清理-写入前', 'MCP_Server_Utils.wsv')

if not os.path.exists(BAK):
    print('!! 备份不存在, 中止: %s' % BAK)
    sys.exit(1)

before = io.open(BAK, encoding='utf-8', newline='').read()
crlf = before.count('\r\n')
lf = before.count('\n') - crlf
print('备份: CRLF=%d LF=%d 总行=%d' % (crlf, lf, before.count('\n') + 1))
if crlf == 0:
    print('!! 备份不是 CRLF, 与事故分析不符, 中止以免改错')
    sys.exit(1)

PAIRS = [
    ('// 修复: 转换失败时丢弃, 不把NUL填充写入stderr',
     '// 转换失败必须丢弃: 否则会把 NUL 填充写进 stderr'),
    ('// 修复: 正文+换行单次写出, 防多线程日志交错错位',
     '// 正文与换行必须单次写出: 分两次写会让多线程日志交错错位'),
]

text = before
for old, new in PAIRS:
    c = text.count(old)
    print('  锚点命中 %d : %s' % (c, old[:50]))
    if c != 1:
        print('!! 锚点不唯一, 中止')
        sys.exit(1)
    text = text.replace(old, new, 1)

if text.count('\r\n') != crlf:
    print('!! 行尾数量变了(会再次破坏行结构), 中止')
    sys.exit(1)

open(SRC, 'wb').write(text.encode('utf-8'))
print('已恢复并改写; CRLF=%d 保持不变; 行数 %d'
      % (text.count('\r\n'), text.count('\n') + 1))

# 复核: 注入块里不应出现裸 @ 粘连
lines = text.split('\r\n')
bad = [i + 1 for i, l in enumerate(lines) if l.count('@') > 1 and l.strip().startswith('@')]
print('复核: 单行出现多个 @ 的行: %s (应为空)' % (bad or '无'))
