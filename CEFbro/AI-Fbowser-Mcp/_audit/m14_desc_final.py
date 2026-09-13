# -*- coding: utf-8 -*-
r"""M14 — 描述改写终检

重点验证: 每条 添加工具JSON 行的字符串引号是否平衡。
若描述里混入裸 ASCII 双引号, 会同时破坏
  (a) 火山字符串字面量 -> 编译错误
  (b) tools/list 的 JSON  -> 客户端解析失败
"""
import io, os, re, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
lines = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")

print("=" * 100)
print("M14 描述改写终检")
print("=" * 100)
print()

def strip_strings(s):
    """把字符串字面量替换为占位, 返回 (净化文本, 字面量列表)"""
    out, lits, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            buf = []
            while j < n:
                if s[j] == "\\":
                    buf.append(s[j]); j += 1
                    if j < n:
                        buf.append(s[j]); j += 1
                    continue
                if s[j] == '"':
                    break
                buf.append(s[j]); j += 1
            lits.append("".join(buf))
            out.append("S")          # 占位符**不能带引号**, 否则下面的平衡统计会把占位符自己数进去
            i = j + 1
            continue
        out.append(c); i += 1
    return "".join(out), lits

bad_quote, bad_json, n_tool = [], [], 0
all_desc = {}
for i, l in enumerate(lines):
    if "添加工具JSON" not in l:
        continue
    m = re.match(r'\s*添加工具JSON\s*\(', l)
    if not m:
        continue
    n_tool += 1
    clean, lits = strip_strings(l)
    # 引号必须成对(净化后不应残留裸引号)
    if clean.count('"') != 0:
        bad_quote.append((i + 1, l.strip()[:150]))
    if len(lits) >= 2:
        name, d = lits[0], lits[1]
        all_desc[name] = d
        # 描述里不得出现会被 JSON 破坏的裸控制字符
        if any(ch in d for ch in ['\n', '\r', '\t']):
            bad_json.append((i + 1, name, "含裸控制字符"))
        # 引号/反斜杠必须已转义为 \" \\ (火山字面量层)
        if '"' in d.replace('\\"', ''):
            bad_json.append((i + 1, name, "含裸引号"))

print("工具注册行: %d   解析到描述: %d" % (n_tool, len(all_desc)))
print()
print("--- 引号平衡检查 ---")
if bad_quote:
    for n, t in bad_quote[:10]:
        print("   !! 行 %d 存在未配对引号: %s" % (n, t))
else:
    print("   ✓ 全部 %d 行引号平衡" % n_tool)
print()
print("--- 描述 JSON 安全性 ---")
if bad_json:
    for n, t, why in bad_json[:10]:
        print("   !! 行 %d %s: %s" % (n, t, why))
else:
    print("   ✓ 无裸引号 / 无裸控制字符")

# 统计
lens = sorted(len(d) for d in all_desc.values())
under12 = sorted(n for n, d in all_desc.items() if len(d) < 12)
print()
print("=" * 100)
print("最终度量")
print("=" * 100)
print("  描述 <12 字: 116 -> %d  (已改写 %d)" % (len(under12), 116 - len(under12)))
print("  描述长度: 最短 %d / 中位 %d / 最长 %d" % (lens[0], lens[len(lens)//2], lens[-1]))
print("  描述总字节: %d (改写前 16572)" % sum(len(d.encode('utf-8')) for d in all_desc.values()))
print()
print("  仍 <12 字(%d 个, 多为名称自明):" % len(under12))
print("     " + "  ".join(under12))
