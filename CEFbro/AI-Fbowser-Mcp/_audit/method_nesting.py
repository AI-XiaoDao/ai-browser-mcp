# -*- coding: utf-8 -*-
"""新增检测器: 方法嵌套检查。

背景: 本会话在插入 helper 时曾把新方法插进另一个方法体内(两个 `}` 相邻),
`a1_format` 只查花括号平衡与注释位置 -> **查不出方法嵌套**。
火山要求 方法 声明必须位于**类体内(depth==1)**, depth>1 即为硬编译错误。

判据: 逐字符维护花括号深度; 遇到 `方法 X <` 声明时, 若深度 != 1 -> 报错。
"""
import io
import os

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
PROJ = ["main.wsv", "MCP_Server.wsv", "MCP_Stdio.wsv", "MCP_BrowserEvents.wsv",
        "MCP_Callbacks.wsv", "MCP_Server_VIP.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_Core.wsv", "MCP_Server_Form.wsv", "MCP_Server_System.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv",
        "MCP_Server_Utils.wsv", "MCP_Server_Reverse.wsv", "MCP_Kernel.wsv"]

import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
MSTART = re.compile(r'^\s*方法\s+[\u4e00-\u9fff]')

total_bad = 0
print("=" * 88)
print("方法嵌套检查 (方法声明必须出现在 depth==1 的类体内)")
print("=" * 88)
for f in PROJ:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    text = io.open(p, encoding="utf-8").read()
    depth, i, in_str, line, bad = 0, 0, False, 1, []
    while i < len(text):
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "/" and text[i:i + 2] == "//":
                j = text.find("\n", i)
                i = len(text) if j < 0 else j
                continue
            elif c == "@":
                # @ 行是不透明的嵌入 C++, 其花括号必须跳过(否则 depth 被污染)
                j = text.find("\\n", i)
                i = len(text) if j < 0 else j
                continue
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == "方" and text[i:i + 2] == "方法":
                # 只看行首的方法声明
                ls = text.rfind("\n", 0, i)
                prefix = text[ls + 1:i]
                if prefix.strip() == "" and depth != 1:
                    bad.append((line, depth))
        i += 1
    if bad:
        total_bad += len(bad)
        print("  !! %-26s 嵌套异常 %d 处: %s" % (f, len(bad), bad[:5]))
    else:
        print("  OK %-26s 全部方法均在类体内" % f)
print()
print("★ 嵌套异常合计: %d" % total_bad)
