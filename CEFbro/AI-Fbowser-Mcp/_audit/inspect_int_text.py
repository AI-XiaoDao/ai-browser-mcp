# -*- coding: utf-8 -*-
import io, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
t = io.open(os.path.join(SRC, "MCP_Server_Core.wsv"), encoding="utf-8").read().split("\n")
pat = re.compile(r'yyjson取文本\s*\(参数JSON,\s*"(column|line)"\)')
print("=== integer 声明却按文本读取的实际写法 ===")
for i, l in enumerate(t):
    if pat.search(l):
        print("%6d| %s" % (i + 1, l.strip()[:170]))
        for k in range(i + 1, min(i + 4, len(t))):
            print("      | %s" % t[k].strip()[:150])
        print()

print("=== 对照: 同一项目里 column/line 的正确双模写法 ===")
ok = re.compile(r'yyjson取整数\s*\(参数JSON,\s*"(column|line)"\)')
for i, l in enumerate(t):
    if ok.search(l):
        print("%6d| %s" % (i + 1, l.strip()[:170]))
        for k in range(i + 1, min(i + 3, len(t))):
            print("      | %s" % t[k].strip()[:150])
        print()
