# -*- coding: utf-8 -*-
r"""补记: 本轮还修了台账探针的两处"缺参假失败"(§160.5)。
用法: py -3 _audit\_doc_round140b.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
APPLY = '--apply' in sys.argv

GAP_TEXT = '''
### §160.5 顺带修掉两处"探针缺参假失败"（不是产品缺陷）

复测事件族工具时 `browser_collect` / `browser_network` 记成 fail，回包原文分别是
`未知action:  | 支持: …` 与 `action 不能省略 | 可用: list(查询, 不改开关) / …`，且 `args={}` ——
即**探针没传 action**，撞上了工具自己的缺参守卫（那测的是守卫，不是实现）。
按 `mass_probe.py` 里 `TOOL_ARG_OVERRIDES` 表头写明的既有做法，补两个**只读且无害**的值：
`browser_collect{action:"get"}`、`browser_network{action:"list"}`。复测双双 **pass**，台账回到 **324/324**。
'''

REPORT_TEXT = '''
### 160.5 顺带修掉两处"探针缺参假失败"

复测事件族时 `browser_collect` / `browser_network` 一度记成 fail（回包是缺参守卫文案、`args={}`）——
根因是**探针没传 action**，属测量缺陷而非产品缺陷。按 `mass_probe.py` 既有做法补只读 action
（`get` / `list`）后复测双双 pass，台账 324/324。
'''


def main():
    for path, text, mark, tag in [(GAP, GAP_TEXT, '### §160.5', '§160.5'),
                                  (REPORT, REPORT_TEXT, '### 160.5', '160.5')]:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if mark in txt:
            print('· %s —— 已存在, 跳过' % tag)
            continue
        out = txt.rstrip('\n') + '\n' + text
        print('· %s: %d -> %d 字符' % (tag, len(txt), len(out)))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(out)
    print('   ✔ 已写入' if APPLY else '(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
