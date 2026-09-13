# -*- coding: utf-8 -*-
"""把改动过的 .wsv 做一次花括号收支自检(语法形态的快速体检, 不替代编译器)。

规则(与项目既有结论一致):
  · `@` 开头行是内嵌 C++ 原文, 不参与计数;
  · `//` 与 `#` 整行注释不参与计数;
  · 行内字符串字面量里的括号不参与计数(逐字符扫, 处理反斜杠转义)。
末深度应为 0(整个文件配平); 最小深度不应为负。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

FILES = ["MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_Reverse.wsv",
         "MCP_Server_VIP.wsv", "MCP_Kernel.wsv", "MCP_ResponseBuilders.wsv",
         "main.wsv", "MCP_BrowserEvents.wsv"]


def check(path):
    lines = io.open(path, encoding="utf-8").read().split("\n")
    depth = 0
    mn = 0
    bad = []
    odd_quote_lines = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("@") or s.startswith("//") or s.startswith("#"):
            continue
        keep = []
        inq = False
        j = 0
        while j < len(s):
            c = s[j]
            if inq:
                if c == "\\":
                    j += 2
                    continue
                if c == '"':
                    inq = False
            else:
                # 行尾注释必须剥掉: 注释里出现的引号若被当成字符串起点, 会把该行剩余部分
                # 全当字符串, 于是真正的 {} 被漏计 —— 我第一版就因此把 MCP_Server.wsv 误报成
                # "末深度=-2"(而它编译 0 错 0 警)。扫描器自身有 bug, 不能当成源码问题。
                if c == "/" and j + 1 < len(s) and s[j + 1] == "/":
                    break
                if c == '"':
                    inq = True
                elif c in "{}":
                    keep.append(c)
            j += 1
        if inq:
            # 整行结束仍在字符串里: 要么是多行字符串(本方言少用), 要么是注释引号干扰 —— 单独报告
            odd_quote_lines.append(i + 1)
        depth += keep.count("{") - keep.count("}")
        if depth < mn:
            mn = depth
            bad.append(i + 1)
    return depth, mn, bad, odd_quote_lines


badany = 0
for f in FILES:
    p = os.path.join(ROOT, "src", f)
    if not os.path.exists(p):
        print("%-28s (不存在, 跳过)" % f)
        continue
    d, mn, bad, odd = check(p)
    ok = (d == 0 and mn >= 0)
    print("%-28s 末深度=%-4d 最小深度=%-4d %s%s%s"
          % (f, d, mn, "OK" if ok else "!!! 异常",
             (" 首次异常行=%s" % bad[:5]) if bad else "",
             (" 疑似未闭合字符串行=%s" % odd[:5]) if odd else ""))
    if not ok:
        badany += 1
print("\n结果: %s" % ("全部配平" if badany == 0 else "%d 个文件异常" % badany))
sys.exit(1 if badany else 0)
