# -*- coding: utf-8 -*-
"""A7 — 资源管理检查: 取记录集 是否配对 释放; 创建的对象是否泄漏"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

W = []
def w(s=""):
    W.append(s)

w("=" * 100)
w("A7 资源管理检查")
w("=" * 100)
w()
w("--- [1] 方法内 取记录集 与 释放 是否配对 ---")
rows = []
for f in FILES:
    ls, _ = lines_of(f)
    for (i0, mname, sig, b0, b1) in find_methods(f):
        objs = collections.defaultdict(lambda: [0, 0, []])
        for k in range(b0, b1 + 1):
            code = re.sub(r"//.*$", "", ls[k])
            for m in re.finditer(r"([A-Za-z0-9_\u4e00-\u9fff]+)\s*=\s*[\w\.]*取记录集\s*\(", code):
                objs[m.group(1)][0] += 1
                objs[m.group(1)][2].append(k + 1)
            for m in re.finditer(r"([A-Za-z0-9_\u4e00-\u9fff]+)\.释放\s*\(\s*\)", code):
                objs[m.group(1)][1] += 1
        for name, (c, r, lines) in objs.items():
            if c != r:
                rows.append((f, i0 + 1, mname, name, c, r, lines))
w("   不配对的方法: %d" % len(rows))
for (f, l, m, name, c, r, lines) in rows:
    w("   %-26s:%-6d %-34s 变量 %-14s 取记录集%d 释放%d  行%s"
      % (f, l, m, name, c, r, lines))

w()
w("--- [2] 数据库可用性守卫: 对 缓存数据库 的直用点是否先判可用 ---")
guard_missing = []
for f in FILES:
    ls, _ = lines_of(f)
    for (i0, mname, sig, b0, b1) in find_methods(f):
        body = "\n".join(ls[k] for k in range(b0, b1 + 1))
        if "缓存数据库.取记录集" not in body and "缓存数据库.执行SQL" not in body:
            continue
        if "缓存数据库可用" in body or "缓存数据库已打开" in body:
            continue
        guard_missing.append((f, i0 + 1, mname))
w("   无守卫的方法: %d" % len(guard_missing))
for (f, l, m) in guard_missing:
    w("   %-26s:%-6d %s" % (f, l, m))

w()
w("--- [3] 浏览器/VIP 对象获取后是否判空 ---")
# 抽查: 取主浏览器 之后下一步是否判空
suspicious = []
for f in FILES:
    ls, _ = lines_of(f)
    for (i0, mname, sig, b0, b1) in find_methods(f):
        for k in range(b0, b1 + 1):
            code = re.sub(r"//.*$", "", ls[k])
            m = re.search(r"([A-Za-z0-9_\u4e00-\u9fff]+)\s*=\s*[\w\.]*取主浏览器\s*\(\s*\)", code)
            if not m:
                continue
            var = m.group(1)
            nxt = "\n".join(re.sub(r"//.*$", "", ls[x]) for x in range(k + 1, min(k + 6, b1 + 1)))
            if ("是否为空" not in nxt) and ("是否已关闭" not in nxt):
                suspicious.append((f, k + 1, mname, var))
w("   取主浏览器 后 5 行内未判空/未判关闭: %d" % len(suspicious))
for (f, l, m, var) in suspicious[:25]:
    w("   %-26s:%-6d %-34s 变量 %s" % (f, l, m, var))
if len(suspicious) > 25:
    w("   ... 另有 %d 处" % (len(suspicious) - 25))

p = out_report("report_A7_resource.txt", "\n".join(W))
print("written", p)
print("记录集不配对 %d | 数据库无守卫 %d | 取主浏览器未判空 %d"
      % (len(rows), len(guard_missing), len(suspicious)))
