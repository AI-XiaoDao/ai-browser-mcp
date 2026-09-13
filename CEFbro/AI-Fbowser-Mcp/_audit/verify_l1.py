# -*- coding: utf-8 -*-
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"


def show(f, a, b, tag):
    ls = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    print("=" * 100)
    print("%s   %s:%d-%d" % (tag, f, a, b))
    print("=" * 100)
    for k in range(a - 1, min(b, len(ls))):
        print("%6d| %s" % (k + 1, ls[k]))
    print()


show("MCP_Server_Core.wsv", 5640, 5700, "L1-a  url_pattern / keyword 被丢弃")

# 找 5657 所属的工具分支
ls = io.open(os.path.join(SRC, "MCP_Server_Core.wsv"), encoding="utf-8").read().split("\n")
for k in range(5657, 0, -1):
    m = re.search(r'方法名\s*==\s*"([A-Za-z0-9_]+)"', ls[k])
    if m:
        print(">>> 5657 所属工具分支: %s  (分支行 %d)" % (m.group(1), k + 1))
        break
print()

show("MCP_Kernel.wsv", 415, 470, "L1-b  解除域名 被丢弃")
