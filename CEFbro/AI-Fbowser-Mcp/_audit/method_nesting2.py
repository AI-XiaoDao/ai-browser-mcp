# -*- coding: utf-8 -*-
"""方法嵌套检查 v2 —— 改用**局部**判据, 不依赖全局花括号深度。

v1(全局深度)的缺陷: `@` 嵌入式 C++ 行 / 行内 `//` 注释 / 跨行字符串都会污染深度,
导致 depth 变成负数这种不可能的结果 -> 大量假阳性(实测 9 处)。

v2 判据(局部、抗污染):
  行首 `方法 X <` 声明**合法**当且仅当向上回溯到的第一个"实质行"是:
    (a) 类的开始 `{`(即前面有 `类 X <...>`), 或
    (b) 上一个方法/定义的结束 `}`
  否则说明它被写进了某个方法体内 -> 报"方法嵌套"。
局部判据只依赖相邻行, 不受远处 `@`/注释/字符串影响。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
PROJ = ["main.wsv", "MCP_Server.wsv", "MCP_Stdio.wsv", "MCP_BrowserEvents.wsv",
        "MCP_Callbacks.wsv", "MCP_Server_VIP.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_Core.wsv", "MCP_Server_Form.wsv", "MCP_Server_System.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv",
        "MCP_Server_Utils.wsv", "MCP_Server_Reverse.wsv", "MCP_Kernel.wsv"]

METHOD = re.compile(r'^\s*方法\s+[\u4e00-\u9fff]')
CLASS = re.compile(r'^类\s+')


def sub_starts(line):
    """该方法声明是否为"子成员声明": @开头(嵌入式/属性)行 / 参数行 / 方法行 / 注释行 都算同一块的延续。"""
    s = line.strip()
    if s == "":
        return False
    if s.startswith("@"):
        return True
    if s.startswith("参数") or s.startswith("返回值注释") or s.startswith("注释"):
        return True
    if s.startswith("方法 ") or s.startswith("变量 ") or s.startswith("常量 "):
        return True
    return False


total_bad = 0
print("=" * 90)
print("方法嵌套检查 v2 (局部判据: 方法声明前一个实质行必须是 类开括号 或 上一方法闭合)")
print("=" * 90)
for f in PROJ:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    lines = io.open(p, encoding="utf-8").read().split("\n")
    bad = []
    for i, l in enumerate(lines):
        if not METHOD.match(l):
            continue
        # 向上回溯第一个"实质行"
        j = i - 1
        prev = None
        while j >= 0:
            s = lines[j].strip()
            if s == "":
                j -= 1
                continue
            if s.startswith("#"):
                j -= 1
                continue
            prev = s
            break
        if prev is None:
            bad.append((i + 1, "文件开头"))
            continue
        # 合法前驱: 类开括号 / 上一方法闭合 / 类级成员声明 / 上一方法(无方法体)的参数行
        ok = prev in ("{", "}", "};")
        if not ok:
            for pfx in ("变量 ", "常量 ", "参数 ", "返回值注释", "类 "):
                if prev.startswith(pfx):
                    ok = True
                    break
        if not ok:
            bad.append((i + 1, "前一行是: %s" % prev[:40]))
    if bad:
        total_bad += len(bad)
        print("  !! %-26s 可疑 %d 处" % (f, len(bad)))
        for ln, why in bad[:6]:
            print("        L%-6d %s" % (ln, why))
    else:
        print("  OK %-26s 全部方法均在类体内" % f)
print()
print("★ 可疑合计: %d" % total_bad)
