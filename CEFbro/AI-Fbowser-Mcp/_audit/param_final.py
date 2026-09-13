# -*- coding: utf-8 -*-
"""A 组 11 项终审: 逐项打印该参数名在全工程的每一次字面量出现 (含所属工具/行)。"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import SRC
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

PROJ = ["main.wsv", "MCP_Server.wsv", "MCP_Stdio.wsv", "MCP_BrowserEvents.wsv",
        "MCP_Callbacks.wsv", "MCP_Server_VIP.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_Core.wsv", "MCP_Server_Form.wsv", "MCP_Server_System.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv",
        "MCP_Server_Utils.wsv", "MCP_Server_Reverse.wsv", "MCP_Kernel.wsv"]
FILES = []
for f in PROJ:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        FILES.append((f, io.open(p, encoding="utf-8").read().split("\n")))

CASES = [
    ("browser_get_text", ["max_chars"]),
    ("browser_dom_query", ["index"]),
    ("browser_evaluate", ["max_ms"]),
    ("browser_intercept", ["match_mode"]),
    ("browser_fingerprint_ua", ["brands"]),
    ("browser_debugger_last_paused", ["parse"]),
    ("browser_vip_enable_inspector", ["repaint"]),
    ("browser_vip_fingerprint_media_devices", ["devices"]),
    ("browser_reverse_scan_crypto", ["script_index"]),
    ("browser_reverse_detect_obfuscator", ["script_index"]),
    ("browser_move_window", ["x", "y", "width", "height", "repaint"]),
]

for tool, keys in CASES:
    print("=" * 100)
    print("工具: %s" % tool)
    print("=" * 100)
    for k in keys:
        lit = '"%s"' % k
        print("  ── 参数 %s ──" % k)
        n = 0
        for f, lines in FILES:
            for i, l in enumerate(lines):
                if lit in l:
                    n += 1
                    if n <= 6:
                        s = l.strip()
                        # 标注是否在读取访问器里
                        mark = "READ" if re.search(r'取\w*\s*\([^)]*' + re.escape(lit), l) else "    "
                        print("     [%s] %s:%d  %s" % (mark, f, i + 1, s[:118]))
        if n == 0:
            print("     ★ 全工程 0 次出现")
        elif n > 6:
            print("     ... 共 %d 次" % n)
    print()
