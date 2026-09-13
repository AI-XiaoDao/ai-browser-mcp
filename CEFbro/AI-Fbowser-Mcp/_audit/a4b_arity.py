# -*- coding: utf-8 -*-
r"""A4b — 类型感知的类库 API 元数核对

修正 A4 的致命缺陷: 首版按**裸方法名**匹配, 导致跨类/跨模块同名冲突
  例: `配置解析.取文本 ("port")` —— 取文本 是 yyJSON 类的方法(1参),
       却撞上 FBrowser 里某个 0 参的同名方法 -> 误报 62 条
  例: `选择 (条件, 真值, 假值)` —— 核心库全局方法(3参), 同样撞名

本版做法:
  1) 解析 FBrowser 类库 -> {类名: {方法名: (总参数, 必填参数)}}
  2) 在项目每个方法体内建 局部变量 -> 类型 映射 (变量 X <类型 = T>)
  3) 仅检查**接收者类型确实是 FBrowser 类**的调用 X.方法(实参)
  4) 另检查静态调用 类名前缀 形式 (如 FBrowser_浏览器_取数量 (...))
"""
import sys, os, re, io, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SKILL = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库"
W = []
def w(s=""):
    W.append(s)


def brace_map_text(text):
    """通用: 返回 (lines, depth_before[]) —— 跳过 @ / # 行"""
    ls = text.split("\n")
    db, d = [], 0
    for ln in ls:
        db.append(d)
        s = ln.strip()
        if s[:1] in ("@", "#") or s == "":
            continue
        clean, _ = strip_strings_and_comment(ln)
        d += clean.count("{") - clean.count("}")
    return ls, db


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


# ---------- 1. 解析 FBrowser 类库: 类 -> 方法 -> 参数数 ----------
FB = collections.defaultdict(dict)
cls_names = set()
for mod in ("FBrowser浏览器",):
    d = os.path.join(SKILL, mod)
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".wsv"):
            continue
        ls, db = brace_map_text(io.open(os.path.join(d, fn), encoding="utf-8",
                                        errors="replace").read())
        cur = None
        curdepth = None
        for i, ln in enumerate(ls):
            if ln.strip().startswith(("#", "@")):
                continue
            m = re.match(r"\s*类\s+(\S+)", ln)
            if m:
                cur = m.group(1); cls_names.add(cur); curdepth = db[i]
                continue
            if cur is None or curdepth is None:
                continue
            if db[i] != curdepth + 1:      # 只在类体直属层取方法
                continue
            mm = re.match(r"\s*方法\s+(\S+)", ln)
            if not mm:
                continue
            name = mm.group(1)
            total = required = 0
            # 先跳过跨行的属性表 (到含 '>' 的那一行为止), 再数参数行
            k = i
            merged = ls[i]
            while k < len(ls) and ">" not in merged:
                k += 1
                if k < len(ls):
                    merged += ls[k]
            k += 1
            while k < len(ls) and re.match(r"\s*参数\s+\S+", ls[k]):
                pm = ls[k]; kk = k + 1
                while kk < len(ls) and ">" not in pm and not re.match(r"\s*(参数|方法|变量|常量|类)\s", ls[kk]):
                    pm += ls[kk]; kk += 1
                total += 1
                if "@默认值" not in pm:
                    required += 1
                k = kk
            FB[cur][name] = (total, required)

w("=" * 100)
w("A4b 类型感知的类库 API 元数核对")
w("=" * 100)
w()
w("FBrowser / FBrowserVIP 类库: %d 个类, %d 个方法签名"
  % (len(FB), sum(len(v) for v in FB.values())))

# ---------- 2+3. 逐方法体推断类型并核对 ----------
CALL = re.compile(r"([A-Za-z0-9_\u4e00-\u9fff]+)\s*\.\s*([A-Za-z0-9_\u4e00-\u9fff]+)\s*\(")
VAR = re.compile(r"\s*变量\s+(\S+)\s*<[^>]*类型\s*=\s*([A-Za-z0-9_\u4e00-\u9fff]+)")
over, checked, skipped_untyped = [], 0, 0
for f in FILES:
    for (i0, mname, sig, b0, b1) in find_methods(f):
        ls, _ = lines_of(f)
        vtype = {}
        for k in range(b0, b1 + 1):
            vm = VAR.match(ls[k])
            if vm:
                vtype[vm.group(1)] = vm.group(2)
        for k in range(b0, b1 + 1):
            if classify(ls[k]) == "EMBED":
                continue
            code = re.sub(r"//.*$", "", ls[k])
            for m in CALL.finditer(code):
                recv, fn = m.group(1), m.group(2)
                t = vtype.get(recv)
                if t is None or t not in FB or fn not in FB[t]:
                    continue
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
                    skipped_untyped += 1
                    continue
                a = code[start + 1:j].strip()
                # 顶层逗号切分(嵌套括号/字符串感知) —— 首版用 a.count(",") 会把
                # `f (x, yyjson取整数 (参数JSON, "seed"))` 数成 3 个实参
                n = 0 if a == "" else len(split_top(a))
                total, required = FB[t][fn]
                checked += 1
                if n > total:
                    over.append((f, k + 1, t, fn, n, total, code.strip()[:110]))

w()
w("经类型解析确认的类库调用点: %d 个 (跨行调用跳过 %d)" % (checked, skipped_untyped))
w()
w("--- [确定性错误] 实参个数 > 该类该方法的形参个数 ---  共 %d" % len(over))
for r in over[:40]:
    w("   %-24s:%-6d %s.%s  实参%d > 形参%d" % (r[0], r[1], r[2], r[3], r[4], r[5]))
    w("        %s" % r[6])
if not over:
    w("   (无)")

p = out_report("report_A4_arity.txt", "\n".join(W))
print("written", p)
print("类型确认调用点 %d | 确定性错误 %d" % (checked, len(over)))
