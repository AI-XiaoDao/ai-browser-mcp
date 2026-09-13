# -*- coding: utf-8 -*-
r"""把"操作备注"的判定口径钉在**开发过程叙述**上(这才是用户要清的东西)。

上一版把 STRONG 一律上报, 于是 `实测`/`原实现`/`原来` 这类**证据与理由**也被算进来 —— 但项目里这些
注释恰恰是**唯一记录实测结论**的地方(见 `_audit/_notes_cleanup_plan_r117.md` 开头列的 27 条),
清掉等于把踩过的坑重新埋回去。故本轮口径改为:

  操作备注 = 只含"我/上一轮/曾经/修复了"这类**过程口吻**的注释;
  `实测`/`原实现`/`原来`/`先前` -> **移出 STRONG**(它们是"为什么有这条约束"的依据, 应保留)。

保留: 修复[:：(]、已修、曾因、曾经、踩坑、踩过、教训、本轮、上一轮、上一版、第N轮、现改为、改回、
      纠正、笔误、漏了、误判、假成功。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
src = open(P, 'rb').read().decode('utf-8')

OLD = '''NOTE_STRONG = re.compile(
    r"修复[:：(]|已修|实测|曾因|曾经|踩坑|踩过|教训|本轮|原实现|原返回|原来|误判|"
    r"假成功|先前|上一轮|上一版|第\\d+轮|现改为|改回|纠正|笔误|漏了")'''
NEW = '''# 口径(第117/118轮定稿): **只把"开发过程叙述"算作操作备注**。
#   · 移出 `实测|原实现|原返回|原来|先前` —— 它们是"为什么存在这条约束"的**依据**, 且项目里
#     这些注释常常是唯一记录实测结论的地方(清掉=把踩过的坑重新埋回去)。
#   · 移出 `静默|之前|本次|回退` —— 多为运行期语义(见 §136)。
#   · 保留真正带过程口吻的词。
NOTE_STRONG = re.compile(
    r"修复[:：(]|已修|曾因|曾经|踩坑|踩过|教训|本轮|上一轮|上一版|第\\d+轮|"
    r"现改为|改回|纠正|笔误|漏了|误判|假成功")'''
if src.count(OLD) != 1:
    print('!! 锚点命中 %d 次' % src.count(OLD))
    sys.exit(1)
open(P, 'wb').write(src.replace(OLD, NEW, 1).encode('utf-8'))
print('口径已定稿: 只看过程叙述')
