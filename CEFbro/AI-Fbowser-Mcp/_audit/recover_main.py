# -*- coding: utf-8 -*-
"""搜索被覆盖的 main.wsv 版本 (含 渲染_即将创建V8环境)"""
import os, subprocess, glob
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

PAT = "渲染_即将创建V8环境".encode("utf-8")
ROOTS = [
    r"C:\Users\cxzxc\Desktop\MCP源码",
    r"C:\Users\cxzxc\AppData\Local\Temp",
    r"C:\Users\cxzxc\AppData\Roaming",
    r"C:\Users\cxzxc\Documents",
    r"D:\\",
]
EXTS = (".wsv", ".vbak", ".bak", ".tmp", ".txt", ".vhistory", ".as", ".zip", ".7z")
hits = []
seen = 0
for root in ROOTS:
    if not os.path.isdir(root):
        continue
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "generated-cpp")]
        for fn in files:
            if not fn.lower().endswith(EXTS):
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > 60 * 1024 * 1024:
                    continue
                d = open(p, "rb").read()
            except Exception:
                continue
            seen += 1
            if PAT in d and "main.wsv" in fn:
                hits.append((p, len(d), d.count(b"\n")))

print("扫描文件数:", seen)
print()
if hits:
    print("!!! 找到候选副本:")
    for (p, sz, ln) in hits:
        print("   %s  (%d 字节, %d 行)" % (p, sz, ln))
else:
    print("未找到包含该方法的 main.wsv 副本。")
    print()
    print("--- 放宽: 任何含该字符串的文件 ---")
    for root in ROOTS[:2]:
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git")]
            for fn in files:
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) > 20 * 1024 * 1024:
                        continue
                    d = open(p, "rb").read()
                except Exception:
                    continue
                if PAT in d:
                    print("   %s  (%d 字节)" % (p, len(d)))
