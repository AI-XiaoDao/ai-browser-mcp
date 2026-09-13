# -*- coding: utf-8 -*-
r"""A10 — 为每个方法定义行写入 @输出名 = "<C++输出名>"

依据: 技能书 参考/语法手册/05_五扩展属性表_1.md
  @输出名 数据类型=文本型, 应用场合="任何定义型程序成员",
  用作指定其编译后的输出名称。
写法参考技能书类库真实样例:
  方法 系统变量被改变 <公开 定义事件 类型 = 整数 注释 = "..." @输出名 = "SysVarChanged">

写入策略:
  * 值 = 该成员**当前实际生成**的 C++ 符号名(含 rg_ 前缀), 因此生成的 C++ 完全不变,
    只是把编译器隐式生成的符号名在源码里显式固定下来, 便于 C++ 侧协同开发。
  * 仅写入"高置信"条目: 与 generated-cpp 头文件逐字核对通过 或 字典全字可译且无多音冲突。
    含未收录汉字的条目跳过并单独列出(写错会改变符号, 比不写更糟)。
  * 成员行原无属性表时补 <@输出名 = "...">。
  * 保留原编码与行尾; 逐行内插入, 不增删行。
"""
import sys, os, re, json, io, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

OUT = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
MAP = json.load(open(os.path.join(OUT, "symbol_map.json"), encoding="utf-8"))

APPLY = os.environ.get("APPLY", "0") == "1"
# name       = 仅写 @输出名
# name_force = @输出名 + @强制输出 = 真  (技能书推荐: 未在程序中直接调用就不会被编译输出)
MODE = os.environ.get("MODE", "name_force")
SUFFIX = ' @输出名 = "%s"' + (' @强制输出 = 真' if MODE == "name_force" else "")


def attr_table_close(lines, row0):
    """定位 row0 起的属性表结束位置 '>'; 返回 (row, col) 或 None。字符串感知。"""
    p = lines[row0].find("<")
    if p < 0:
        return None
    in_str = False
    row = row0
    col = p
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
    """在 '>' 之前插入; 回退空白; 若 '>' 位于行首则插在上一行末。"""
    if c == 0:
        if r == 0:
            return None
        return (r - 1, len(lines[r - 1]))
    j = c
    line = lines[r]
    while j > 0 and line[j - 1] in " \t":
        j -= 1
    return (r, j)


report = []
stats = collections.Counter()
skipped = []

# 保护: main.wsv 正在被用户于 IDE 中编辑 (mtime 距检测时刻 <1 分钟), 本次跳过
PROTECT = set(os.environ.get("PROTECT", "").split(",")) - {""}

for f in FILES:
    if f in PROTECT:
        report.append("%-26s 【保护跳过：文件正被编辑】" % f)
        stats["保护跳过"] += 1
        continue
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
    # 重建 类 -> 方法(名, 行idx)
    targets = []            # (row, member_name, cpp, cls)
    cls = None
    for i, ln in enumerate(lines):
        if classify(ln) != "CODE":
            continue
        clean = strip_strings_and_comment(ln)[0]
        m = re.match(r"\s*类\s+(\S+)", clean)
        if m:
            cls = m.group(1); continue
        if cls is None or da[i] != 1:
            continue
        mm = re.match(r"\s*方法\s+(\S+)", clean)
        if not mm:
            continue
        mname = mm.group(1)
        e = MAP.get("%s.%s" % (cls, mname))
        if e is None:
            skipped.append((f, i + 1, cls, mname, "无映射条目")); stats["无映射"] += 1; continue
        if "@输出名" in ln:
            stats["已有"] += 1; continue
        if "?" in e["cpp"]:
            skipped.append((f, i + 1, cls, mname, "含未收录字 -> " + e["cpp"])); stats["跳过(未知字)"] += 1; continue
        targets.append((i, mname, e["cpp"], cls, e["src"]))

    if not targets:
        report.append("%-26s 无写入" % f)
        continue

    # 自底向上插入, 保持行索引有效
    edits_by_row = collections.defaultdict(list)
    for (row, mname, cpp, cls, src) in targets:
        pos = attr_table_close(lines, row)
        if pos is None:
            # 无属性表: 行尾补一个空属性表
            r, ins = row, None
        else:
            pp = insert_pos(lines, pos[0], pos[1])
            if pp is None:
                skipped.append((f, row + 1, cls, mname, "无法定位属性表")); stats["定位失败"] += 1; continue
            r, ins = pp
        edits_by_row[r].append((ins, cpp, mname))
        stats["写入"] += 1

    for r in sorted(edits_by_row, reverse=True):
        for (ins, cpp, mname) in edits_by_row[r]:
            if ins is None:
                lines[r] = lines[r] + " <" + (SUFFIX % cpp) + ">"
            else:
                lines[r] = lines[r][:ins] + (SUFFIX % cpp) + lines[r][ins:]

    new = "\n".join(l + e for l, e in zip(lines, eols))
    if APPLY:
        with open(os.path.join(SRC, f), "wb") as fh:
            fh.write(bom + new.encode("utf-16-le" if bom == b"\xff\xfe" else "utf-8"))
    report.append("%-26s 写入 %3d 条" % (f, len(targets)))

print("APPLY =", APPLY)
for r in report:
    print("  " + r)
print()
print("统计:", dict(stats))
if skipped:
    print()
    print("跳过明细 (%d 条):" % len(skipped))
    for s in skipped[:80]:
        print("   %s:%d  %s.%s  -> %s" % s)
    if len(skipped) > 80:
        print("   ... 另有 %d 条" % (len(skipped) - 80))
