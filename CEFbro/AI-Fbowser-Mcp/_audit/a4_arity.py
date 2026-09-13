# -*- coding: utf-8 -*-
r"""A4 — 类库 API 调用元数(arity)核对

依据: 技能书 资料/类库/FBrowser浏览器/*.wsv (类库源码 = 一手契约)
方法:
  1) 解析类库全部 方法 的定义行 + 紧随的 参数 行 -> {方法名: (总参数数, 必填参数数)}
  2) 在项目 .wsv 中找形如 `X.方法名 (实参)` / `方法名 (实参)` 的调用
  3) 顶层逗号切分实参(括号/字符串感知) 得到实参个数
  4) 实参 > 总参数  => 确定性错误;  实参 < 必填 => 可疑(可能用到默认值或实参跨行)
"""
import sys, os, re, io, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SKILL = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
W = []
def w(s=""):
    W.append(s)


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


def split_top(s):
    """顶层逗号切分, 括号与字符串感知"""
    out, depth, cur, instr = [], 0, [], False
    i = 0
    while i < len(s):
        c = s[i]
        if instr:
            cur.append(c)
            if c == "\\":
                if i + 1 < len(s):
                    cur.append(s[i + 1]); i += 2; continue
            elif c == '"':
                instr = False
            i += 1; continue
        if c == '"':
            instr = True; cur.append(c); i += 1; continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            out.append("".join(cur).strip()); cur = []; i += 1; continue
        cur.append(c); i += 1
    tail = "".join(cur).strip()
    if tail or out:
        out.append(tail)
    return [x for x in out if x != ""]


# ---------- 1. 解析类库签名 ----------
sig = collections.defaultdict(lambda: [(0, 0)])
nfiles = 0
for fn in sorted(os.listdir(SKILL)):
    if not fn.endswith(".wsv"):
        continue
    nfiles += 1
    ls = read(os.path.join(SKILL, fn)).split("\n")
    i = 0
    while i < len(ls):
        m = re.match(r"\s*方法\s+(\S+)", ls[i])
        if not m or ls[i].lstrip().startswith("#"):
            i += 1; continue
        name = m.group(1)
        # 合并跨行属性表
        merged = ls[i]; j = i + 1
        while j < len(ls) and ">" not in merged:
            merged += ls[j]; j += 1
        total = 0; required = 0
        k = j
        while k < len(ls) and re.match(r"\s*参数\s+\S+", ls[k]):
            pm = ls[k]; kk = k + 1
            while kk < len(ls) and ">" not in pm and re.match(r"\s+\S", ls[kk]) and not re.match(r"\s*参数\s", ls[kk]):
                pm += ls[kk]; kk += 1
            total += 1
            if "@默认值" not in pm:
                required += 1
            k = kk
        if total > 0 or True:
            sig[name].append((total, required))
        i = max(k, i + 1)

w("=" * 100)
w("A4 类库 API 调用元数核对")
w("=" * 100)
w()
w("类库源文件 %d 个, 解析出方法签名 %d 个" % (nfiles, len(sig)))

# 只保留"唯一参数个数"的签名 (同名方法在多个类中参数数可能不同)
uniq = {k: v for k, v in sig.items() if v}
print("  签名条目:", sum(len(v) for v in uniq.values()))

# ---------- 2+3. 扫描调用 ----------
CALL = re.compile(r"(?:([A-Za-z0-9_\u4e00-\u9fff]+)\.)?([A-Za-z0-9_\u4e00-\u9fff]+)\s*\(")
over, under, checked = [], [], 0
for f in FILES:
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        if classify(ln) == "EMBED":
            continue
        code = re.sub(r"//.*$", "", ln)
        for m in CALL.finditer(code):
            obj, fn = m.group(1), m.group(2)
            if fn not in uniq:
                continue
            # 取实参文本
            start = m.end() - 1
            depth, j, instr = 0, start, False
            while j < len(code):
                c = code[j]
                if instr:
                    if c == "\\":
                        j += 2; continue
                    if c == '"':
                        instr = False
                else:
                    if c == '"':
                        instr = True
                    elif c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                        if depth == 0:
                            break
                j += 1
            if j >= len(code):
                continue          # 跨行调用, 跳过
            args = split_top(code[start + 1:j])
            n = len(args)
            cands = uniq[fn]
            maxt = max(t for t, r in cands)
            minr = min(r for t, r in cands)
            checked += 1
            if n > maxt:
                over.append((f, i + 1, fn, n, maxt, code.strip()[:110]))
            elif n < minr:
                under.append((f, i + 1, fn, n, minr, code.strip()[:110]))

w()
w("扫描到类库方法调用点 %d 个" % checked)
w()
w("--- [确定性错误] 实参个数 > 类库最大形参个数 ---  共 %d" % len(over))
for (f, l, fn, n, mx, t) in over[:40]:
    w("   %-26s:%-6d %-28s 实参%d > 形参%d" % (f, l, fn, n, mx))
    w("        %s" % t)
w()
w("--- [提示] 实参个数 < 类库最小必填个数 (可能用到默认值/跨行) ---  共 %d" % len(under))
for (f, l, fn, n, mn, t) in under[:25]:
    w("   %-26s:%-6d %-28s 实参%d < 必填%d" % (f, l, fn, n, mn))
    w("        %s" % t)

p = out_report("report_A4_arity.txt", "\n".join(W))
print("written", p)
print("调用点 %d | 确定性错误 %d | 可疑 %d" % (checked, len(over), len(under)))
