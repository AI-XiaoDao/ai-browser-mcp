# -*- coding: utf-8 -*-
"""两处精修:
① 段数校验放宽到"允许行尾多一个空段"(行尾补 | 是常见写法), 只拒绝真正的列位错位。
② 施加侧的**跳过**(父菜单不存在 / 命令ID<1)也要进 菜单施加失败, 否则规格写错时仍然只有 0 条生效
   而无任何解释 —— 这正是我上一轮踩到的坑(4 条规格被跳过, apply_failed 却是空的)。
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


c, nl2 = load(CORE)
c = rep(c, '''                    如果 (cm段.取成员数 () > 6)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行字段过多(" + 到文本 (cm段.取成员数 ()) + " 段, 最多 6): " + cm行 + " | 列位固定为 类型|标签|命令ID|参数|父命令ID|快捷键 —— 修改类的**新标签写第2列**(如 relabel|新名字|26501|1|0|), 快捷键写第6列(如 accel||26501|1|0|70C|)"))
                    }
''', '''                    变量 cm段数 <类型 = 整数>
                    cm段数 = cm段.取成员数 ()
                    如果 (cm段数 == 7 && cm段.取成员 (6) == "")
                    {
                        // 行尾多补一个 | 是常见写法, 按 6 列处理(不算错位)
                        cm段数 = 6
                    }
                    如果 (cm段数 > 6)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行字段过多(" + 到文本 (cm段.取成员数 ()) + " 段, 格式只有 6 列): " + cm行 + " | 列位固定为 类型|标签|命令ID|参数|父命令ID|快捷键 —— 修改类的**新标签写第2列**(如 relabel|新名字|26501|1|0|), 快捷键写第6列(如 accel||26501|1|0|70C|); 若某列留空就写成连续两个 |, 不要在该列填别的内容"))
                    }
''', 'Core 段数校验精修', nl2)
open(CORE, 'wb').write(c.encode('utf-8'))

s, nl = load(SERVER)
s = rep(s, '''                如果 (条目命令ID < 1)
                {
                    菜单上次错误 = "修改类条目需要已存在的命令ID: " + 行文本
                    到循环尾
                }
''', '''                如果 (条目命令ID < 1)
                {
                    菜单上次错误 = "修改类条目需要已存在的命令ID: " + 行文本
                    失败条数 = 失败条数 + 1
                    失败明细 = 失败明细 + "[跳过 " + 条目类型 + ": 命令ID 解析为 " + 到文本 (条目命令ID) + " | 列位: 类型|标签|命令ID|参数|父命令ID|快捷键] "
                    到循环尾
                }
''', '施加侧 命令ID<1 计入失败', nl)

s = rep(s, '''            如果 (目标模型.是否为空 ())
            {
                菜单上次错误 = "父菜单不存在, 跳过: " + 行文本 + " | 第5列是父命令ID(想要顶层项该列为 0 或留空); 列位: 类型|标签|命令ID|参数|父命令ID|快捷键"
                到循环尾
            }
''', '''            如果 (目标模型.是否为空 ())
            {
                菜单上次错误 = "父菜单不存在, 跳过: " + 行文本 + " | 第5列是父命令ID(想要顶层项该列为 0 或留空); 列位: 类型|标签|命令ID|参数|父命令ID|快捷键"
                失败条数 = 失败条数 + 1
                失败明细 = 失败明细 + "[跳过 " + 条目类型 + " " + 到文本 (条目命令ID) + ": 第5列父命令ID=" + 到文本 (条目父ID) + " 指向上方不存在的 sub 行"
                如果 (条目父ID < 26500)
                {
                    失败明细 = 失败明细 + "(该列像是不小心填了别的值: 列位 类型|标签|命令ID|参数|父命令ID|快捷键)"
                }
                失败明细 = 失败明细 + "] "
                到循环尾
            }
''', '施加侧 父菜单跳过计入失败', nl)
open(SERVER, 'wb').write(s.encode('utf-8'))
print('问题: %r' % problems)
sys.exit(1 if problems else 0)
