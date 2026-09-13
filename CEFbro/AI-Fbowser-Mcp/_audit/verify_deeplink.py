# -*- coding: utf-8 -*-
"""验证 mcp_help 深链实现"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

CHECKS = [
    ("MCP_Server.wsv", "方法 取工具详情JSON", "详情查询入口"),
    ("MCP_Server.wsv", '锚点 = "{\\"name\\":\\""', "锚点构造"),
    ("MCP_Server.wsv", "下一段 = 寻找文本 (工具列表缓存", "条目边界查找"),
    ("MCP_Server.wsv", "倒找文本", "末条兜底"),
    ("MCP_Server_Core.wsv", 'yyjson取文本 (参数JSON, "tool")', "读取 tool 参数"),
    ("MCP_Server_Core.wsv", "取工具详情JSON (深链工具名)", "调用详情查询"),
    ("MCP_Server_Core.wsv", "未找到工具: ", "未命中提示"),
]

print("=" * 96)
print("mcp_help <tool> 深链实现核对")
print("=" * 96)
ok = 0
for f, pat, tag in CHECKS:
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [i + 1 for i, l in enumerate(t) if pat in l and not l.strip().startswith("#")]
    if hits:
        ok += 1
    print("  %s%-18s %-24s %s" % ("OK " if hits else "!! ", tag, f, hits[:3] if hits else "未找到"))
print()
print("通过 %d / %d" % (ok, len(CHECKS)))

print()
print("=" * 96)
print("取工具详情JSON 核心逻辑")
print("=" * 96)
t = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
a = [i for i, l in enumerate(t) if "方法 取工具详情JSON" in l][0]
for k in range(a, min(a + 46, len(t))):
    print("%6d| %s" % (k + 1, t[k]))
