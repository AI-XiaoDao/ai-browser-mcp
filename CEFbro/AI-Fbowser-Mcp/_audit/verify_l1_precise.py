# -*- coding: utf-8 -*-
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

CASES = [
    ("MCP_Server_Core.wsv", "exUrlPattern"),
    ("MCP_Server_Core.wsv", "exKeyword"),
    ("MCP_Kernel.wsv", "解除域名"),
]
for f, var in CASES:
    ls = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [(i + 1, l.strip()) for i, l in enumerate(ls)
            if re.search(r"(?<![A-Za-z0-9_\u4e00-\u9fff])" + re.escape(var)
                         + r"(?![A-Za-z0-9_\u4e00-\u9fff])", l)]
    print("=" * 96)
    print("%s  变量 %s  出现 %d 次" % (f, var, len(hits)))
    print("=" * 96)
    for (n, l) in hits:
        print("%6d| %s" % (n, l[:150]))
    print()
