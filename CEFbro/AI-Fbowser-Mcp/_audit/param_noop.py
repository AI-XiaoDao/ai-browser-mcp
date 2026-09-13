# -*- coding: utf-8 -*-
"""铁证级审计: 找出"只在 添加工具JSON 注册行里出现过、代码里从不出现"的参数名。

原理: 实现若要读取某个参数, 必然至少有一次该参数名的字符串字面量出现在
非注册代码中 (取文本/取整数/取数组/取对象成员/... 都需要字面量键名)。
若字面量仅出现在注册行 → 该参数在任何代码路径上都读不到 → AI 传它必然静默无效。
本判据不依赖"分支归属推断", 因此不受委托跟随/路由器等建模复杂度影响。
"""
import io, os, re, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import SRC
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

PROJ = ["main.wsv", "MCP_Server.wsv", "MCP_Stdio.wsv", "MCP_BrowserEvents.wsv",
        "MCP_Callbacks.wsv", "MCP_Server_VIP.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_Core.wsv", "MCP_Server_Form.wsv", "MCP_Server_System.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv",
        "MCP_Server_Utils.wsv", "MCP_Server_Reverse.wsv", "MCP_Kernel.wsv"]

# 逐行读全工程; 标记哪些行属于"注册行"
lines_all = []          # (file, lineno, text, is_registration_line)
for f in PROJ:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    for i, l in enumerate(io.open(p, encoding="utf-8").read().split("\n")):
        lines_all.append((f, i + 1, l, "添加工具JSON" in l))

# 参数名 -> 非注册行出现次数
nonreg_hits = collections.Counter()
for f, ln, l, isreg in lines_all:
    if isreg:
        continue
    for m in re.finditer(r'"([A-Za-z_][A-Za-z0-9_]*)"', l):
        nonreg_hits[m.group(1)] += 1

# 解析注册行, 取 schema 参数
ITEM = re.compile(r'属性项JSON\s*\(([^)]*)\)')
SINGLE = re.compile(r'单参数Schema文本\s*\(([^)]*)\)')


def split_args(s, start):
    depth, i, in_str, cur, args = 0, start, False, [], []
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\" and i + 1 < len(s):
                cur.append(s[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            else:
                cur.append(c)
        else:
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
                if depth > 1:
                    cur.append(c)
            elif c == ")":
                depth -= 1
                if depth == 0:
                    args.append("".join(cur)); return args, i
                cur.append(c)
            elif c == "," and depth == 1:
                args.append("".join(cur)); cur = []
            else:
                cur.append(c)
        i += 1
    return args, -1


def params_of(expr):
    out = []
    for RX in (ITEM, SINGLE):
        for m in RX.finditer(expr):
            a, _ = split_args("(" + m.group(1) + ")", 0)
            a = [x.strip() for x in a]
            if len(a) >= 2:
                nm = a[0].strip('"')
                tp = a[1].strip().strip('"')
                if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', nm):
                    out.append((nm, tp))
    return out


REG = collections.OrderedDict()
for f, ln, l, isreg in lines_all:
    if not isreg:
        continue
    m = re.search(r'添加工具JSON\s*\(', l)
    if not m:
        continue          # 方法定义行/注释里的 "添加工具JSON" 不含调用括号
    args, _ = split_args(l, m.end() - 1)
    if len(args) < 2:
        continue
    nm = args[0].strip().strip('"')
    if not re.fullmatch(r'[A-Za-z0-9_.\-]+', nm):
        continue
    REG[nm] = {"schema": args[2] if len(args) > 2 else "", "file": f, "line": ln}

print("=" * 100)
print("铁证级审计: 只在注册行出现、代码中从不出现的参数名")
print("=" * 100)
print("  注册工具 %d 个" % len(REG))
print()

findings = []
for tool, info in REG.items():
    for nm, tp in params_of(info["schema"]):
        if nonreg_hits[nm] == 0:
            findings.append((tool, nm, tp, info["file"], info["line"]))

print("─" * 100)
print("★ 必然失效的参数 (字面量仅出现在注册行, 全工程非注册代码 0 次) — %d 项" % len(findings))
print("─" * 100)
by_tool = collections.defaultdict(list)
for t, nm, tp, f, l in findings:
    by_tool[t].append((nm, tp, f, l))
for t in sorted(by_tool):
    items = by_tool[t]
    print("  %-40s %s" % (t, ", ".join("%s(%s)" % (n, y) for n, y, _, _ in items)))
    print("      %s" % ("%s:%d" % (items[0][2], items[0][3])))

print()
print("=" * 100)
print("并按『参数是否被其它工具共用』复核 (排除误报)")
print("=" * 100)
for t, nm, tp, f, l in findings:
    print("  %-38s %-14s 该名字在非注册代码中出现: %d 次" % (t, nm, nonreg_hits[nm]))

json.dump(findings, io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "_param_noop.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print()
print("saved _param_noop.json")
