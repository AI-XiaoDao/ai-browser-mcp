# -*- coding: utf-8 -*-
"""企业级能力(会话/进度)落地核对 + 方法结构完整性"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

print("=" * 96)
print("Round 5 企业级能力核对")
print("=" * 96)
print()

CHECKS = [
    ("MCP_Server.wsv", "变量 会话ID", "会话ID 状态量"),
    ("MCP_Server.wsv", "h_Session.name = \"Mcp-Session-Id\"", "响应头 Mcp-Session-Id"),
    ("MCP_Server.wsv", "Access-Control-Expose-Headers", "CORS 暴露头"),
    ("MCP_Server.wsv", "变量 当前进度令牌", "进度令牌 状态量"),
    ("MCP_Server.wsv", "变量 当前推送通道", "推送通道 状态量"),
    ("MCP_Server.wsv", "方法 上报进度", "上报进度 实现"),
    ("MCP_Server.wsv", "notifications/progress", "progress 通知帧"),
    ("MCP_Server.wsv", "发送WebSocket数据", "WS 推送分支"),
    ("MCP_Stdio.wsv", "方法 写入一行", "stdio 推送分支(复用)"),
    ("MCP_Server.wsv", "保存进度令牌 = 当前进度令牌", "放锁前保存进度上下文"),
    ("MCP_Server.wsv", "当前进度令牌 = 保存进度令牌", "取回锁后恢复进度上下文"),
]
ok = 0
for f, pat, tag in CHECKS:
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [i + 1 for i, l in enumerate(t) if pat in l and not l.strip().startswith("#")]
    if hits:
        ok += 1
    print("  %s%-28s %-22s %s" % ("OK " if hits else "!! ", tag, f, hits[:2] if hits else "未找到"))
print()
print("通过 %d / %d" % (ok, len(CHECKS)))

print()
print("=" * 96)
print("关键方法结构 (确认编辑未破坏方法边界)")
print("=" * 96)
ms = find_methods("MCP_Server.wsv")
want = ["协议锁让出延时", "上报进度", "同步等待异步任务", "等待异步任务完成",
        "取指标文本", "搜索工具名补全", "取精简工具列表", "取工具详情JSON"]
by = {m[1]: m for m in ms}
for w in want:
    if w in by:
        i0, name, sig, b0, b1 = by[w]
        print("  %-20s 定义行 %-6d 体 %d~%d  (%d 行)" % (name, i0 + 1, b0 + 1, b1 + 1, b1 - b0 + 1))
    else:
        print("  %-20s !! 未解析到" % w)

print()
print("方法总数: %d" % len(ms))
