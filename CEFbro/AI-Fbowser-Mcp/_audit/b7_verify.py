# -*- coding: utf-8 -*-
"""B7 — 英文输出名写入后最终校验"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))

print("=" * 104)
print("B7 写入后最终校验")
print("=" * 104)
print()
print("%-26s %-8s %-6s %-6s %6s %6s %6s %6s %7s" %
      ("文件", "编码", "行尾", "BOM", "类", "方法", "变量", "参数", "强制输出"))
print("-" * 104)
tot = collections.Counter()
for f in FILES:
    text, enc, eol, bom, raw = read_wsv(f)
    n_cls = len(re.findall(r"^\s*类\s+\S+.*@输出名", text, re.M))
    n_m = len(re.findall(r"^\s*方法\s+\S+.*@输出名", text, re.M))
    n_v = len(re.findall(r"^\s*(?:变量|常量)\s+\S+.*@输出名", text, re.M))
    n_p = len(re.findall(r"^\s*参数\s+\S+.*@输出名", text, re.M))
    n_force = text.count("@强制输出")
    for k, v in (("c", n_cls), ("m", n_m), ("v", n_v), ("p", n_p), ("f", n_force)):
        tot[k] += v
    print("%-26s %-8s %-6s %-6s %6d %6d %6d %6d %7d" %
          (f, enc, eol, bom or "无", n_cls, n_m, n_v, n_p, n_force))
print("-" * 104)
print("%-26s %-8s %-6s %-6s %6d %6d %6d %6d %7d" %
      ("合计", "", "", "", tot["c"], tot["m"], tot["v"], tot["p"], tot["f"]))

print()
print("--- 健全性校验 ---")
bad = collections.Counter()
for f in FILES:
    text, enc, eol, bom, raw = read_wsv(f)
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        if ln.count("@输出名") > 1:
            bad["同行重复@输出名"] += 1
        if "@输出名" in ln and classify(ln) != "CODE":
            bad["出现在非CODE行"] += 1
    for m in re.finditer(r'@输出名\s*=\s*"([^"]*)"', text):
        v = m.group(1)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", v):
            bad["非法C++标识符:" + v] += 1
    if enc != "utf-8":
        bad["编码非UTF-8"] += 1
    if "@输出名" in text and eol not in ("CRLF", "LF"):
        bad["行尾异常"] += 1
    if b"\xef\xbb\xbf" in raw[:3]:
        bad["出现BOM"] += 1
if bad:
    for k, v in bad.items():
        print("   !! %s : %d" % (k, v))
else:
    print("   全部通过: 无同行重复 / 无非法标识符 / 编码与行尾保持 / 无BOM")

print()
print("--- 虚拟覆盖保护校验 (应无 @输出名) ---")
n_virt = n_virt_tagged = 0
for f in FILES:
    ls, _, da = brace_map(f)
    cls = None
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        c = strip_strings_and_comment(ln)[0]
        m = re.match(r"\s*类\s+(\S+)", c)
        if m:
            cls = m.group(1); continue
        mm = re.match(r"\s*方法\s+(\S+)", c)
        if not mm or cls is None:
            continue
        merged = ln
        j = i + 1
        while j < len(ls) and ">" not in merged:
            merged += ls[j]; j += 1
        if "@虚拟方法" in merged:
            n_virt += 1
            if "@输出名" in merged:
                n_virt_tagged += 1
                print("   !! %s:%d %s.%s 竟被加了 @输出名" % (f, i + 1, cls, mm.group(1)))
print("   虚拟覆盖方法总数 %d, 其中被误加 @输出名 %d" % (n_virt, n_virt_tagged))

print()
print("--- 结构复检 ---")
bad2 = 0
for f in FILES:
    _, _, da = brace_map(f)
    if da and da[-1] != 0:
        print("   !! %s 末 depth=%d" % (f, da[-1])); bad2 += 1
print("   花括号不平衡文件数: %d" % bad2)
