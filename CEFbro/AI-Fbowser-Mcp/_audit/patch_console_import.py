# -*- coding: utf-8 -*-
"""把 `import _console`(控制台 UTF-8 兜底)补到 _audit 下所有会 print 的脚本里。

## 为什么值得批处理
同一个坑本会话已经踩了 5 次(台账 --status、两个验证脚本、breaker 工具、以及本轮 fastcheck):
项目消息里含 `⏱`(U+23F1)、`⚠`(U+26A0) 等字符, 而 Windows 控制台是 GBK 代码页 ->
`print` 抛 UnicodeEncodeError -> **脚本在"打印结论"这一步崩掉**。
最危险的不是崩, 而是**崩在打印会把已经测出来的结论一起吞掉**: 本轮 `fastcheck` 就是
"结果统计没打出来 + 退出码 1", 看起来像"快检失败", 其实只是打印崩了 —— 直接误导判断。

## 做法(保守)
- 只给**同时满足**的脚本打补丁: ① 含 `print(`; ② 尚未 import _console; ③ 已 import sys(否则先补 sys)。
- 在最后一个顶层 import 之后插入:
      import os as _os, sys as _sys          # 仅当缺 sys 时
      sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
      import _console  # noqa: F401
- 改完用 py_compile 逐个校验语法, 任一失败即中止(不留下坏脚本)。
- 幂等: 已有 import _console 的跳过, 可反复运行。
"""
import io
import os
import py_compile
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401

SKIP = {"_console.py"}
imports = ["import sys", "import os", "import io", "import json", "import time",
           "import re", "import glob", "import urllib.request", "import subprocess"]

patched, skipped, failed = [], [], []
for name in sorted(os.listdir(HERE)):
    if not name.endswith(".py") or name in SKIP:
        continue
    p = os.path.join(HERE, name)
    try:
        s = io.open(p, encoding="utf-8").read()
    except Exception as ex:
        failed.append("%s(读取失败:%s)" % (name, ex))
        continue
    if "print(" not in s:
        continue
    if "import _console" in s:
        skipped.append(name)
        continue

    lines = s.split("\n")
    need_sys = not re.search(r"^import sys$|^import sys,|, sys|sys\.", s, re.M)
    # 找最后一个顶层 import 行的位置
    last = -1
    for i, l in enumerate(lines[:80]):
        if re.match(r"^(import |from )", l):
            last = i
    if last < 0:
        failed.append("%s(找不到 import 区)" % name)
        continue

    ins = []
    if need_sys:
        ins.append("import os as _os")
        ins.append("import sys as _sys")
        ins.append("_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))")
        ins.append("import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)")
    else:
        ins.append("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))"
                   if "import os" in s else
                   "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))")
        ins.append("import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)")
    new = lines[:last + 1] + ins + lines[last + 1:]
    txt = "\n".join(new)

    # 先语法校验再落盘
    tmp = os.path.join(tempfile.gettempdir(), "_chk_%s" % name)
    io.open(tmp, "w", encoding="utf-8").write(txt)
    try:
        py_compile.compile(tmp, cfile=tmp + "c", doraise=True)
    except Exception as ex:
        failed.append("%s(语法校验失败:%s)" % (name, str(ex)[:80]))
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(txt)
    patched.append(name)

print("已补 _console: %d 个" % len(patched))
for n in patched:
    print("   + %s" % n)
print("已有(跳过): %d 个" % len(skipped))
if failed:
    print("!! 未处理: %s" % "; ".join(failed))
    sys.exit(1)
