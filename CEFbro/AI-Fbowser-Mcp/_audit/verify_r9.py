# -*- coding: utf-8 -*-
"""Round 8 核对: 4 个"永不生效参数"已从 schema 移除 + 描述同步更新 + 结构未破坏。"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import SRC
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = os.path.join(SRC, "MCP_Server.wsv")
lines = io.open(P, encoding="utf-8").read().split("\n")


def find_line(sub):
    for i, l in enumerate(lines):
        if sub in l:
            return i + 1, l
    return None, None


CASES = [
    # (说明, 定位串, 必须不存在, 必须存在)
    # 第(后续)轮语义反转: brands 已被后续轮次**重新纳入** UA 参数(与本轮无关, 此处如实反转断言)
    ("browser_fingerprint_ua 现已含 brands(后续轮次重新纳入)",
     '添加工具JSON ("browser_fingerprint_ua"', '__NONE__', '"brands"'),
    # enable 参数仍在, 但类型说明由 boolean 改成"字符串 true/false 显式表态"(后续轮次变更)
    ("browser_vip_enable_inspector 的 enable 参数仍在(类型说明已改)",
     '添加工具JSON ("browser_vip_enable_inspector"', '__NONE__', '"enable"'),
    # 第121轮语义反转: devices 从"永不生效的空参数"变成**真参数**(type=1/2 必填), 故本 case 随之反转。
    ("browser_vip_fingerprint_media_devices 现已支持 devices(真参数, required 含 type)",
     '添加工具JSON ("browser_vip_fingerprint_media_devices"', '__NONE__',
     '"devices", "text"'),
    ("browser_intercept 已移除 match_mode",
     '添加工具JSON ("browser_intercept"', 'match_mode', '"action", "text"'),
    ("browser_intercept 描述已补充『无正则模式』",
     '添加工具JSON ("browser_intercept"', '__NONE__', '无正则模式'),
]
ok = 0
for tag, anchor, must_absent, must_present in CASES:
    ln, l = find_line(anchor)
    if ln is None:
        print("  !!  %-46s 未找到注册行" % tag)
        continue
    absent = (must_absent == "__NONE__") or (must_absent not in l)
    present = must_present in l
    good = absent and present
    ok += good
    print("  %s%-46s L%d  移除=%s 保留=%s" % ("OK " if good else "!! ", tag, ln,
                                              "是" if absent else "否",
                                              "是" if present else "否"))
print()
print("通过 %d / %d" % (ok, len(CASES)))

print()
print("=" * 100)
print("引号词法复检 (被改动的 4 行)")
print("=" * 100)


def scan(line):
    i, in_str, n, bad = 0, False, 0, False
    while i < len(line):
        c = line[i]
        if in_str:
            if c == "\\":
                i += 2; continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
        i += 1
    return not in_str


names = ["browser_fingerprint_ua", "browser_vip_enable_inspector",
         "browser_vip_fingerprint_media_devices", "browser_intercept"]
for nm in names:
    ln, l = find_line('添加工具JSON ("%s"' % nm)
    if ln:
        print("  %s L%-6d %-40s %s" % ("OK " if scan(l) else "!! ", ln, nm,
                                       "字符串闭合" if scan(l) else "!! 未闭合"))
