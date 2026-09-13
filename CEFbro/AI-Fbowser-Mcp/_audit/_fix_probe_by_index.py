# -*- coding: utf-8 -*-
r"""修台账探针: `browser_by_index` 复测记 fail, 回包原文「序号 10 没有对应浏览器(当前共 1 个)」
—— 那是**探针造了越界序号**(通用整数兜底 10)撞上工具自己的越界守卫, 属探针假失败而非产品缺陷。
按 mass_probe 既有做法补一个运行期合法小整数(0)。
用法: py -3 _audit\_fix_probe_by_index.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, '_audit', 'mass_probe.py')
APPLY = '--apply' in sys.argv

ANCHOR = '''    "browser_collect": {"action": "get"},        # 只读: 取当前各族监控开关状态'''
NEW = ANCHOR + '''
    # 序号类: 通用整数兜底给的是 10, 而测试实例通常只有 1 个浏览器 ⇒ 撞上工具自己的越界守卫。
    # 给 0(第一个浏览器)才是"打到实现"的调用; 越界行为另由 verify_round141.py 专门验证。
    "browser_by_index": {"index": 0},'''


def main():
    txt = io.open(PROBE, encoding='utf-8', newline='').read()
    if 'browser_by_index": {"index": 0}' in txt:
        print('· 已应用过, 跳过')
        return
    assert txt.count(ANCHOR) == 1, '锚点命中 %d 次' % txt.count(ANCHOR)
    txt = txt.replace(ANCHOR, NEW, 1)
    print('· 已给 browser_by_index 补 index=0')
    if APPLY:
        io.open(PROBE, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 mass_probe.py')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
