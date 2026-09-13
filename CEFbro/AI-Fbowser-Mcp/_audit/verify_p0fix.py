# -*- coding: utf-8 -*-
"""P0 修复点验证 + A2 未广告/未读清单对比"""
import io, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

CHECKS = [
    ("MCP_Server.wsv", '返回 (yyjson取逻辑_默认 (参数JSON, "expand", 真))', "P0-1a expand 布尔读取"),
    ("MCP_Server.wsv", '返回 (yyjson取逻辑_默认 (参数JSON, "return_by_value", 真))', "P0-1b return_by_value 布尔读取"),
    ("MCP_Server.wsv", '返回 (yyjson取逻辑_默认 (参数JSON, "resume", 真))', "P0-1c resume 缺省回默认真"),
    ("MCP_Server.wsv", "MCP可中断延时 (200, 50, 假)", "P0-2 取安全主框架 不持锁延时"),
    ("MCP_Server_Core.wsv", 'yyjson取逻辑_默认 (参数JSON, "parse", 假)', "P0-1d parse 布尔读取"),
    ("MCP_Server_Core.wsv", 'yyjson取逻辑_默认 (参数JSON, "fresh", 假)', "P0-1e fresh 布尔读取"),
    ("MCP_Kernel.wsv", "响应字节集 = 取字节集右边 (响应字节集, size - 读取大小)", "P0-3 资源处理器 回写字节集"),
    ("MCP_BrowserEvents.wsv", "返回 (假)", "P0-4 音频Hook 不采集(返回假)"),
    ("MCP_Server_VIP.wsv", 'yyjson取逻辑 (参数JSON, "enable")', "P0-5 is_trusted 键名 enable"),
]

print("=" * 100)
print("P0 修复点验证")
print("=" * 100)
ok = 0
for f, pat, tag in CHECKS:
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [i + 1 for i, l in enumerate(t) if pat in l and not l.strip().startswith("//")]
    mark = "OK " if hits else "!! "
    if hits:
        ok += 1
    print("  %s%-28s %-46s 行%s" % (mark, tag, f, hits[:3] if hits else "未找到"))
print()
print("通过 %d / %d" % (ok, len(CHECKS)))

print()
print("=" * 100)
print("残留检查: 断点家族是否还有 布尔参数被取文本读取 的写法")
print("=" * 100)
BAD = []
for f in ("MCP_Server.wsv", "MCP_Server_Core.wsv"):
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    for i, l in enumerate(t):
        for key in ("expand", "return_by_value", "resume", "parse", "fresh", "async_only",
                    "wait_for_load", "sync_wait", "exclusive", "ignore_cache"):
            if re.search(r'yyjson取文本\s*\([^,]+,\s*"' + key + r'"', l):
                BAD.append((f, i + 1, key, l.strip()[:110]))
if BAD:
    for b in BAD:
        print("   %s:%d 键 %s" % (b[0], b[1], b[2]))
        print("        %s" % b[3])
else:
    print("   无 (上述布尔参数已不再用 取文本 读取)")

print()
print("=" * 100)
print("A2 复检: hard / unread 数")
print("=" * 100)
r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_A2.txt"),
            encoding="utf-8").read()
for line in r.split("\n"):
    if line.startswith("# [") or line.startswith("汇总"):
        print("   " + line)
