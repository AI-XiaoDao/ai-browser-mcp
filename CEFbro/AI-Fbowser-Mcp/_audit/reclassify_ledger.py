# -*- coding: utf-8 -*-
"""用修好的分类器重算台账里已有失败项的类别, 并**逐条打印变化**(可复核)。

为什么要做: 旧的 `prereq_of` 会把失败文案尾部的提示段("注意 iframe 内元素需先切换框架")
当成"缺前置", 于是 7 个 `browser_fill_*` 的**目标不存在**失败被记成 PREREQ,
让本目标最核心的指标"前置缺失类失败数"虚高。分类错了, 后续所有优化方向都会被带偏。

原则: 只改**类别**, 不改任何 note/status; 且每条变化都打印 (旧类别 -> 新类别 + 命中依据),
便于人工复核"这次重分类是纠错还是掩盖问题"。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM

LEDGER = os.path.join(HERE, "_tool_ledger.json")
d = json.load(io.open(LEDGER, encoding="utf-8"))

changed = []
for k, v in sorted(d.items()):
    if not (v.get("status") or "").startswith("fail"):
        continue
    note = v.get("note") or ""
    old = v.get("kind", "")
    new, why = CM.prereq_of(note)
    if new != old:
        changed.append((k, old, new, why, note))

print("失败项共 %d, 类别发生变化 %d 条\n" % (
    len([1 for v in d.values() if (v.get("status") or "").startswith("fail")]), len(changed)))
for k, old, new, why, note in changed:
    print("%-38s %-10s -> %-10s  依据=%s" % (k, old, new, why))
    print("     原文: %s" % note[:150])

# 打印受影响工具的 note 里"提示段"剥掉后的对照, 证明是纠错而非掩饰
print("\n== 剥掉提示段前后的分类对照(仅列变化的) ==")
for k, old, new, why, note in changed:
    core = CM.strip_hints(note)
    print("  %-36s" % k)
    print("     全量文案分类: %s" % CM.prereq_of(note)[0])
    print("     去掉提示段:   %s   (核心原因: %s)" % (CM.prereq_of(core)[0], core[:90]))

if "--write" not in sys.argv:
    print("\n(未写入; 加 --write 落盘)")
    sys.exit(0)

for k, old, new, why, note in changed:
    d[k]["kind"] = new
    d[k]["kind_reclassified_from"] = old
    d[k]["kind_reason"] = why
json.dump(d, io.open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已写回 %d 条类别变化" % len(changed))

from collections import Counter
bad = [v for v in d.values() if (v.get("status") or "").startswith("fail")]
print("新的失败性质分布:", dict(Counter(v.get("kind", "") for v in bad)))
