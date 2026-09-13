# -*- coding: utf-8 -*-
"""A1 — 格式与编码合规（已剔除建模错误的检查项，见文末说明）"""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HDR = '<火山程序 类型 = "通常" 版本 = 1 />'
W = []
def w(s=""):
    W.append(s)

w("=" * 100)
w("A1 格式与编码合规检查")
w("依据: 技能书 参考/wsv文件格式.md (规则1-4) + 参考/语法速查.md §3")
w("=" * 100)
w()

summary, detail = [], []
for f in FILES:
    ls, (enc, eol, bom, raw) = lines_of(f)
    _, db, da = brace_map(f)
    body = method_body_set(f)
    issues = []

    # 规则1
    first = next((l for l in ls if l.strip() != ""), "")
    if first.strip() != HDR:
        issues.append(("规则1", "首非空行非标准文档头"))

    # 包: 唯一且为首个成员
    members = member_lines(f)
    pkgs = [(i, l) for i, l in members if re.match(r"\s*包\s+\S+", l)]
    if len(pkgs) != 1:
        issues.append(("包", "包定义 %d 个 (要求 1)" % len(pkgs)))
    elif pkgs[0][0] != members[0][0]:
        issues.append(("包", "包定义非首个成员 (首成员第 %d 行)" % (members[0][0] + 1)))

    # 类: 文档顶层 depth==0
    for i, l in members:
        if re.match(r"\s*类\s+\S+", l) and db[i] != 0:
            issues.append(("类", "第%d行 类定义 depth=%d (要求0)" % (i + 1, db[i])))

    # 方法: 类体内 depth>=1
    for (i0, mname, sig, b0, b1) in find_methods(f):
        if db[i0] < 1:
            issues.append(("方法", "第%d行 方法[%s] 位于文档顶层" % (i0 + 1, mname)))

    # 方法体内禁止 '#'
    for k in sorted(body):
        if classify(ls[k]) == "HASH":
            issues.append(("注释", "第%d行 方法体内出现 '#' 行" % (k + 1)))

    # 方法体外禁止 '//'
    for i, l in members:
        if l.strip().startswith("//"):
            issues.append(("注释", "第%d行 顶层/类级出现 '//' 注释行" % (i + 1)))

    # 语句行以 '<' 开头须有 '<>'
    for k in sorted(body):
        s = ls[k].strip()
        if classify(ls[k]) == "CODE" and s.startswith("<") and not s.startswith("<>"):
            issues.append(("语句行", "第%d行 以 '<' 开头却无 '<>' 前缀" % (k + 1)))

    # 花括号平衡
    if da and da[-1] != 0:
        issues.append(("括号", "末行 depth=%d (要求0)" % da[-1]))
    neg = [i + 1 for i, d in enumerate(da) if d < 0]
    if neg:
        issues.append(("括号", "提前闭合于行 %s" % neg[:5]))

    # 非法控制字符
    ctl = re.findall(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", raw)
    if ctl:
        issues.append(("编码", "含 %d 个非法控制字符" % len(ctl)))

    summary.append((f, enc, eol, bom or "无", len(ls), da[-1] if da else 0, len(issues)))
    for cat, msg in issues:
        detail.append("[%s][%s] %s" % (f, cat, msg))

w("%-24s %-9s %-6s %-6s %7s %7s %6s" % ("文件", "编码", "行尾", "BOM", "行数", "末depth", "问题"))
w("-" * 100)
for r in summary:
    w("%-24s %-9s %-6s %-6s %7d %7d %6d" % r)
w()
w("总计问题: %d" % len(detail))
if detail:
    w()
    for d in detail:
        w("  " + d)
else:
    w()
    w(">>> 结构/编码层面: 16/16 文件零违规")
w()
w("--- 行尾一致性 (LOW: 非 CRLF 会导致 IDE 保存时产生全文件 diff) ---")
n_none = 0
for f in FILES:
    _, _, eol, _, _ = read_wsv(f)
    if eol != "CRLF":
        w("  %-24s %s" % (f, eol)); n_none += 1
if n_none == 0:
    w("  全部 CRLF")

w()
w("--- 已剔除的检查项 (建模错误，避免误报) ---")
w("  x  '语句行以 包/类/方法/参数/常量/变量 开头须有 <>'")
w("     理由: wsv格式规则中『变量/常量』可合法位于『方法子语句体(局部变量)』，")
w("     此时它们是成员定义行而非语句行，IDE 本身即不带 <> 前缀。")
w("     前任审计报告 §1.1 亦称该项 0 处违规，与本次实测一致。")

p = out_report("report_A1.txt", "\n".join(W))
print("written", p, "| total issues:", len(detail))
