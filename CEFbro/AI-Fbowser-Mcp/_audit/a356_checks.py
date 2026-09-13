# -*- coding: utf-8 -*-
r"""A3 + A5 + A6 — 路由 / 并发 / 返回 三项检查

A3 路由: 注册表(添加工具JSON) vs 实现分支 vs 命令注册表ID 三方 diff
A5 并发: 锁配对(方法内加/解锁平衡) + 可中断延时未传持锁标志的调用点
A6 返回: 声明返回类型但方法体内无任何 返回 语句
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

W = []
def w(s=""):
    W.append(s)

REG_LINE = re.compile(r'添加工具JSON\s*\(\s*"([^"]+)"')
ID_LINE = re.compile(r'置整数值\s*\(\s*"([^"]+)"\s*,\s*(\d+)')
# 注意: 不能用 '(?:如果|否则)\s*\(' 前缀 —— 形如
#   否则 (方法名 == "browser.fill_click" || 方法名 == "browser_fill_click")
# 的第二个比较前面是 '||', 会被漏掉 (A3 首版因此产生 16 条误报)
BRANCH = re.compile(r'(?:方法名|工具名)\s*==\s*"([A-Za-z0-9_.]+)"')

# ---------- 采集 ----------
reg, regline = {}, {}
for i, ln in enumerate(lines_of("MCP_Server.wsv")[0]):
    m = REG_LINE.search(ln)
    if m and m.group(1) not in reg:
        reg[m.group(1)] = i + 1
idmap = {}
for i, ln in enumerate(lines_of("MCP_Server.wsv")[0]):
    for m in ID_LINE.finditer(ln):
        idmap[m.group(1)] = int(m.group(2))

impl = {}          # tool(规范化: . -> _) -> [(file, line)]
for f in FILES:
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        for m in BRANCH.finditer(re.sub(r"//.*$", "", ln)):
            name = m.group(1).replace(".", "_")
            impl.setdefault(name, []).append((f, i + 1))

w("=" * 104)
w("A3 路由检查: 注册表 <-> 实现分支 <-> 命令注册表ID")
w("=" * 104)
w()
w("注册工具 %d 个 | 实现分支工具名 %d 个 | 命令注册表键 %d 个" % (len(reg), len(impl), len(idmap)))
w()
only_impl = sorted(set(impl) - set(reg))
only_reg = sorted(set(reg) - set(impl))
w("--- [A] 有实现分支但未在 添加工具JSON 注册 (客户端 tools/list 看不到) ---  共 %d" % len(only_impl))
for t in only_impl:
    loc = impl[t][0]
    has_id = "有命令注册表ID=%d" % idmap[t] if t in idmap else "无ID"
    w("   %-46s %s:%d   (%s)" % (t, loc[0], loc[1], has_id))
w()
w("--- [B] 已注册但无实现分支 (调用将走回退链或报未知命令) ---  共 %d" % len(only_reg))
for t in only_reg:
    w("   %-46s 注册于 MCP_Server.wsv:%d" % (t, reg[t]))
w()
# 短名/无前缀工具是否可达
w("--- [C] 无 browser_ 前缀的注册工具 (需靠短名映射或特殊路由可达) ---")
for t in sorted(reg):
    if not t.startswith("browser_"):
        w("   %-46s %s" % (t, "命令注册表ID=%d" % idmap[t] if t in idmap else "无ID"))

# ---------- A5 并发 ----------
w()
w("=" * 104)
w("A5 并发检查")
w("=" * 104)
w()
lock_delta = []
for f in FILES:
    for (i0, mname, sig, b0, b1) in find_methods(f):
        ls, _ = lines_of(f)
        plus = minus = 0
        for k in range(b0, b1 + 1):
            code = re.sub(r"//.*$", "", ls[k])
            plus += len(re.findall(r"\.加锁\s*\(\s*\)", code))
            minus += len(re.findall(r"\.解锁\s*\(\s*\)", code))
        if plus != minus:
            lock_delta.append((f, i0 + 1, mname, plus, minus))
w("--- [A5-1] 方法内 加锁/解锁 次数不平衡 ---  共 %d" % len(lock_delta))
w("    (注意: '加锁一次->互斥分支各解锁一次' 是合法模式, 需人工确认)")
for (f, l, m, p, q) in lock_delta:
    w("   %-26s:%-6d %-34s 加锁%d 解锁%d" % (f, l, m, p, q))

w()
w("--- [A5-2] MCP可中断延时 调用点未显式传 是否持锁 (默认真 -> 会解锁) ---")
bad_delay = []
for f in FILES:
    ls, _ = lines_of(f)
    for i, ln in enumerate(ls):
        code = re.sub(r"//.*$", "", ln)
        for m in re.finditer(r"MCP可中断延时\s*\(([^)]*)\)", code):
            args = m.group(1)
            if args.count(",") < 1:
                bad_delay.append((f, i + 1, ln.strip()[:100]))
w("   共 %d 处 (只传了毫秒, 未传 是否持锁 → 走默认 真)" % len(bad_delay))
for (f, l, t) in bad_delay:
    w("   %-26s:%-6d %s" % (f, l, t))

# ---------- A6 返回 ----------
w()
w("=" * 104)
w("A6 返回检查: 声明返回类型但方法体内 0 个 返回 语句")
w("=" * 104)
w()
noret = []
for f in FILES:
    ls, _ = lines_of(f)
    for (i0, mname, sig, b0, b1) in find_methods(f):
        merged = ls[i0]
        j = i0 + 1
        while j < len(ls) and ">" not in merged:
            merged += ls[j]; j += 1
        if "类型" not in merged:
            continue
        if "定义事件" in merged:
            continue
        body = "\n".join(re.sub(r"//.*$", "", ls[k]) for k in range(b0, b1 + 1))
        if not re.search(r"\b返回\s*\(", body):
            noret.append((f, i0 + 1, mname, sig[:80]))
w("   共 %d 个 (排除 定义事件)" % len(noret))
for (f, l, m, s) in noret:
    w("   %-26s:%-6d %s" % (f, l, s))

p = out_report("report_A356.txt", "\n".join(W))
print("written", p)
print("A3: 未注册实现 %d | 注册无实现 %d" % (len(only_impl), len(only_reg)))
print("A5: 锁不平衡 %d | 延时缺持锁标志 %d" % (len(lock_delta), len(bad_delay)))
print("A6: 无返回语句 %d" % len(noret))
