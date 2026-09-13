# -*- coding: utf-8 -*-
"""校验 method_nesting2 的判据: 用**精确构造**的坏状态测它。

上一次校验失败的原因: 用正则 `.*?\\n    \\}\\n`(re.S) 提取 helper2 时,
非贪婪匹配停在了 helper2 **内部第一个 `}`**, 提取到的片段不完整 -> 坏状态根本没造对。
本次改用**花括号配对**精确定位 helper2 的起止, 再把整块搬到 helper1 的 `返回 (真)` 之后
(即 helper1 方法体内), 必然构成"方法嵌套"。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRCDIR = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
MAIN = os.path.join(SRCDIR, "main.wsv")
lines = io.open(MAIN, encoding="utf-8").read().split("\n")


def line_of(sub, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip().startswith(sub):
            return i
    return -1


def brace_end(start):
    """从 start 行起做花括号配对, 返回闭合行索引。"""
    depth, i, in_str, started = 0, start, False, False
    while i < len(lines):
        for c in lines[i]:
            if in_str:
                continue
            if c == '"':
                in_str = True
        # 简化: 逐字符扫描该行(忽略字符串内的括号)
        depth2, instr = 0, False
        for c in lines[i]:
            if instr:
                continue
            if c == '"':
                instr = True
            elif c == "{":
                depth2 += 1
            elif c == "}":
                depth2 -= 1
        depth += depth2
        if depth > 0:
            started = True
        if started and depth == 0:
            return i
        i += 1
    return -1


METHOD = re.compile(r'^\s*方法\s+[\u4e00-\u9fff]')


def check(text_lines):
    bad = []
    for i, l in enumerate(text_lines):
        if not METHOD.match(l):
            continue
        j, prev = i - 1, None
        while j >= 0:
            s = text_lines[j].strip()
            if s == "" or s.startswith("#"):
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
            bad.append((i + 1, "前一行: " + prev[:36]))
    return bad


h1 = line_of("方法 记录应用事件渲染侧 <")
h2 = line_of("方法 记录应用事件渲染侧_按浏览器 <")
print("helper1 起 L%d, helper2 起 L%d" % (h1 + 1, h2 + 1))
h1_end = brace_end(h1)
h2_end = brace_end(h2)
print("helper1 止 L%d, helper2 止 L%d" % (h1_end + 1, h2_end + 1))

# 精确切出 helper2 整块
block = lines[h2:h2_end + 1]
rest = lines[:h2] + lines[h2_end + 1:]

# 把 helper2 插到 helper1 的 "返回 (真)" 之后(仍在 helper1 体内)
ins = None
for i in range(h1, h1_end + 1):
    if rest[i].strip() == "返回 (真)":
        ins = i + 1
        break
print("插入点: helper1 内 '返回 (真)' 之后 -> L%s" % (ins + 1 if ins else "未找到"))

if ins is None:
    print("!! 构造失败")
else:
    bad_lines = rest[:ins] + block + rest[ins:]
    rg = check(lines)
    rb = check(bad_lines)
    print()
    print("  正常 main.wsv            -> 可疑 %d 处" % len(rg))
    print("  精确构造的坏状态          -> 可疑 %d 处" % len(rb))
    for ln, why in rb[:5]:
        print("        L%-6d %s" % (ln, why))
    print()
    if len(rb) > len(rg):
        print("  ✅ 检测器有效: 能抓到方法嵌套")
    else:
        print("  ❌ 检测器无效: 抓不到 -> 判据必须重做")
