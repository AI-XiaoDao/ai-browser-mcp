# -*- coding: utf-8 -*-
import io, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

t = io.open(os.path.join(SRC, "MCP_BrowserEvents.wsv"), encoding="utf-8").read().split("\n")
i = [k for k, l in enumerate(t) if "方法 浏览器_获取音频参数" in l][0]
print("=== P0-4  浏览器_获取音频参数 (定义行 %d) 尾部 ===" % (i + 1))
for k in range(i + 44, min(i + 62, len(t))):
    print("%6d| %s" % (k + 1, t[k]))

print()
v = io.open(os.path.join(SRC, "MCP_Server_VIP.wsv"), encoding="utf-8").read().split("\n")
print("=== P0-5  内核开关_设置EventIsTrusted ===")
for k, l in enumerate(v):
    if "内核开关_设置EventIsTrusted" in l:
        print("%6d| %s" % (k + 1, l.strip()))

print()
kk = io.open(os.path.join(SRC, "MCP_Kernel.wsv"), encoding="utf-8").read().split("\n")
j = [k for k, l in enumerate(kk) if "方法 读取 <公开" in l][0]
print("=== P0-3  类_MCP_方案资源处理器.读取 ===")
for k in range(j, min(j + 36, len(kk))):
    print("%6d| %s" % (k + 1, kk[k]))
