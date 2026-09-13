# -*- coding: utf-8 -*-
"""收尾: 撤仪表 + 把"列位错位"这种**真实易犯的错误**变成 set 阶段的明确拒绝。

背景: 我自己的规格写成了 `relabel||26502|改名了|1|0|`(标签放错到第4列, 又多一个尾部分隔符 -> 7 段),
解析后 参数/父命令ID 整体错位, 父ID 变成 1 -> 施加时被"父菜单不存在"跳过, 只留一条 last_error。
这正是本轮要消灭的"难懂失败", 所以:
  · Core 校验侧: 段数 > 6 直接拒绝并讲清列位(合法格式最多 6 列)。
  · 施加侧: "父菜单不存在"的跳过文案补上列位提示。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
problems = []


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def rep(text, old, new, tag, nl='\n', n=1):
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != n:
        problems.append('%s: 命中 %d 次(应 %d)' % (tag, c, n))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:80]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), n)


# ───────── Server: 撤仪表 + 跳过文案 ─────────
s, nl = load(SERVER)
s = rep(s, '失败明细 = 失败明细 + "[F" + 到文本 (失败条数) + "]" + 菜单失败说明 (',
        '失败明细 = 失败明细 + 菜单失败说明 (', '撤 [F] 标记', nl, 7)
s = rep(s, '''        菜单施加失败 = 失败明细
        如果 (失败条数 > 0)
        {
            菜单上次错误 = "仪表 失败条数=" + 到文本 (失败条数) + " 明细=[" + 失败明细 + "]"
        }
''', '        菜单施加失败 = 失败明细\n', '撤仪表 last_error 写入', nl)
s = rep(s, '                菜单上次错误 = "父菜单不存在, 跳过: " + 行文本\n',
        '                菜单上次错误 = "父菜单不存在, 跳过: " + 行文本 + " | 第5列是父命令ID(想要顶层项该列为 0 或留空); 列位: 类型|标签|命令ID|参数|父命令ID|快捷键"\n',
        '父菜单跳过文案补列位提示', nl)
open(SERVER, 'wb').write(s.encode('utf-8'))

# ───────── Core: 段数 > 6 直接拒绝 ─────────
c, nl2 = load(CORE)
c = rep(c, '''                    如果 (cm段.取成员数 () < 3)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行字段不足(至少 类型|标签|命令ID): " + cm行))
                    }
''', '''                    如果 (cm段.取成员数 () < 3)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行字段不足(至少 类型|标签|命令ID): " + cm行))
                    }
                    // 合法规格最多 6 列(类型|标签|命令ID|参数|父命令ID|快捷键)。多于 6 列几乎总是**列位写错**
                    // (例如把"修改类的新标签"写到第4列, 于是 参数/父命令ID 整体错位, 施加时被当成子项跳过)。
                    如果 (cm段.取成员数 () > 6)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行字段过多(" + 到文本 (cm段.取成员数 ()) + " 段, 最多 6): " + cm行 + " | 列位固定为 类型|标签|命令ID|参数|父命令ID|快捷键 —— 修改类的**新标签写第2列**(如 relabel|新名字|26501|1|0|), 快捷键写第6列(如 accel||26501|1|0|70C|)"))
                    }
''', 'Core 拒绝 >6 段', nl2)
open(CORE, 'wb').write(c.encode('utf-8'))
print('问题: %r' % problems)
sys.exit(1 if problems else 0)
