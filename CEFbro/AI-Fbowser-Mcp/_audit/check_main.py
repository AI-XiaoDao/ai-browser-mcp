# -*- coding: utf-8 -*-
import os, subprocess, hashlib, io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

REPO = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp"
CUR = os.path.join(REPO, r"CEFbro\AI-Fbowser-Mcp\src\main.wsv")
BAK = os.path.join(REPO, r"CEFbro\AI-Fbowser-Mcp\备份\输出名-20260830-前\main.wsv")

def info(tag, path=None, data=None):
    if data is None:
        data = open(path, "rb").read()
    n_lines_crlf = data.count(b"\r\n")
    n_lf = data.count(b"\n")
    has = "渲染_即将创建V8环境".encode("utf-8") in data
    print("%-26s bytes=%7d  LF=%5d CRLF=%5d  sha256=%s  含新方法=%s"
          % (tag, len(data), n_lf, n_lines_crlf, hashlib.sha256(data).hexdigest()[:16], has))
    return data

print("=" * 100)
cur = info("当前磁盘 main.wsv", CUR)
bak = info("我的备份 main.wsv", BAK)
head = subprocess.run(["git", "show", "HEAD:CEFbro/AI-Fbowser-Mcp/src/main.wsv"],
                      cwd=REPO, capture_output=True).stdout
info("git HEAD main.wsv", data=head)
print()
print("当前 == 备份 ?", cur == bak)
print("当前 == HEAD ?", cur == head)
print("备份 == HEAD ?", bak == head)
print()
print("--- 搜索所有可能保存了 18:21 版本的副本 ---")
pat = "渲染_即将创建V8环境".encode("utf-8")
for root, dirs, files in os.walk(os.path.join(REPO, "CEFbro")):
    if "generated-cpp" in root:
        continue
    for fn in files:
        if not fn.lower().endswith((".wsv", ".vbak", ".bak", ".txt", ".~vbak")):
            continue
        p = os.path.join(root, fn)
        try:
            d = open(p, "rb").read()
        except Exception:
            continue
        if pat in d:
            print("  命中: %s  (%d 字节, %d 行)" % (p, len(d), d.count(b"\n")))
print()
print("--- src 目录下所有 main*.wsv* ---")
for fn in sorted(os.listdir(os.path.dirname(CUR))):
    if fn.startswith("main"):
        p = os.path.join(os.path.dirname(CUR), fn)
        d = open(p, "rb").read()
        print("  %-34s %7d 字节  %5d 行  含新方法=%s" % (fn, len(d), d.count(b"\n"), pat in d))
