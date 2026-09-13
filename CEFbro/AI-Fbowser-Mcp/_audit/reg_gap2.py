# -*- coding: utf-8 -*-
"""工具注册一致性 (全 16 个工程源文件; 修正分支识别, 只认分派变量比较)

分支识别: 只接受 左操作数 属于分派变量集合 的字符串比较, 例如
  方法名 == "browser_x"   /   否则 (方法名 == "a" || 方法名 == "b")
不把 格式=="png" 这类业务值比较当成工具分支。
"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

# 工程实际编译的 16 个源文件 (来自 AI-Fbowser-Mcp.vprj file1..file16)
PROJ = ["main.wsv", "MCP_Server.wsv", "MCP_Stdio.wsv", "MCP_BrowserEvents.wsv",
        "MCP_Callbacks.wsv", "MCP_Server_VIP.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_Core.wsv", "MCP_Server_Form.wsv", "MCP_Server_System.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv",
        "MCP_Server_Utils.wsv", "MCP_Server_Reverse.wsv", "MCP_Kernel.wsv"]

DISPATCH_VARS = ["方法名", "工具名", "命令名", "动作", "name", "tool", "toolName", "cmd"]
VAR_ALT = "|".join(DISPATCH_VARS)
BRANCH = re.compile(r'(?:%s)\s*==\s*"([A-Za-z0-9_.\-]{3,})"' % VAR_ALT)
REG = re.compile(r'添加工具JSON\s*\(\s*"([^"]+)"')
REG2 = re.compile(r'命令注册表\.置整数值\s*\(\s*"([^"]+)"')

branches, regs, regtbl = {}, {}, {}
for f in PROJ:
    if not os.path.exists(os.path.join(SRC, f)):
        print("!! 缺失源文件: %s" % f)
        continue
    for i, l in enumerate(lines_of(f)[0]):
        if l.lstrip().startswith("@"):
            continue
        for m in BRANCH.finditer(l):
            branches.setdefault(m.group(1).replace(".", "_"), []).append((f, i + 1))
        for m in REG.finditer(l):
            regs.setdefault(m.group(1), []).append((f, i + 1))
        for m in REG2.finditer(l):
            regtbl.setdefault(m.group(1), []).append((f, i + 1))

print("=" * 100)
print("工具注册一致性 (全 16 个工程源文件)")
print("=" * 100)
print("  添加工具JSON 注册数(暴露给AI): %d" % len(regs))
print("  命令注册表(内部命令表)条目:    %d" % len(regtbl))
print("  分派分支数(分派变量==...):     %d" % len(branches))
print()

noimpl = sorted(set(regs) - set(branches))
print("-" * 100)
print("A. 已注册但无分派分支 (AI 能调用但一定失败) — %d" % len(noimpl))
print("-" * 100)
for n in noimpl:
    also = "  [在命令注册表]" if n in regtbl else ""
    print("  %-38s %s%s" % (n, ", ".join("%s:%d" % ab for ab in regs[n][:2]), also))

toolish = {k: v for k, v in branches.items() if ("_" in k or k.startswith("browser"))}
unreg = sorted(set(toolish) - set(regs))
print()
print("-" * 100)
print("B. 有分派分支但未注册 (AI 完全看不到) — %d" % len(unreg))
print("-" * 100)
for n in unreg:
    inreg = "  [在命令注册表]" if n in regtbl else "  [!! 无内部注册]"
    print("  %-38s %s%s" % (n, ", ".join("%s:%d" % ab for ab in toolish[n][:2]), inreg))

print()
print("-" * 100)
print("C. 命令注册表有条目但既未注册也无分派 (内部死条目)")
print("-" * 100)
dead = sorted(set(regtbl) - set(regs) - set(branches))
print("  数量: %d" % len(dead))
for n in dead[:25]:
    print("  %-38s %s" % (n, ", ".join("%s:%d" % ab for ab in regtbl[n][:1])))
if len(dead) > 25:
    print("  ... 其余 %d 条" % (len(dead) - 25))

io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_reg_gap.json"), "w",
        encoding="utf-8").write(json.dumps(
    {"noimpl": noimpl, "unreg": unreg, "dead": dead,
     "regs": {k: v for k, v in regs.items()},
     "branches": {k: v for k, v in toolish.items()}}, ensure_ascii=False, indent=1))
print()
print("saved _reg_gap.json")
