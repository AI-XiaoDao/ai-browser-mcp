# -*- coding: utf-8 -*-
"""二分第三步: 怀疑点是**局部文本变量的 `值 = ""` 初始化**。

依据: 全项目里 `值 = ""` 只出现在 `公开 静态` 的成员变量上; 我这两处是**局部变量**
(`变量 ccBad <类型 = 文本型 值 = ""`), 全项目没有先例 —— 方言里局部变量可能不接受 `值 =`。
本步只改这两处(去掉 ` 值 = ""`), 其它一律不动, 语法检查:
  · 通过 => 确认就是它;
  · 仍失败 => 继续在分支体里找。
"""
import io
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

CORE = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
BAK = os.path.join(HERE, "_core_step3.bak")
shutil.copy2(CORE, BAK)
COMPILER = r"E:\HSPC\bin\x64\voldev_awp.exe"
VSLN = "AI-Fbowser-Mcp.vsln"

try:
    s = io.open(CORE, encoding="utf-8").read()
    a = s.count('变量 ccBad <类型 = 文本型 值 = ""')
    b = s.count('变量 ccTypeBad <类型 = 文本型 值 = ""')
    print("改前: ccBad=%d ccTypeBad=%d" % (a, b))
    s = s.replace('变量 ccBad <类型 = 文本型 值 = ""', '变量 ccBad <类型 = 文本型>')
    s = s.replace('变量 ccTypeBad <类型 = 文本型 值 = ""', '变量 ccTypeBad <类型 = 文本型>')
    io.open(CORE, "w", encoding="utf-8", newline="\n").write(s)
    p = subprocess.run([COMPILER, "@compile", VSLN, "/c"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    errs = [l.strip() for l in out.splitlines() if "错误:" in l]
    print("退出码=%s 错误行=%d" % (p.returncode, len(errs)))
    for e in errs[:4]:
        print("   %s" % e[:150])
    print("\n结论: %s" % ("确认: 局部文本变量不能写 `值 = \"\"`" if len(errs) == 0
                          else "不是它, 需继续查"))
finally:
    shutil.copy2(BAK, CORE)
    print("已恢复 Core 原文件(未保留本步改动)")
