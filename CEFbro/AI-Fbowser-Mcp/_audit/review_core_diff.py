# -*- coding: utf-8 -*-
"""把当前 MCP_Server_Core.wsv 与"本轮写入前"备份做逐行 diff, 逐条审阅删除行。

起因: 我重构鼠标分支时**漏读了分支开头**, 把 click/wheel 的缺参守卫整段删除,
      靠 fastcheck 才发现。故此处强制逐行核对: **每一个被删除的行都必须能解释**。
输出到 _audit/_core_diff.txt(UTF-8), 并在控制台只打印统计与"未解释的删除"。
"""
import difflib
import io
import os
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

# 本会话第三次栽在同一个坑上: 控制台是 GBK, 而源码/消息含 ⚠ 等字符 →
# print 抛 UnicodeEncodeError, "统计打到一半就崩"。统一强制 utf-8 + replace。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CUR = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
BAK = os.path.join(ROOT, "备份", "CDP触摸派发与死代码清理-写入前", "MCP_Server_Core.wsv")

a = io.open(BAK, encoding="utf-8").read().split("\n")
b = io.open(CUR, encoding="utf-8").read().split("\n")

d = list(difflib.unified_diff(a, b, "写入前", "当前", n=2, lineterm=""))
io.open(os.path.join(HERE, "_core_diff.txt"), "w", encoding="utf-8").write("\n".join(d))

# 统计删除/新增的可执行行(排除空行与纯注释), 便于判断是否"只该删死代码, 只该加新结构"
def code(s):
    t = s.strip()
    return t and not t.startswith("//") and not t.startswith("#") and not t.startswith("@")

minus = [l[1:] for l in d if l.startswith("-") and not l.startswith("---")]
plus = [l[1:] for l in d if l.startswith("+") and not l.startswith("+++")]

# 报告直接由 python 写 UTF-8 文件(PowerShell 的 > 会写 UTF-16, 读不回来)
rep = []
rep.append("diff 行数 %d | 删除 %d (其中可执行 %d) | 新增 %d (其中可执行 %d)"
           % (len(d), len(minus), len([x for x in minus if code(x)]),
              len(plus), len([x for x in plus if code(x)])))
rep.append("\n== 被删除的可执行行(必须逐条能解释) ==")
for x in minus:
    if code(x):
        rep.append("  - %s" % x.strip()[:160])
rep.append("\n== 新增的可执行行(应为新结构) ==")
for x in plus:
    if code(x):
        rep.append("  + %s" % x.strip()[:160])
rep.append("\n完整 diff: _audit/_core_diff.txt")
io.open(os.path.join(HERE, "_diff_summary.txt"), "w", encoding="utf-8").write("\n".join(rep))
print("summary written: deleted=%d(exe %d) added=%d(exe %d)"
      % (len(minus), len([x for x in minus if code(x)]),
         len(plus), len([x for x in plus if code(x)])))
