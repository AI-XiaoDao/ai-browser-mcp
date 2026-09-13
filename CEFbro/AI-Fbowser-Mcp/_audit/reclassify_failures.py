# -*- coding: utf-8 -*-
"""用修正后的分类器**重新归类**台账里已记录的失败项(不改动它们的原始 note)。

背景: 台账 store 里存的是 classify() 当时算出的 kind。分类器补了规则后, 旧记录不会自动更新,
于是"失败性质"统计仍显示过时的 OTHER。本脚本按**同一条 note**重算 kind 并就地更新,
只动 kind/why 两个字段, 原始 note/args/status 一律不动 —— 保证证据链可追溯。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import tool_ledger as TL
import cold_matrix as CM

d = TL.load()
changed = []
kept = []
for name, r in d.items():
    if r.get("status") != "fail":
        continue
    note = r.get("note") or ""
    kind, why = CM.prereq_of(note)
    old = r.get("kind")
    if kind != old:
        r["kind"] = kind
        r["why"] = why
        r["kind_reclassified"] = "第98轮: 分类器补充内核对'目标资源不存在'的原话后重算"
        changed.append((name, old, kind, why))
    else:
        kept.append((name, kind))

print("== 重算后发生变化的失败项 ==")
for name, old, new, why in changed:
    print("   %-34s %-10s -> %-10s (%s)" % (name, old, new, why))
print("\n== 未变化 ==")
for name, kind in kept:
    print("   %-34s %s" % (name, kind))

if changed:
    TL.save(d)
    print("\n已写回台账(仅 kind/why 字段)")
else:
    print("\n无变化, 未写回")
