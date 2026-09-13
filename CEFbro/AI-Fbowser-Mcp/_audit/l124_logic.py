# -*- coding: utf-8 -*-
r"""L1/L2/L4 — 逻辑缺陷检测（第二轮）

L1 读取后被丢弃: 局部变量由 `yyjson取X (参数JSON,"key")` 赋值, 但此后从未被使用
                  -> 参数"读了等于没读"(A2 只查"从未读取", 查不出这一类)
L2 无条件成功  : 紧跟 SDK 调用之后的 `返回 (...命令成功...)`, 中间没有任何结果/存在性判断
                  -> 选择器未命中/调用失败也报成功(前任 §3.5 只在 Form 里发现 6 处)
L4 缺省与 0 不可区分: `X = yyjson取整数(...)` 后 `如果 (X == 0) { X = 默认 }`,
                  而 schema 描述里写明 "0=..." 有别的含义
"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

W = []
def w(s=""):
    W.append(s)

METHODS = []
for f in FILES:
    for (i0, mname, sig, b0, b1) in find_methods(f):
        METHODS.append((f, mname, i0 + 1, b0, b1))

# ============ L1 读取后被丢弃 ============
w("=" * 104)
w("L1 参数读取后从未使用 (局部变量由 yyjson取X 赋值, 之后再无引用)")
w("=" * 104)
w()
dead = []
for (f, mname, mline, b0, b1) in METHODS:
    ls, _ = lines_of(f)
    decl = {}
    for k in range(b0, b1 + 1):
        m = re.match(r"\s*变量\s+(\S+)\s*<", ls[k])
        if m:
            decl[m.group(1)] = k
    for name, dk in decl.items():
        # 找出该变量在声明后被赋值为 参数读取 的行
        assign_lines = []
        for k in range(dk, b1 + 1):
            code = re.sub(r"//.*$", "", ls[k])
            if re.search(re.escape(name) + r"\s*=\s*[\w\.]*(yyjson取|取对象|取数组)", code):
                assign_lines.append(k)
        if not assign_lines:
            continue
        # 统计该变量在 method 内的全部出现次数(含声明行)
        cnt = 0
        for k in range(b0, b1 + 1):
            code = re.sub(r"//.*$", "", ls[k])
            cnt += len(re.findall(r"\b" + re.escape(name) + r"\b", code))
        # 出现次数 <= 声明1 + 赋值1 = 2  => 赋值后从未被读
        if cnt <= 1 + len(assign_lines):
            key = ""
            km = re.search(r'"([^"]+)"', re.sub(r"//.*$", "", ls[assign_lines[0]]))
            if km:
                key = km.group(1)
            dead.append((f, mline, mname, name, key, decl[name] + 1, assign_lines[0] + 1))
w("共 %d 处" % len(dead))
for (f, ml, mname, name, key, dl, al) in dead:
    w("   %-24s:%-6d %-34s 变量 %-22s 键 %-18s (声明%d 赋值%d)"
      % (f, ml, mname, name, key or "-", dl, al))

# ============ L2 无条件成功 ============
w()
w("=" * 104)
w("L2 调用后无判断即返回成功 (选择器未命中/调用失败也报成功)")
w("=" * 104)
w()
SUCCESS = re.compile(r'返回\s*\(\s*(?:MCP_响应构建\.)?(?:命令成功|命令成功_原始JSON|构建简单JSON|构建标准成功JSON)')
GUARD = re.compile(r'如果|否则|返回\s*\(\s*(?:MCP_响应构建\.)?(?:命令失败|构建标准失败JSON)|是否为空|是否有效|元素是否存在|success|成功')
uncond = []
for (f, mname, mline, b0, b1) in METHODS:
    ls, _ = lines_of(f)
    for k in range(b0, b1 + 1):
        code = re.sub(r"//.*$", "", ls[k])
        if not SUCCESS.search(code):
            continue
        # 前 6 行内是否有守卫
        pre = "\n".join(re.sub(r"//.*$", "", ls[x]) for x in range(max(b0, k - 6), k))
        if GUARD.search(pre):
            continue
        # 前 6 行内是否有类库/SDK 调用(说明是"调用后直接报成功")
        call = re.search(r"[A-Za-z0-9_\u4e00-\u9fff]+\s*\.\s*[A-Za-z0-9_\u4e00-\u9fff]+\s*\(", pre)
        if not call:
            continue
        uncond.append((f, k + 1, mname, call.group(0)[:50], code.strip()[:80]))
w("共 %d 处 (需人工确认: 部分调用本身不返回结果, 无法判断成败)" % len(uncond))
for (f, l, mname, call, ret) in uncond[:60]:
    w("   %-24s:%-6d %-30s 前置调用 %-34s" % (f, l, mname, call))

# ============ L4 缺省与 0 不可区分 ============
w()
w("=" * 104)
w("L4 可选数值参数: 缺省与显式 0 不可区分")
w("=" * 104)
w()
zero_default = []
for (f, mname, mline, b0, b1) in METHODS:
    ls, _ = lines_of(f)
    for k in range(b0, b1 + 1):
        code = re.sub(r"//.*$", "", ls[k])
        m = re.search(r"(\w+)\s*=\s*[\w\.]*yyjson取整数\s*\([^,]+,\s*\"([^\"]+)\"\)", code)
        if not m:
            continue
        var, key = m.group(1), m.group(2)
        # 紧随 1..3 行内 如果 (var == 0) { var = 常量 }
        for j in range(k + 1, min(k + 4, b1 + 1)):
            c2 = re.sub(r"//.*$", "", ls[j])
            if re.search(r"如果\s*\(\s*" + re.escape(var) + r"\s*==\s*0\s*\)", c2):
                nxt = "\n".join(re.sub(r"//.*$", "", ls[x]) for x in range(j + 1, min(j + 3, b1 + 1)))
                mm = re.search(re.escape(var) + r"\s*=\s*([^;\n]+)", nxt)
                if mm:
                    zero_default.append((f, k + 1, mname, var, key, mm.group(1).strip()[:40]))
                break
w("共 %d 处 (schema 若声明 '0=某含义' 则为缺陷; 若 0 本身就是无效值则属正常兜底)" % len(zero_default))
for (f, l, mname, var, key, dflt) in zero_default:
    w("   %-24s:%-6d %-34s 参数 %-18s ==0 -> %s" % (f, l, mname, key, dflt))

p = out_report("report_L124.txt", "\n".join(W))
print("written", p)
print("L1 读取后丢弃 %d | L2 无条件成功 %d | L4 0与缺省不分 %d"
      % (len(dead), len(uncond), len(zero_default)))
