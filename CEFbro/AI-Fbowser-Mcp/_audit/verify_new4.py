# -*- coding: utf-8 -*-
"""核实 A2 的 4 条新发现"""
import io, re, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
core = io.open(os.path.join(SRC, "MCP_Server_Core.wsv"), encoding="utf-8").read().split("\n")


def branch(tool, span=90):
    for i, l in enumerate(core):
        if ('"' + tool + '"') in l and "方法名" in l:
            return i, core[i:i + span]
    return None, []


def scan(tool, pats, span=90):
    i, blk = branch(tool, span)
    print("=== %s  (分支起始行 %d) ===" % (tool, i + 1 if i is not None else -1))
    if i is None:
        print("   未找到分支")
        return
    for j, l in enumerate(blk):
        for p in pats:
            if p in l:
                print("   %5d| %s" % (i + j + 1, l.strip()[:140]))
                break
    print()


scan("browser_get_text", ["max_chars"])
scan("browser_retry", ['"args"', '"tool"', '"max_retries"', "重试参数", "args"])
scan("browser_reverse_scan_crypto", ["script_index"])
scan("browser_reverse_detect_obfuscator", ["script_index"])

print("=== schema 中这 4 处的声明 ===")
srv = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
for i, l in enumerate(srv):
    if any(('"' + t + '"') in l and "添加工具JSON" in l
           for t in ["browser_get_text", "browser_retry",
                     "browser_reverse_scan_crypto", "browser_reverse_detect_obfuscator"]):
        print("   %5d| %s" % (i + 1, l.strip()[:230]))
