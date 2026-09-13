# -*- coding: utf-8 -*-
"""验证: 精简工具清单 (M 系列) 的实现完整性"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

CHECKS = [
    ("MCP_Server.wsv", "变量 工具简表构建缓冲区", "静态变量声明"),
    ("MCP_Server.wsv", "方法 取简述文本", "一行摘要helper"),
    ("MCP_Server.wsv", "工具简表构建缓冲区 = \"[\"", "开始构建时重置"),
    ("MCP_Server.wsv", "工具简表构建缓冲区 = 工具简表构建缓冲区 + \",\"", "追加分隔"),
    ("MCP_Server.wsv", "工具简表构建缓冲区 = 工具简表构建缓冲区 + \"]\"", "收尾闭合"),
    ("MCP_Server.wsv", "方法 取精简工具列表", "精简清单入口"),
    ("MCP_Server.wsv", "协议锁.加锁 ()", "(存在性)"),
    ("MCP_Server_HTTP.wsv", "/tools/brief", "HTTP路由"),
    ("MCP_Server_HTTP.wsv", "取精简工具列表 ()", "路由调用"),
]

print("=" * 92)
print("精简工具清单 (/tools/brief) 实现核对")
print("=" * 92)
ok = 0
for f, pat, tag in CHECKS:
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [i + 1 for i, l in enumerate(t) if pat in l and not l.strip().startswith("#")]
    mark = "OK " if hits else "!! "
    if hits:
        ok += 1
    print("  %s%-22s %-26s %s" % (mark, tag, f, hits[:3] if hits else "未找到"))
print()
print("通过 %d / %d" % (ok, len(CHECKS)))

print()
print("=" * 92)
print("取精简工具列表 全文")
print("=" * 92)
t = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
a = [i for i, l in enumerate(t) if "方法 取精简工具列表" in l][0]
for k in range(a, min(a + 20, len(t))):
    print("%6d| %s" % (k + 1, t[k]))
