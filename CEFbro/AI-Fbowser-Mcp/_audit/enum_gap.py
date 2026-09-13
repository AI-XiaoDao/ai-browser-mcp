# -*- coding: utf-8 -*-
"""第三类缺陷扫描: 「实现里有 action 取值, 但注册行的 schema 枚举里没列」——AI 猜不到的能力。

做法:
  1) 在每个 `否则 (方法名 == "tool") { ... }` 分支体内, 收集 `action == "x"` 的取值集合
     (同时收集上游 `action = 取文本(参数JSON,"action")` 所在的工具分组)
  2) 取该工具注册行文本, 看每个值是否作为子串出现
  3) 输出差集

局限(如实标注): 若某工具的 action 链写在"方法名分组"里(一个分支体覆盖多个工具),
本脚本按分支体归属, 可能与注册工具名不一一对应 -> 结果作为**线索**而非最终结论。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

TXT = {}
for f in sorted(os.listdir(SRC)):
    if f.endswith(".wsv") and ".~vbak" not in f:
        TXT[f] = io.open(os.path.join(SRC, f), encoding="utf-8").read()

CORE = TXT.get("MCP_Server_Core.wsv", "")
SERVER = TXT.get("MCP_Server.wsv", "")

# 工具分支:  否则 (方法名 == "tool") { ... }   (取到配对花括号)
BRANCH = re.compile(r'(?:否则|如果)\s*\(\s*方法名\s*==\s*"([A-Za-z0-9_.\-]+)"\s*\)\s*\{')
ACT = re.compile(r'action\s*==\s*"([^"]+)"')


def body_at(text, i):
    depth, j, in_str = 0, i, False
    while j < len(text):
        c = text[j]
        if in_str:
            if c == "\\":
                j += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[i:j + 1]
        j += 1
    return ""


REG = {}
for m in re.finditer(r'添加工具JSON\s*\(\s*"([A-Za-z0-9_.\-]+)"', SERVER):
    name = m.group(1)
    # 取该调用的完整参数直到行尾 (注册均为单行)
    line_end = SERVER.find("\n", m.start())
    REG[name] = SERVER[m.start():line_end]

rows = []
for m in BRANCH.finditer(CORE):
    tool = m.group(1)
    body = body_at(CORE, m.end() - 1)
    acts = sorted(set(ACT.findall(body)))
    if not acts:
        continue
    if tool not in REG:
        continue
    reg = REG[tool]
    missing = [a for a in acts if a not in reg]
    if missing:
        rows.append((tool, missing, len(acts)))

print("=" * 100)
print("第三类缺陷: 实现有 action 取值, 但注册行 schema 枚举文本里未出现")
print("=" * 100)
print("  扫描到带 action 链且有注册的工具分支: %d 个" % sum(1 for _ in BRANCH.finditer(CORE)))
print("  其中存在『枚举未列出』的: %d 个" % len(rows))
print()
for tool, miss, tot in rows:
    print("  %-28s 共 %d 个 action, 未列出 %d 个:" % (tool, tot, len(miss)))
    print("        %s" % ", ".join(miss))
