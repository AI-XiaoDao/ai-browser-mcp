# -*- coding: utf-8 -*-
"""修复 register_and_warn.py 造成的 6 行描述损坏(警告被插进字符串中部 + 描述重复)。

## 事故复盘
我用 `re.sub` + 正则 `(添加工具JSON \\("(?P<tool>...)", ")(?P<desc>(?:[^"\\\\]|\\\\.)*)(", (?:多属性...|...) \\()` 去
"在原描述末尾插入警告"。结果是 group(2) **多吃了**跨过 `", 多属性Schema文本 (` 之前的更多内容,
替换后又把残留片段拼回去, 于是出现"警告插在中间 + 描述重复 + `", 多属性Schema文本 (` 丢失"的坏行,
编译器报 6 个 "字符串常量无效位置"。

**教训**: 对方言/转义规则不完全掌握时, **不要用正则去改字符串字面量的边界** ——
应改为"按已知锚点做确定性的字符串插入"(本脚本就是这么修的), 并在写前先打印将要发生的改动。

## 修法
以本轮开始前的备份行(确定正确, 含原始描述)为基准, 用 `line.index('", 多属性Schema文本 (')`
定位描述收尾引号, 在它**之前**插入警告文本。不解析、不猜测引号配对。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CUR = os.path.join(ROOT, "src", "MCP_Server.wsv")
BAK = os.path.join(ROOT, "备份", "11个幽灵能力补齐-写入前", "MCP_Server.wsv")

WARN = (" | **警告: 本工具走内核级注入, 实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具"
        "都会超时/退化, 连 browser_status 都可能挂), 必须重启 AI-Fbowser-Mcp.exe 才能恢复;"
        "如后续还要用 CDP 类工具, 请改用 CDP 版: browser_mouse_click / browser_mouse_move / "
        "browser_mouse_wheel / browser_key_event")

TOOLS = ["browser_vip_mouse_click", "browser_vip_mouse_move", "browser_vip_mouse_wheel",
         "browser_vip_key_press", "browser_vip_key_release", "browser_vip_key_click"]

bak = io.open(BAK, encoding="utf-8").read().split("\n")
cur = io.open(CUR, encoding="utf-8").read().split("\n")

TAIL = '", 多属性Schema文本 ('
fixed = 0
for t in TOOLS:
    key = '添加工具JSON ("%s", "' % t
    bi = [i for i, l in enumerate(bak) if l.startswith("        " + key.strip()) or key in l]
    if len(bi) != 1:
        print("!! 备份中 %s 定位到 %d 行(应 1) -> 中止" % (t, len(bi)))
        sys.exit(2)
    orig = bak[bi[0]]
    p = orig.index(TAIL)
    good = orig[:p] + WARN + orig[p:]

    ci = [i for i, l in enumerate(cur) if key in l]
    if len(ci) != 1:
        print("!! 当前文件中 %s 定位到 %d 行(应 1) -> 中止" % (t, len(ci)))
        sys.exit(2)
    bad = cur[ci[0]]
    print("%-26s 行 %d: 坏行长度 %d -> 修复为 %d" % (t, ci[0] + 1, len(bad), len(good)))
    assert bad != good, "该行已正确, 无需修复"
    cur[ci[0]] = good
    fixed += 1

io.open(CUR, "w", encoding="utf-8", newline="\n").write("\n".join(cur))
print("已修复 %d 行" % fixed)

# 自检: 每行必须恰好 1 个警告、恰好 1 个 schema 头、且不再有重复描述
chk = io.open(CUR, encoding="utf-8").read().split("\n")
bad = 0
for t in TOOLS:
    line = [l for l in chk if '添加工具JSON ("%s", "' % t in l][0]
    n_warn = line.count("CDP 通道在本会话内失效")
    n_schema = line.count("多属性Schema文本 (")
    n_tool = line.count('添加工具JSON ("%s"' % t)
    ok = (n_warn == 1 and n_schema == 1 and n_tool == 1)
    print("自检 %-26s 警告=%d schema=%d 注册=%d %s"
          % (t, n_warn, n_schema, n_tool, "OK" if ok else "!! 异常"))
    if not ok:
        bad += 1
print("OK" if bad == 0 else "!! %d 行仍异常" % bad)
sys.exit(1 if bad else 0)
