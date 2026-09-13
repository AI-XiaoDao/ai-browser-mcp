# -*- coding: utf-8 -*-
r"""修台账探针: 给 `browser_collect` / `browser_network` 补上**只读 action**, 让复测打到实现而不是守卫。

## 现象(本轮复测)
  browser_collect  fail 0.01s 未知action:  | 支持: network_enable/…/get/clear, …
  browser_network  fail 0.02s action 不能省略 | 可用: list(查询, 不改开关) / …
两者 args={} —— 探针**没传 action**, 撞上工具自己的缺参守卫。这与 `mass_probe.py` 里
`TOOL_ARG_OVERRIDES` 表头写明的已知情形完全一致:「工具把关键入参声明成**可选** ⇒ 探针传空参
撞上守卫 ⇒ 记成失败 —— 那测的是守卫, 不是实现」。故按既有做法补两个**只读且无害**的值。

用法: py -3 _audit\_fix_probe_collect_network.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, '_audit', 'mass_probe.py')
APPLY = '--apply' in sys.argv

ANCHOR = '''    "browser_kernel_download": {"action": "list"},                 # 只列进行中的下载, 不发起下载'''
NEW = ANCHOR + '''
    # 读类 action(无副作用): 这两者把 action 声明成了可选, 但实现里"省略 action"是**刻意拒绝**
    # (browser_network 原文: 省略会隐式启用网络日志, 故拒绝) ⇒ 不补就只测到守卫。
    "browser_collect": {"action": "get"},        # 只读: 取当前各族监控开关状态
    "browser_network": {"action": "list"},       # 只读: 列出已记录的网络请求, 不改开关'''


def main():
    txt = io.open(PROBE, encoding='utf-8', newline='').read()
    if 'browser_collect": {"action": "get"}' in txt:
        print('· 已应用过, 跳过')
        return
    assert txt.count(ANCHOR) == 1, '锚点命中 %d 次' % txt.count(ANCHOR)
    txt = txt.replace(ANCHOR, NEW, 1)
    print('· 已给 browser_collect / browser_network 补只读 action')
    if APPLY:
        io.open(PROBE, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 mass_probe.py')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
