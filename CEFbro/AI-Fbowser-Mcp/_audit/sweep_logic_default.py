# -*- coding: utf-8 -*-
"""统计"可能受同一缺陷影响"的读取点: `yyjson取逻辑_默认 (参数JSON, "键", 假)`。

## 为什么要统计
本轮定死了一个真缺陷: `browser_debugger_wait_paused` 里
`清除旧 = yyjson取逻辑_默认 (参数JSON, "fresh", 假)` 在 **fresh 键不存在**时没有回落到默认值,
导致每次调用都把"正要等的那个暂停事件"清掉 → 工具永远报"等超时"。
若 `yyjson取逻辑_默认` 对**缺失键**的回落真的不生效, 那么所有"默认值=假"的调用点都会**被当成真**,
这是**系统性**问题(例如 enabled/disable 之类开关会被静默反转)。

本脚本只做**静态统计与清单**(候选, 不是结论) —— 逐个真机验证由后续轮次串行做。
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

PAT_FALSE = re.compile(r'yyjson取逻辑_默认 \(参数JSON, "([a-z_0-9]+)", 假\)')
PAT_TRUE = re.compile(r'yyjson取逻辑_默认 \(参数JSON, "([a-z_0-9]+)", 真\)')
# 其他对象上的同类调用(不限于 参数JSON), 也一并列出以便判断影响面
PAT_ANY_FALSE = re.compile(r'yyjson取逻辑_默认 \(([^,()]+), "([a-z_0-9]+)", 假\)')

tot_f = tot_t = 0
detail = []
for p in sorted(glob.glob(os.path.join(ROOT, "src", "*.wsv"))):
    if "~vbak" in p:
        continue
    s = io.open(p, encoding="utf-8").read()
    a = PAT_FALSE.findall(s)
    b = PAT_TRUE.findall(s)
    if a or b:
        detail.append((os.path.basename(p), a, b))
        tot_f += len(a)
        tot_t += len(b)

print("== 按文件: `yyjson取逻辑_默认 (参数JSON, 键, 默认)` 的默认值分布 ==")
for name, a, b in detail:
    print("  %-28s 默认假 %2d 处 | 默认真 %2d 处" % (name, len(a), len(b)))
    if a:
        print("        默认假(风险: 缺失键时若被当成真, 行为会反转): %s" % ", ".join(sorted(set(a))))
print("\n合计: 默认假 %d 处 | 默认真 %d 处" % (tot_f, tot_t))

print("\n== 全仓(不限 参数JSON) 默认值为假的调用点 ==")
n = 0
for p in sorted(glob.glob(os.path.join(ROOT, "src", "*.wsv"))):
    if "~vbak" in p:
        continue
    s = io.open(p, encoding="utf-8").read()
    hits = PAT_ANY_FALSE.findall(s)
    for obj, key in hits:
        n += 1
        if n <= 40:
            print("  %-28s %-24s %s" % (os.path.basename(p), obj.strip()[:22], key))
print("  ... 共 %d 处" % n)

print("\n说明: 以上是**候选清单**, 不是结论。判定某处是否真受影响, 需要")
print("      ① 真机调用该工具并观察与实际参数不符的行为; 或")
print("      ② 一个直接测 `yyjson取逻辑_默认` 缺键回落行为的最小工具/探针。")
