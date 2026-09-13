# -*- coding: utf-8 -*-
"""验证假设: 分支里 `清理缓存.全部` / `缓存类型.全部` 这类**类库常量类引用**是否就是类构建失败的真因。

做法: 临时把这两处(以及助手里同族引用)换成等值数字, 跑语法检查:
  · 错误消失 => 确认是常量类引用的问题(再决定用"项目侧常量"的干净写法替代);
  · 错误仍在 => 另有原因。
无论结果如何都恢复原文件, 不在验证中途留下半成品。
"""
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

CORE = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
BAK = os.path.join(HERE, "_core_consttest.bak")
shutil.copy2(CORE, BAK)
COMPILER = r"E:\HSPC\bin\x64\volcdev_placeholder"
COMPILER = r"E:\HSPC\bin\x64\voldev_awp.exe"
VSLN = "AI-Fbowser-Mcp.vsln"

# 类库常量 → 等值数字
repl = {
    "清理缓存.全部": "4294967295",
    "缓存类型.全部": "4294967295",
    "清理缓存.Appcache": "1",
    "清理缓存.Cookies": "2",
    "清理缓存.FileSystem": "4",
    "清理缓存.IndexedDB": "8",
    "清理缓存.LocalStorage": "16",
    "清理缓存.ShaderCache": "32",
    "清理缓存.WebSql": "64",
    "清理缓存.ServiceWorkers": "128",
    "清理缓存.CacheStorage": "256",
    "清理缓存.PluginPrivateData": "512",
    "清理缓存.BackGroundFetch": "1024",
    "清理缓存.Conversions": "2048",
    "缓存类型.临时": "1",
    "缓存类型.永久": "2",
    "缓存类型.可用": "4",
}


def syntax_check(tag):
    p = subprocess.run([COMPILER, "@compile", VSLN, "/c"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    errs = [l.strip() for l in out.splitlines() if "错误:" in l]
    print("  [%s] 退出码=%s 错误行=%d" % (tag, p.returncode, len(errs)))
    for e in errs[:3]:
        print("      %s" % e[:140])
    return len(errs)


try:
    s = io.open(CORE, encoding="utf-8").read()
    cnt = {k: s.count(k) for k in repl if s.count(k)}
    print("将被替换的常量引用: %s" % cnt)
    for k, v in repl.items():
        s = s.replace(k, v)
    io.open(CORE, "w", encoding="utf-8", newline="\n").write(s)
    n = syntax_check("常量换成数字后")
    print("\n结论: %s" % ("错误消失 => 确认是**类库常量类引用**导致类构建失败"
                          if n == 0 else
                          "错误仍在 => 不是常量引用的问题, 需继续二分"))
finally:
    shutil.copy2(BAK, CORE)
    print("已恢复 Core 原文件")
