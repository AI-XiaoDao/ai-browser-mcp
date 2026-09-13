# -*- coding: utf-8 -*-
r"""B6 — 把英文输出名写入 .wsv

写入规则:
  类     : @输出名 = "<Class>"          (启动类 跳过)
  方法   : @输出名 = "<Method>" @强制输出 = 真   (虚拟覆盖 跳过)
  变量/常量: @输出名 = "<Var>"
  参数   : @输出名 = "<Param>"

安全:
  * PROTECT 中的文件(默认 main.wsv)不写
  * 保留原编码与行尾; 仅在行内插入, 不增删行
  * 属性表缺失时补 <...>
  * 自底向上插入以保持行号有效
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

OUT = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
NAMES = json.load(open(os.path.join(OUT, "english_names.json"), encoding="utf-8"))
APPLY = os.environ.get("APPLY", "0") == "1"
PROTECT = set(os.environ.get("PROTECT", "main.wsv").split(",")) - {""}


def attr_close(lines, row0):
    p = lines[row0].find("<")
    if p < 0:
        return None
    in_str, row, col = False, row0, p
    while row < len(lines):
        line = lines[row]
        k = col if row == row0 else 0
        while k < len(line):
            ch = line[k]
            if in_str:
                if ch == "\\":
                    k += 2; continue
                if ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == ">":
                    return (row, k)
            k += 1
        row += 1
    return None


def insert_pos(lines, r, c):
    if c == 0:
        return (r - 1, len(lines[r - 1])) if r > 0 else None
    j = c
    while j > 0 and lines[r][j - 1] in " \t":
        j -= 1
    return (r, j)


report, stats, skipped = [], collections.Counter(), []

for f in FILES:
    if f in PROTECT:
        report.append("%-26s 【保护跳过】" % f); stats["保护跳过"] += 1; continue
    raw = open(os.path.join(SRC, f), "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        text = raw[3:].decode("utf-8"); bom = b"\xef\xbb\xbf"
    elif raw[:2] == b"\xff\xfe":
        text = raw.decode("utf-16-le"); bom = b"\xff\xfe"
    else:
        text = raw.decode("utf-8"); bom = b""
    parts = text.split("\n")
    lines, eols = [], []
    for p in parts:
        if p.endswith("\r"):
            lines.append(p[:-1]); eols.append("\r")
        else:
            lines.append(p); eols.append("")

    _, db, da = brace_map(f)
    edits = collections.defaultdict(list)   # row -> [(pos|None, suffix)]
    n_cls = n_m = n_v = n_p = 0
    cls = None
    for i, ln in enumerate(lines):
        if classify(ln) != "CODE":
            continue
        clean = strip_strings_and_comment(ln)[0]
        m = re.match(r"\s*类\s+(\S+)", clean)
        if m:
            cls = m.group(1)
            e = NAMES["classes"].get(cls)
            if e and not e["keep"]:
                r, c = (i, ln.find("<"))
                pos = attr_close(lines, i)
                edits[insert_pos(lines, *pos)[0] if pos else i].append(
                    (insert_pos(lines, *pos)[1] if pos else None,
                     ' @输出名 = "%s"' % e["en"]))
                n_cls += 1
            continue
        if cls is None or da[i] != 1:
            continue
        mm = re.match(r"\s*方法\s+(\S+)", clean)
        if mm:
            mname = mm.group(1)
            e = NAMES["methods"].get("%s.%s" % (cls, mname))
            if e is None:
                skipped.append((f, i + 1, cls, mname, "无条目")); stats["无条目"] += 1; continue
            if e["keep"]:
                stats["虚拟覆盖保留"] += 1
            else:
                pos = attr_close(lines, i)
                if pos is None:
                    edits[i].append((None, ' <@输出名 = "%s" @强制输出 = 真>' % e["en"]))
                else:
                    r, c = insert_pos(lines, *pos)
                    edits[r].append((c, ' @输出名 = "%s" @强制输出 = 真' % e["en"]))
                n_m += 1
            # 参数
            k = i + 1
            while k < len(lines) and re.match(r"\s*参数\s+\S+", lines[k]):
                pm = re.match(r"\s*参数\s+(\S+)", lines[k])
                pe = NAMES["params"].get("%s|%s|%s" % (cls, mname, pm.group(1)))
                if pe:
                    pp = attr_close(lines, k)
                    if pp is None:
                        edits[k].append((None, ' <@输出名 = "%s">' % pe["en"]))
                    else:
                        rr, cc = insert_pos(lines, *pp)
                        edits[rr].append((cc, ' @输出名 = "%s"' % pe["en"]))
                    n_p += 1
                k += 1
            continue
        mv = re.match(r"\s*(变量|常量)\s+(\S+)", clean)
        if mv:
            vname = mv.group(2)
            e = NAMES["vars"].get("%s.%s" % (cls, vname))
            if e:
                pos = attr_close(lines, i)
                if pos is None:
                    edits[i].append((None, ' <@输出名 = "%s">' % e["en"]))
                else:
                    r, c = insert_pos(lines, *pos)
                    edits[r].append((c, ' @输出名 = "%s"' % e["en"]))
                n_v += 1
            else:
                skipped.append((f, i + 1, cls, vname, "无变量条目")); stats["无条目"] += 1

    for r in sorted(edits, reverse=True):
        for (pos, suf) in sorted(edits[r], key=lambda x: (-1 if x[0] is None else x[0]), reverse=True):
            if pos is None:
                lines[r] = lines[r] + suf
            else:
                lines[r] = lines[r][:pos] + suf + lines[r][pos:]

    if APPLY:
        new = "\n".join(l + e for l, e in zip(lines, eols))
        with open(os.path.join(SRC, f), "wb") as fh:
            fh.write(bom + new.encode("utf-16-le" if bom == b"\xff\xfe" else "utf-8"))
    report.append("%-26s 类%2d 方法%3d 变量%3d 参数%3d" % (f, n_cls, n_m, n_v, n_p))
    stats["类"] += n_cls; stats["方法"] += n_m; stats["变量"] += n_v; stats["参数"] += n_p

print("APPLY =", APPLY)
for r in report:
    print("  " + r)
print()
print("统计:", dict(stats))
if skipped:
    print()
    print("跳过 %d 条:" % len(skipped))
    for s in skipped[:20]:
        print("   %s:%d %s.%s -> %s" % s)
