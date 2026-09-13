# -*- coding: utf-8 -*-
"""检查编译产物: 验证 @输出名 是否被编译器采用"""
import os, re, json, hashlib, datetime
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

ROOT = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
INT = os.path.join(ROOT, "_int")


def ts(p):
    return datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m-%d %H:%M:%S")


print("=" * 100)
print("编译产物检查")
print("=" * 100)
print()
print("--- src 文件 mtime (我的英文写入时刻) ---")
src = os.path.join(ROOT, "src")
rows = []
for fn in os.listdir(src):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        p = os.path.join(src, fn)
        rows.append((os.path.getmtime(p), fn, os.path.getsize(p)))
rows.sort(reverse=True)
for t, fn, sz in rows:
    print("   %s  %-26s %7d B" % (datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M:%S"), fn, sz))

print()
print("--- _int 下的生成 C++ (compiler 目录) ---")
comp = os.path.join(INT, "AI-Fbowser-Mcp", "debug", "x64", "compiler")
if not os.path.isdir(comp):
    print("   目录不存在:", comp)
else:
    files = sorted(os.listdir(comp))
    print("   文件数:", len(files))
    hs = [f for f in files if f.startswith("vcls_") and f.endswith(".h")]
    ps = [f for f in files if f.startswith("vpkg_") and f.endswith(".cpp")]
    print("   vcls_*.h: %d   vpkg_*.cpp: %d" % (len(hs), len(ps)))
    print()
    print("   抽样 (按时间):")
    for f in sorted(files, key=lambda x: -os.path.getmtime(os.path.join(comp, x)))[:10]:
        p = os.path.join(comp, f)
        print("     %s  %-46s %8d B" % (ts(p), f, os.path.getsize(p)))

print()
print("--- 关键验证: 生成头里是否出现英文输出名 ---")
targets = ["MCPServerTool", "MCPCommandServer", "ConsoleOutput", "GetMainBrowser",
           "HandleMCPRequest", "MCPKernelDispatch", "MCPConst", "MCPResponseBuilder"]
found_any = False
if os.path.isdir(comp):
    for f in os.listdir(comp):
        if not f.endswith(".h"):
            continue
        p = os.path.join(comp, f)
        try:
            d = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        hit = [t for t in targets if re.search(r"\b" + t + r"\b", d)]
        if hit:
            found_any = True
            print("   %-46s -> %s" % (f, ", ".join(hit)))
if not found_any:
    print("   (未在任何 .h 中找到) —— 抽取 vcls_rg_*.h 内容确认")

print()
print("--- 直接找 MCP_服务器工具 / MCP命令服务器 对应的头 ---")
if os.path.isdir(comp):
    for f in os.listdir(comp):
        if not f.endswith(".h"):
            continue
        p = os.path.join(comp, f)
        d = open(p, encoding="utf-8", errors="replace").read()
        if "rg_volcano_app" in d and ("MCPServerTool" in d or "MCPCommandServer" in d):
            print("   ########", f)
            print(d[:1800])
            break
