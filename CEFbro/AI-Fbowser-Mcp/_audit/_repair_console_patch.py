# -*- coding: utf-8 -*-
"""修复并完成上一版 `patch_console_import.py` 的两处自身缺陷。

## 我上一版犯了什么错(必须记录)
1. **插入了不自洽的代码**: 当目标脚本已 import sys 时, 我插入的是
   `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` —— 但它**假设 os 已被 import**。
   `fastcheck.py` 恰好没有 import os, 于是插入后立刻 `NameError: name 'os' is not defined`,
   **把快检(项目的主力回归测试)直接弄坏了**。而且我当时那句三元表达式两个分支写的是同一个字符串,
   等于"看起来做了判断, 实际什么都没判断"。
   → 教训: 批量改写他人脚本时, 插入的代码必须**完全自洽**(不假设任何既有名字已存在)。
2. **漏了带 BOM 的脚本**: 我用 `^(import |from )` 找 import 区, 而这些脚本首行是
   `\ufeffimport io,os`(UTF-8 BOM 在行首), 正则匹配不到 -> 37 个脚本被记成"找不到 import 区"。
   → 正确处理: 读的时候用 utf-8-sig(或手工跳过 BOM), 写回时保持原编码。

## 本脚本做三件事
A. 把上一版插入的**不自洽片段**替换为自洽片段(带 _os/_sys 别名, 不依赖目标文件既有名字);
B. 给那 37 个带 BOM 且仍缺 `import _console` 的脚本补上(保持 BOM);
C. 每个文件改前 py_compile 校验, 失败则不改 —— 不留下坏脚本。
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

BAD = ("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
       "import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)")
GOOD = ("import os as _os, sys as _sys\n"
        "_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))\n"
        "import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)")

repaired, bom_added, failed = [], [], []
for name in sorted(os.listdir(HERE)):
    if not name.endswith(".py") or name in ("_console.py", "_repair_console_patch.py"):
        continue
    p = os.path.join(HERE, name)
    raw = io.open(p, "rb").read()
    has_bom = raw[:3] == b"\xef\xbb\xbf"
    try:
        s = raw.decode("utf-8-sig")
    except Exception as ex:
        failed.append("%s(解码失败:%s)" % (name, ex))
        continue
    orig = s
    changed = False

    # A. 替换不自洽片段
    if BAD in s:
        s = s.replace(BAD, GOOD)
        changed = True
        repaired.append(name)

    # B. 带 BOM 且仍缺 _console 的, 在其首个 import 之后插入自洽片段
    if "print(" in s and "import _console" not in s:
        lines = s.split("\n")
        last = -1
        for i, l in enumerate(lines[:120]):
            if re.match(r"^\s*(import |from )", l):
                last = i
        if last < 0:
            failed.append("%s(仍找不到 import 区)" % name)
            continue
        lines = lines[:last + 1] + GOOD.split("\n") + lines[last + 1:]
        s = "\n".join(lines)
        changed = True
        bom_added.append(name)

    if not changed or s == orig:
        continue
    # C. 先语法校验
    tmp = os.path.join(tempfile.gettempdir(), "_fix_%s" % name)
    io.open(tmp, "w", encoding="utf-8").write(s)
    try:
        py_compile.compile(tmp, cfile=tmp + "c", doraise=True)
    except Exception as ex:
        failed.append("%s(语法校验失败:%s)" % (name, str(ex)[:70]))
        continue
    out = ("\ufeff" + s) if has_bom else s
    io.open(p, "w", encoding="utf-8", newline="\n").write(out)

print("A 修复不自洽片段: %d 个" % len(repaired))
print("B 补带BOM脚本: %d 个" % len(bom_added))
if failed:
    print("!! 未处理 %d 个: %s" % (len(failed), "; ".join(failed[:12])))

# 自检: 全目录不应再出现不自洽片段; 且不应再有"缺 _console 但会 print"的脚本
rest_bad, rest_missing = [], []
for name in sorted(os.listdir(HERE)):
    if not name.endswith(".py"):
        continue
    s = io.open(os.path.join(HERE, name), "rb").read().decode("utf-8-sig", "replace")
    if BAD in s:
        rest_bad.append(name)
    if "print(" in s and "import _console" not in s:
        rest_missing.append(name)
print("自检: 残留不自洽片段 %d 个 %s" % (len(rest_bad), rest_bad[:5]))
print("自检: 仍缺 _console 且会 print 的脚本 %d 个 %s" % (len(rest_missing), rest_missing[:8]))
sys.exit(1 if (rest_bad or failed) else 0)
