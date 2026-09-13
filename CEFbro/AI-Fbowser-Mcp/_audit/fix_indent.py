# -*- coding: utf-8 -*-
"""把 MCP_Kernel.wsv 两处补丁的缩进对齐到所在层级 (火山按花括号解析, 缩进仅影响可读性)。"""
import io
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Kernel.wsv"
lines = io.open(P, encoding="utf-8").read().split("\n")

# 定位: 缩进异常的 "如果 (数据 == \"\")" 行 -> 其后 5 行需要重新缩进
fixed = 0
i = 0
while i < len(lines):
    s = lines[i]
    st = s.strip()
    ind = len(s) - len(s.lstrip())
    if st == '如果 (数据 == "")' and ind == 12:
        # 期望: 如果 12 / { 12 / 注释 16 / 返回 16 / } 12 / 返回 12
        want = [12, 12, 16, 16, 12, 12]
        for k in range(6):
            j = i + k
            if j >= len(lines):
                break
            body = lines[j].strip()
            lines[j] = " " * want[k] + body
        fixed += 1
        i += 6
        continue
    i += 1

io.open(P, "w", encoding="utf-8", newline="").write("\n".join(lines))
print("已修正缩进块: %d" % fixed)

# 复核
t = io.open(P, encoding="utf-8").read().split("\n")
for n in range(1336, 1384):
    if n - 1 < len(t):
        l = t[n - 1]
        if l.strip():
            ind = len(l) - len(l.lstrip())
            print("%5d|%3d| %s" % (n, ind, l.strip()[:88]))
