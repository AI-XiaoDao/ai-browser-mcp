# -*- coding: utf-8 -*-
"""Round 6 核对: HTTP 服务创建检测 + GET/DELETE /mcp 规范和性"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

print("=" * 100)
print("Round 6 — HTTP 启动检测 / GET·DELETE /mcp 规范和性")
print("=" * 100)
print()

CHECKS = [
    ("MCP_Server.wsv", "变量 HTTP服务可用", "HTTP服务可用 状态量"),
    ("MCP_Server.wsv", "变量 HTTP服务已尝试", "HTTP服务已尝试 状态量"),
    ("MCP_Server.wsv", "方法 是否禁用HTTP服务", "是否禁用HTTP服务"),
    ("MCP_Server.wsv", '读环境变量 ("AI_BROWSER_MCP_NO_HTTP")', "环境变量开关读取"),
    ("MCP_Server.wsv", "浏览器容器.HTTP服务已尝试 = 真", "总是尝试创建"),
    ("MCP_Server.wsv", "方法 发送CORS405响应", "405 发送helper"),
    ("MCP_Server.wsv", 'h_Allow.name = "Allow"', "Allow 头(RFC 9110)"),
    ("MCP_Server.wsv", '"GET, POST, DELETE, OPTIONS"', "CORS 允许方法含 DELETE"),
    ("MCP_Server_HTTP.wsv", "如果 (服务器.是否为空 ())", "创建成败可靠判据"),
    ("MCP_Server_HTTP.wsv", "浏览器容器.HTTP服务可用 = 真", "成功回填"),
    ("MCP_Server_HTTP.wsv", "浏览器容器.HTTP服务可用 = 假", "失败回填"),
    ("MCP_Server_HTTP.wsv", 'HTTP方法 == "DELETE"', "DELETE 路由"),
    ("MCP_Server_HTTP.wsv", "发送CORS405响应 (服务器, 连接ID", "GET /mcp 回 405"),
    ("MCP_Server_HTTP.wsv", '如果 (URL路径 == "/api")', "/api 独占元信息路由"),
]
ok = 0
for f, pat, tag in CHECKS:
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [i + 1 for i, l in enumerate(t) if pat in l and not l.strip().startswith("#")]
    if hits:
        ok += 1
    print("  %s%-30s %-22s %s" % ("OK " if hits else "!! ", tag, f, hits[:2] if hits else "未找到"))
print()
print("通过 %d / %d" % (ok, len(CHECKS)))

print()
print("=" * 100)
print("关键方法结构")
print("=" * 100)
for f, want in [("MCP_Server.wsv", ["是否禁用HTTP服务", "发送CORS405响应", "发送CORS响应", "初始化CORS响应头"]),
                ("MCP_Server_HTTP.wsv", ["服务器即将创建", "收到HTTP请求"])]:
    ms = find_methods(f)
    by = {m[1]: m for m in ms}
    for w in want:
        if w in by:
            i0, name, sig, b0, b1 = by[w]
            print("  %-20s %-22s 定义行 %-6d 体 %d~%d (%d 行)" % (name, f, i0 + 1, b0 + 1, b1 + 1, b1 - b0 + 1))
        else:
            print("  %-20s %-22s !! 未解析到" % (w, f))

print()
print("=" * 100)
print("HTTP 请求分派顺序 (确认 GET/DELETE 先于 POST 之前正确落位)")
print("=" * 100)
t = io.open(os.path.join(SRC, "MCP_Server_HTTP.wsv"), encoding="utf-8").read().split("\n")
for i, l in enumerate(t):
    s = l.strip()
    if s.startswith('如果 (HTTP方法 =='):  # noqa
        print("  L%-5d %s" % (i + 1, s))
for i, l in enumerate(t):
    s = l.strip()
    if s.startswith('如果 (URL路径 ==') or s.startswith('如果 (MCP命令服务器.工具列表缓存'):
        print("  L%-5d %s" % (i + 1, s))
