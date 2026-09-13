# -*- coding: utf-8 -*-
r"""按清理计划 §六 修**扫描口径**(它是度量工具, 不该把契约注释算成"操作备注"):

① `回退`/`静默`/`之前`/`本次` 移出 STRONG —— 实测它们在代码里多是**运行期语义**
   (`回退`=运行期回退分支, `静默`=描述内核行为, `之前`=时序先后, `本次`=运行期序数), 误报 95/247;
② `NOTE_KEEP` 整行排除会**反向漏报**(如 `原实现将id:0误判为通知` 因含"字符"被放过) ->
   改为"STRONG 一律报, 只有 MEDIUM 才受 KEEP 抑制";
③ `=== … ===` 段标题被 MEDIUM 的 `新增/补充` 误判 -> 整类豁免;
④ 补批次词 `第\d+轮` / `上一版`(实测漏 2 条真实叙述)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
src = open(P, 'rb').read().decode('utf-8')
problems = []

OLD_STRONG = '''NOTE_STRONG = re.compile(
    r"修复[:：(]|已修|实测|曾因|曾经|踩坑|踩过|教训|本轮|原实现|原返回|原来|误判|"
    r"假成功|静默|之前|先前|上一轮|本次|现改为|改回|回退|纠正|笔误|漏了")'''
NEW_STRONG = '''# 口径修正(见 报告 §136 与 _audit/_notes_cleanup_plan_r117.md §六):
#   · 移出 `静默|之前|本次|回退` —— 实测它们在代码里多为**运行期语义**
#     (`回退`=运行期回退分支, `静默`=描述内核/被调用方行为, `之前`=时序先后, `本次`=运行期序数),
#     旧口径把 95/247 条契约注释误判成"操作备注"。
#   · 补 `第\\d+轮|上一版`(实测漏报真实叙述)。
NOTE_STRONG = re.compile(
    r"修复[:：(]|已修|实测|曾因|曾经|踩坑|踩过|教训|本轮|原实现|原返回|原来|误判|"
    r"假成功|先前|上一轮|上一版|第\\d+轮|现改为|改回|纠正|笔误|漏了")'''

OLD_CLS = '''                if NOTE_STRONG.search(s) and not NOTE_KEEP.search(s):
                    notes.append((f, i, "STRONG", s[:150]))
                elif NOTE_MEDIUM.search(s) and not NOTE_KEEP.search(s):
                    notes.append((f, i, "MEDIUM", s[:150]))'''
NEW_CLS = '''                # `=== … ===` 是段标题, 不是备注(旧口径被 MEDIUM 的"新增/补充"等词误判)
                是段标题 = bool(re.match(r"//\\s*[=＝\\-—_]{2,}", s)) or ("===" in s and s.count("=") >= 6)
                if 是段标题:
                    pass
                elif NOTE_STRONG.search(s):
                    # STRONG 一律报: 旧口径"KEEP 整行排除"会反向漏报
                    # (实测漏掉 `已修复` 因含"返回"、`原实现靠…回落到默认值` 因含"默认")
                    notes.append((f, i, "STRONG", s[:150]))
                elif NOTE_MEDIUM.search(s) and not NOTE_KEEP.search(s):
                    notes.append((f, i, "MEDIUM", s[:150]))'''

for old, new, tag in ((OLD_STRONG, NEW_STRONG, 'STRONG 口径'), (OLD_CLS, NEW_CLS, '分类逻辑')):
    if src.count(old) != 1:
        problems.append('%s: 锚点命中 %d 次' % (tag, src.count(old)))
        continue
    src = src.replace(old, new, 1)
    print('   ok %s 已改' % tag)

if problems:
    print('!! 未写文件: %r' % problems)
    sys.exit(1)
open(P, 'wb').write(src.encode('utf-8'))
print('扫描口径已更新')
