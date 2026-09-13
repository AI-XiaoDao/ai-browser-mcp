# -*- coding: utf-8 -*-
r"""在报告 §156.5 末尾加一行**指向 §157 的更正指引**, 避免只读旧章节的读者按已失效的结论行事。

用法: py -3 _audit\_doc_round137_ptr.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
APPLY = '--apply' in sys.argv

ANCHOR = '本轮不新增代码改动，只把上述方案与锚点写入台账（`_audit/_gap_verified.md`），供下一轮直接实施。'
ADD = ('\n\n> **结论更正（第137轮）**：本节 §156.1 的"本会话 JS 通道被打死、只能重启"与 §156.4 的兜底条款\n'
       '> "若 ② 无法达成则保留现状" **均已由第137轮的实测推翻** —— 装上插装后 `execute_js` 实测 **0.99 / 0.96 / 0.97s**\n'
       '> 连续可用（`remove` 0.05s、之后回到 0.02s）。落地细节、量测表与验收见 **§157**；\n'
       '> 本节的"2500ms 首轮预算 + resume 后重试一次"方案在实施中被证伪（重派发会再次命中同一条插装），\n'
       '> 实际生效的是"**resume 后继续等原来那条请求**"。')


def main():
    txt = io.open(REPORT, encoding='utf-8', newline='').read()
    if '结论更正（第137轮）' in txt:
        print('· 已存在指引, 跳过')
        return
    assert txt.count(ANCHOR) == 1, '锚点命中 %d 次' % txt.count(ANCHOR)
    out = txt.replace(ANCHOR, ANCHOR + ADD, 1)
    print('· 已插入指向 §157 的更正指引 (%d -> %d 字符)' % (len(txt), len(out)))
    if APPLY:
        io.open(REPORT, 'w', encoding='utf-8', newline='').write(out)
        print('   ✔ 已写入 MCP工具可用性检测报告.md')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
