# -*- coding: utf-8 -*-
"""临时仪表: 失败分支到底有没有跑? 菜单失败说明() 到底有没有返回文本?

apply_failed 是"" 有三种可能, 单跑一次就能分开:
  ① 失败分支根本没执行             -> 失败条数 保持 0
  ② 分支执行了但 菜单失败说明() 返回 "" -> 失败条数>0 而 明细只有 [F1][F2] 这种标记
  ③ 分支执行且拼接正常, 只是字段没被写上 -> 明细在 last_error 里有全文, 而 apply_failed 为空
做法: 在明细里加 [F<序号>] 标记, 并把 失败条数+明细 同时写进**另一条已验证能显示的通道** 菜单上次错误。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
text = open(p, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

OLD = '失败明细 = 失败明细 + 菜单失败说明 ('
NEW = '失败明细 = 失败明细 + "[F" + 到文本 (失败条数) + "]" + 菜单失败说明 ('
n = text.count(OLD)
print('失败分支拼接点: %d 处' % n)
if n != 7:
    print('!! 预期 7 处(5 个修改类 + noaccel + 公共快捷键块), 实际 %d' % n)
    sys.exit(1)
text = text.replace(OLD, NEW)

TAIL_OLD = '''        菜单最近项数 = 顶层菜单.取数量 ()
        菜单回读确认条数 = 回读条数
        菜单施加失败 = 失败明细
'''
TAIL_NEW = '''        菜单最近项数 = 顶层菜单.取数量 ()
        菜单回读确认条数 = 回读条数
        菜单施加失败 = 失败明细
        如果 (失败条数 > 0)
        {
            菜单上次错误 = "仪表 失败条数=" + 到文本 (失败条数) + " 明细=[" + 失败明细 + "]"
        }
'''
if text.count(TAIL_OLD) != 1:
    print('!! 收尾锚点命中 %d' % text.count(TAIL_OLD))
    sys.exit(1)
text = text.replace(TAIL_OLD, TAIL_NEW, 1)
open(p, 'wb').write(text.encode('utf-8'))
print('仪表已加入')
