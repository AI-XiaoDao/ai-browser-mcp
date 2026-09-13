# -*- coding: utf-8 -*-
"""把"证据薄弱"的通过项分类:
  A 类 = 回执里**有 poll_hint**(明确告知要轮询 mcp_result) -> 两步但诚实、可行动
  B 类 = 回执里**没有 poll_hint**, 只有 "CDP已提交:<方法>" -> 调用方**完全不知道**要再调一次(最危险)
  C 类 = 其它(_async 但既非 A 也非 B)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import tool_ledger as TL

d = TL.load()
tools = {t.get("name") for t in TL.tool_list()}

A, B, C = [], [], []
for name, r in sorted(d.items()):
    if name not in tools or r.get("status") != "pass":
        continue
    note = r.get("note") or ""
    if '"_async":true' not in note and 'CDP已提交' not in note:
        continue
    if 'poll_hint' in note:
        A.append(name)
    elif 'CDP已提交' in note:
        B.append((name, note))
    else:
        C.append((name, note))

print("== A 类(有 poll_hint, 已告知要轮询): %d 个 ==" % len(A))
for n in A:
    print("   %s" % n)

print("\n== B 类(无任何提示, 只回 'CDP已提交'): %d 个 ★优先处理 ==" % len(B))
for n, note in B:
    print("   %-38s %s" % (n, note[:110].replace('\n', ' ')))

print("\n== C 类(其它 _async): %d 个 ==" % len(C))
for n, note in C:
    print("   %-38s %s" % (n, note[:110].replace('\n', ' ')))
