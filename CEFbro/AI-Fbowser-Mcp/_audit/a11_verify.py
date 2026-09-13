# -*- coding: utf-8 -*-
"""A11 — 写入后校验: 编码/行尾/结构/属性位置/幂等性"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

print("=" * 96)
print("A11 写入后校验")
print("=" * 96)
print()
tot_out = tot_force = 0
print("%-26s %-8s %-6s %-6s %8s %8s %8s" % ("文件", "编码", "行尾", "BOM", "输出名", "强制输出", "行数"))
print("-" * 96)
for f in FILES:
    text, enc, eol, bom, raw = read_wsv(f)
    n_out = text.count("@输出名")
    n_force = text.count("@强制输出")
    tot_out += n_out; tot_force += n_force
    print("%-26s %-8s %-6s %-6s %8d %8d %8d" % (f, enc, eol, bom or "无", n_out, n_force, text.count("\n")))
print("-" * 96)
print("%-26s %-8s %-6s %-6s %8d %8d" % ("合计", "", "", "", tot_out, tot_force))

print()
print("--- 关键校验 ---")
# 1) 每个 @输出名 都在属性表内 (即 <> 之间)
bad_pos = []
for f in FILES:
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        if "@输出名" not in ln:
            continue
        if classify(ln) != "CODE":
            bad_pos.append((f, i + 1, "出现在非 CODE 行")); continue
        # 属性表闭合 '>' 必须在同一行或后续行; 同行为简化检查: '<' 在 '>' 之前
        p_in = ln.find("<"); p_gt = ln.find(">")
        if p_in >= 0 and (p_gt < 0 or p_gt < p_in):
            bad_pos.append((f, i + 1, "'<' / '>' 顺序异常"))
print("  属性表内位置异常: %d 处" % len(bad_pos))
for b in bad_pos[:10]:
    print("    %s:%d %s" % b)

# 2) 幂等: 无重复 @输出名
dup = []
for f in FILES:
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        if ln.count("@输出名") > 1:
            dup.append((f, i + 1, ln.count("@输出名")))
print("  同一行重复 @输出名: %d 处" % len(dup))

# 3) 语法: @输出名 值必须是引号字符串
badval = []
for f in FILES:
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        for m in re.finditer(r'@输出名\s*=\s*(\S+)', ln):
            if not m.group(1).startswith('"'):
                badval.append((f, i + 1, m.group(1)[:30]))
print("  @输出名 值非引号字符串: %d 处" % len(badval))

# 4) 值是否为合法 C++ 标识符
badid = []
for f in FILES:
    text, _, _, _, _ = read_wsv(f)
    for m in re.finditer(r'@输出名\s*=\s*"([^"]*)"', text):
        v = m.group(1)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", v):
            badid.append((f, v))
print("  @输出名 值非合法 C++ 标识符: %d 处" % len(badid))
for b in badid[:10]:
    print("    %s -> %s" % b)

# 5) 方法定义数 vs @输出名 数 (应基本一致; 差值=跳过项)
print()
print("  方法定义总数 vs @输出名 数:")
tot_m = 0
for f in FILES:
    ms = find_methods(f)
    tot_m += len(ms)
print("    方法定义 %d 个, @输出名 %d 条, 差值 %d (含 main.wsv 保护跳过 + 含未收录字跳过)"
      % (tot_m, tot_out, tot_m - tot_out))

# 6) 结构复检
print()
print("  花括号平衡复检:")
bad = 0
for f in FILES:
    _, _, da = brace_map(f)
    if da and da[-1] != 0:
        print("    !! %s 末 depth=%d" % (f, da[-1])); bad += 1
print("    不平衡文件数: %d" % bad)
