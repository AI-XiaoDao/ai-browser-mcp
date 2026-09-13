# -*- coding: utf-8 -*-
r"""新增 `browser_hash`(MD5 / MD5文件 / XXH128 / CRC32) —— 依赖"本机已在册"的仰望模块。

注意: 本 docstring 必须是**原始字符串** —— 里面含 Windows 路径(`classlib\user\yw`),
普通三引号会把 `\u` 当转义并报 "truncated \uXXXX escape"(本轮已踩, 脚本根本没跑起来)。

可用性依据(全部只读实测, 见 `_audit/_hash_availability_r116.md`):
  · `E:\HSPC\plugins\vprj_win\classlib\user\yw\md5\md5_.h`(+.cpp)、`XxHash\xxhash.hpp` **都在**;
  · `仰望模块` **已在** `AI-Fbowser-Mcp.vprj` 的模块表里;
  · 类库签名(技能资料 `资料\类库\仰望模块\加密解密库__p.wsv` 原文):
      `MD5类_.取数据摘要_ (缓冲区数据 <字节集类>, 是否小写 <逻辑型 默认真>) -> 文本型`   (:60)
      `MD5类_.取数据摘要3_ (文件路径 <文本型>, 是否小写 <逻辑型 默认真>) -> 文本型`        (:83, "支持大文件")
      `XxHash数据摘要类_.取数据摘要_XxHash_数据 (数据 <通用型>, 数据长度 <变整数 默认-1>, 种子 <长整数 默认0>) -> 文本型` (:10)
      `CRC校验类_.取数据摘要_CRC32 (数据源 <字节集类>, CRC值 <整数 默认0>) -> 整数`        (:36, 走 ntdll, 无需外部头)

**不做 HMAC-MD5**: 类库那段走 CNG(`bcrypt.h` + `Bcrypt.lib`, 计划文档已列为风险), 本轮不引入新链接依赖。

诚实性处理: 文件类 action **先查文件是否存在**再算摘要 —— 否则 `取数据摘要2_` 会把"读不到文件"变成
空字节集, 从而**静默返回空文件的 MD5**(d41d8cd9…), 属典型假成功。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '哈希工具-写入前')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
TOOL = 'browser_hash'
problems = []


def count_braces(lines):
    o = c = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        o += body.count('{')
        c += body.count('}')
    return o, c


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def save(p, text, name):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    open(p, 'wb').write(text.encode('utf-8'))


NEW_ID = 1328
CORE_BLOCK = '''        // === 哈希/摘要 (仰望模块 加密解密库; 本机已实测头文件在册) ===
        否则 (方法名 == "browser_hash")
        {
            变量 hash动作 <类型 = 文本型>
            hash动作 = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            如果 (hash动作 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "action 不能省略 | 支持: md5(文本) / md5_file(文件) / xxhash(文本) / crc32(文本)"))
            }
            变量 hash大写 <类型 = 逻辑型>
            hash大写 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "uppercase", 假)
            变量 hash路径 <类型 = 文本型>
            hash路径 = MCP命令服务器.yyjson取文本 (参数JSON, "path")
            变量 hash数据 <类型 = 文本型>
            hash数据 = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (hash动作 == "md5_file")
            {
                如果 (hash路径 == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "md5_file 需要 path(文件完整路径)"))
                }
                如果 (文件是否存在 (hash路径) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "文件不存在: " + hash路径 + " | 说明: 类库读不到文件时会退化成空字节集, 从而静默返回空文件的 MD5, 故这里先拒绝"))
                }
                变量 hash文件摘要 <类型 = 文本型>
                hash文件摘要 = MD5类_.取数据摘要3_ (hash路径, hash大写 == 假)
                如果 (hash大写)
                {
                    hash文件摘要 = 到大写 (hash文件摘要)
                }
                变量 hash文件结果 <类型 = YYJSON对象类>
                hash文件结果.创建自文本 ("{}")
                hash文件结果.加入文本成员 ("action", "md5_file")
                hash文件结果.加入文本成员 ("md5", hash文件摘要)
                hash文件结果.加入文本成员 ("path", hash路径)
                hash文件结果.加入文本成员 ("algorithm", "MD5(流式, 支持大文件)")
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, hash文件结果.到可读文本 (YYJSON格式化选项.压缩)))
            }
            如果 (hash数据 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data 不能为空 | 空串摘要无意义(空文件 MD5 恒为 d41d8cd98f00b204e9800998ecf8427e), 如需请显式传一个空格"))
            }
            变量 hash字节 <类型 = 字节集类>
            hash字节 = 文本到UTF8 (hash数据, 假)
            变量 hash结果 <类型 = YYJSON对象类>
            hash结果.创建自文本 ("{}")
            hash结果.加入文本成员 ("action", hash动作)
            hash结果.加入整数成员 ("bytes", 取字节集长度 (hash字节))
            如果 (hash动作 == "md5")
            {
                变量 hash摘要 <类型 = 文本型>
                hash摘要 = MD5类_.取数据摘要_ (hash字节, hash大写 == 假)
                如果 (hash大写)
                {
                    hash摘要 = 到大写 (hash摘要)
                }
                hash结果.加入文本成员 ("md5", hash摘要)
                hash结果.加入文本成员 ("algorithm", "MD5")
            }
            否则 (hash动作 == "xxhash")
            {
                变量 hash摘要X <类型 = 文本型>
                hash摘要X = XxHash数据摘要类_.取数据摘要_XxHash_数据 (hash字节, -1, 0)
                如果 (hash大写)
                {
                    hash摘要X = 到大写 (hash摘要X)
                }
                hash结果.加入文本成员 ("xxhash", hash摘要X)
                hash结果.加入文本成员 ("algorithm", "XXH128")
            }
            否则 (hash动作 == "crc32")
            {
                hash结果.加入整数成员 ("crc32", CRC校验类_.取数据摘要_CRC32 (hash字节, 0))
                hash结果.加入文本成员 ("algorithm", "CRC32")
            }
            否则
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "未知 action: " + hash动作 + " | 支持: md5 / md5_file / xxhash / crc32"))
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, hash结果.到可读文本 (YYJSON格式化选项.压缩)))
        }
'''

SCHEMA_JSON = ('多属性Schema文本 (属性项JSON ("action", "text", "md5(文本摘要) / md5_file(文件摘要, 支持大文件) / '
               'xxhash(XXH128) / crc32") + "," + '
               '属性项JSON ("data", "text", "要摘要的文本(md5/xxhash/crc32 用)") + "," + '
               '属性项JSON ("path", "text", "文件完整路径(md5_file 用)") + "," + '
               '属性项JSON ("uppercase", "boolean", "true=摘要用大写输出(默认 false 小写)"), "\\"action\\"")')


def insert_after_line(lines, needle, block, tag):
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != 1:
        problems.append('%s: 定位 %d 行' % (tag, len(idx)))
        return
    i = idx[0]
    ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
    body = [(ind + b if b else '') for b in block]
    for b in body:
        if b and b.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, b.strip()[:90]))
            return
    lines[i + 1:i + 1] = body
    print('   ok %s (插在第 %d 行后, 共 %d 行)' % (tag, i + 1, len(body)))


def insert_before_line(lines, needle, block, tag):
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != 1:
        problems.append('%s: 定位 %d 行' % (tag, len(idx)))
        return
    i = idx[0]
    lines[i:i] = block
    print('   ok %s (插在第 %d 行前, 共 %d 行)' % (tag, i + 1, len(block)))


# ── Server: 注册表 + 工具登记 ──
s, nl = load(SERVER)
if s.count('"%s"' % TOOL) != 0:
    problems.append('Server: %s 改动前已出现 %d 次' % (TOOL, s.count('"%s"' % TOOL)))
else:
    ls = s.split('\n')
    before = count_braces(ls)
    insert_after_line(ls, '命令注册表.置整数值 ("browser_time_convert"',
                      ['命令注册表.置整数值 ("%s", %d)' % (TOOL, NEW_ID)], '注册表 %s' % TOOL)
    insert_after_line(ls, '添加工具JSON ("browser_time_convert"',
                      ['添加工具JSON ("%s", "哈希/摘要: MD5 / MD5(文件, 支持大文件) / XXH128 / CRC32。'
                       '实现走**仰望模块 加密解密库**(本机实测头文件在册: md5_.h/.cpp、xxhash.hpp); '
                       '文件摘要会先校验文件存在 —— 否则类库会把读不到文件退化成空字节集, 静默返回空文件 MD5。'
                       '注意: 字节集摘要按 UTF-8 取字节(data 是文本)' % TOOL,
                       SCHEMA_JSON + ')'], '工具登记 %s' % TOOL)
    after = count_braces(ls)
    if after != before:
        problems.append('Server 花括号变了: %s -> %s' % (before, after))
    else:
        save(SERVER, nl.join(ls), 'MCP_Server.wsv')
        print('   Server 写入完成 (花括号 %s 不变)' % (after,))

# ── Core: 分派分支 ──
c, nl2 = load(CORE)
ls2 = c.split('\n')
before2 = count_braces(ls2)
anchor = '// === 触摸事件 (CDP 派发优先; 内核注入为显式 opt-in) ==='
insert_before_line(ls2, anchor, [b.replace('\n', '') for b in CORE_BLOCK.split('\n')[:-1]],
                   'Core %s 分支' % TOOL)
after2 = count_braces(ls2)
if after2[0] - before2[0] != after2[1] - before2[1]:
    problems.append('Core 花括号增量不配平: Δ{=%d Δ}=%d' % (after2[0] - before2[0], after2[1] - before2[1]))
else:
    save(CORE, nl2.join(ls2), 'MCP_Server_Core.wsv')
    print('   Core 写入完成 (花括号增量 Δ{=%d Δ}=%d, 配平)' % (after2[0] - before2[0], after2[1] - before2[1]))

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
