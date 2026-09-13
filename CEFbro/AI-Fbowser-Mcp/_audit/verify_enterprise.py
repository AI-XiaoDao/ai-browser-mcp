# -*- coding: utf-8 -*-
"""企业级能力落地核对"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

CHECKS = [
    ("MCP_Server.wsv", "变量 指标_请求总数", "指标: 请求总数"),
    ("MCP_Server.wsv", "变量 指标_错误响应数", "指标: 错误响应"),
    ("MCP_Server.wsv", "变量 指标_限流拒绝数", "指标: 限流拒绝"),
    ("MCP_Server.wsv", "变量 指标_认证失败数", "指标: 认证失败"),
    ("MCP_Server.wsv", "变量 指标_协议错误数", "指标: 协议错误"),
    ("MCP_Server.wsv", "方法 取指标文本", "Prometheus 指标文本"),
    ("MCP_Server.wsv", "mcp_requests_total", "指标命名(mcp_ 前缀)"),
    ("MCP_Server.wsv", "变量 MCP日志级别", "logging: 级别状态"),
    ("MCP_Server.wsv", 'logging/setLevel', "logging/setLevel 方法"),
    ("MCP_Server.wsv", 'completion/complete', "completion/complete 方法"),
    ("MCP_Server.wsv", 'resources/templates/list', "resources/templates/list"),
    ("MCP_Server.wsv", "方法 搜索工具名补全", "工具名补全实现"),
    ("MCP_Server.wsv", '"logging", 日志能力', "capabilities.logging 声明"),
    ("MCP_Server.wsv", '"completions", 补全能力', "capabilities.completions 声明"),
    ("MCP_Server_HTTP.wsv", '/metrics', "HTTP /metrics 路由"),
    ("MCP_Server_HTTP.wsv", 'text/plain; version=0.0.4', "Prometheus Content-Type"),
    ("MCP_Server_HTTP.wsv", 'latency_avg_ms', "/health 延迟均值"),
    ("MCP_Server_HTTP.wsv", 'active_requests', "/health 并发度"),
]

print("=" * 96)
print("企业级能力落地核对")
print("=" * 96)
ok = 0
for f, pat, tag in CHECKS:
    t = io.open(os.path.join(SRC, f), encoding="utf-8").read().split("\n")
    hits = [i + 1 for i, l in enumerate(t) if pat in l and not l.strip().startswith("#")]
    if hits:
        ok += 1
    print("  %s%-24s %-22s %s" % ("OK " if hits else "!! ", tag, f, hits[:2] if hits else "未找到"))
print()
print("通过 %d / %d" % (ok, len(CHECKS)))
