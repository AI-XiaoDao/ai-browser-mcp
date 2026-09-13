# -*- coding: utf-8 -*-
"""列出台账里"证据薄弱"的通过项 —— 回包只是 _async 回执(证明"已提交", 不证明"已生效")。

依据(第98轮已实证的机制): 不在 应同步等待 白名单、自己也不 同步等待异步任务 的工具,
只能拿到 {"_async":true,"message":"CDP已提交:<方法>"}。对这类工具, 台账的 pass **只说明命令发出去了**,
至于内核是否接受、功能是否真的生效, 都没有证据 —— 正是"静默假成功"的温床。
本脚本把它们挑出来, 供逐个做**回读验证**(read-back)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import tool_ledger as TL

d = TL.load()
tools = {t.get("name") for t in TL.tool_list()}

weak = []
for name, r in d.items():
    if name not in tools:
        continue
    note = r.get("note") or ""
    if r.get("status") != "pass":
        continue
    if '"_async":true' in note or 'CDP已提交' in note:
        weak.append((name, r.get("round"), note))

print("== 证据薄弱(仅异步回执)的通过项: %d 个 ==" % len(weak))
for name, rnd, note in sorted(weak):
    print("\n   %-38s (第 %s 轮)" % (name, rnd))
    print("      %s" % note[:220])
