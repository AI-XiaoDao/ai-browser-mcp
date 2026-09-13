# -*- coding: utf-8 -*-
r"""查看 mcp_help 的回包结构, 并定位"指引"文案到底从哪个字段出去(用于确认 help 文案改动是否真的可见)。"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode(),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    rr = o.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")


t = call("mcp_help", {})
print('mcp_help 回包长度=%d' % len(t))
print('含"AI浏览器 MCP Server":', 'AI浏览器 MCP Server' in t)
print('含"所有工具通用参数":', '所有工具通用参数' in t)
print('含"1MB":', '1MB' in t)
print('前 300 字: %s' % t[:300].replace('\n', ' '))
# 也看看 /api 与 /tools/brief 是否承载该文案
try:
    api = urllib.request.urlopen(BASE + "/api", timeout=20).read().decode()
    print('/api 含"所有工具通用参数":', '所有工具通用参数' in api)
except Exception as ex:
    print('/api 失败: %r' % ex)
