# -*- coding: utf-8 -*-
"""把 高级鼠标_单击 附近的原文逐字 dump 到文件(避免 GBK 控制台吞掉 ⚠ 等字符)。"""
import io
import os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
p = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
L = io.open(p, encoding="utf-8").read().split("\n")
out = []
for i, l in enumerate(L):
    if "高级鼠标_单击" in l:
        out.append("=== 命中行 %d ===" % (i + 1))
        for j in range(max(0, i - 3), min(len(L), i + 4)):
            out.append("%d |%s|" % (j + 1, L[j]))
io.open(os.path.join(HERE, "_dump_dead.txt"), "w", encoding="utf-8").write("\n".join(out))
print("written", len(out), "lines")
