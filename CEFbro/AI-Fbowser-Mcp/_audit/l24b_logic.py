# -*- coding: utf-8 -*-
r"""L2b / L4b — 收窄后的逻辑检查

L2b: 只保留**可失败的原生调用**之后的"无条件成功" (browser./框架./填表框架./请求环境. 等)
L4b: 把"0 与缺省不可区分"的候选与 schema 描述交叉 —— 只有 schema 明确写了 "0=某含义"
     或 "默认N" 的才算缺陷
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

# schema: 工具 -> {参数: 描述}
srv = lines_of("MCP_Server.wsv")[0]
schema_desc = {}
cur_tool = None
for i, ln in enumerate(srv):
    m = re.search(r'添加工具JSON\s*\(\s*"([^"]+)"', ln)
    if m:
        cur_tool = m.group(1)
        schema_desc.setdefault(cur_tool, {})
        for pm in re.finditer(r'属性项JSON\s*\(\s*"([^"]+)"\s*,\s*"[^"]*"\s*,\s*"([^"]*)"', ln):
            schema_desc[cur_tool][pm.group(1)] = pm.group(2)
        for pm in re.finditer(r'单参数Schema文本\s*\(\s*"([^"]+)"\s*,\s*"[^"]*"\s*,\s*"([^"]*)"', ln):
            schema_desc[cur_tool][pm.group(1)] = pm.group(2)

METHODS = []
for f in FILES:
    for (i0, mname, sig, b0, b1) in find_methods(f):
        METHODS.append((f, mname, i0 + 1, b0, b1))

def owner_of(f, line):
    ls, _ = lines_of(f)
    for k in range(line - 1, 0, -1):
        m = re.search(r'方法名\s*==\s*"([A-Za-z0-9_]+)"', ls[k])
        if m:
            return m.group(1)
    return "?"

# ---------- L2b ----------
w("=" * 104)
w("L2b 可失败原生调用后无判断即返回成功")
w("=" * 104)
w()
FALLIBLE = re.compile(r"\b(browser|框架|主框架|填表框架|请求环境|环境|开发者DOM|vip_ctrl|vp|br)\s*\.\s*[A-Za-z0-9_\u4e00-\u9fff]+\s*\(")
SUCCESS = re.compile(r'返回\s*\(\s*(?:MCP_响应构建\.)?(?:命令成功|命令成功_原始JSON|构建简单JSON|构建标准成功JSON|响应_需要刷新)')
NEG = re.compile(r'命令失败|构建标准失败JSON|是否为空|是否有效|元素是否存在|找到|== -1|!= ""|超时|异常|失败')
res = []
for (f, mname, mline, b0, b1) in METHODS:
    ls, _ = lines_of(f)
    for k in range(b0, b1 + 1):
        code = re.sub(r"//.*$", "", ls[k])
        if not SUCCESS.search(code):
            continue
        pre = [(x + 1, re.sub(r"//.*$", "", ls[x])) for x in range(max(b0, k - 8), k)]
        ptxt = "\n".join(t for _, t in pre)
        fm = FALLIBLE.search(ptxt)
        if not fm:
            continue
        if NEG.search(ptxt):
            continue
        ln = [n for n, t in pre if FALLIBLE.search(t)]
        res.append((f, k + 1, owner_of(f, k + 1), fm.group(0).strip(), ln[-1] if ln else 0))
w("共 %d 处" % len(res))
for (f, l, tool, call, cl) in res:
    w("   %-24s:%-6d %-30s 调用行 %-6d %s" % (f, l, tool, cl, call.replace(" ", "")[:40]))

# ---------- L4b ----------
w()
w("=" * 104)
w("L4b 可选数值参数: 0 与缺省不可区分  (仅列 schema 描述含 '默认' 或 '0=' 的)")
w("=" * 104)
w()
zero = []
for (f, mname, mline, b0, b1) in METHODS:
    ls, _ = lines_of(f)
    for k in range(b0, b1 + 1):
        code = re.sub(r"//.*$", "", ls[k])
        m = re.search(r"(\w+)\s*=\s*[\w\.]*yyjson取整数\s*\([^,]+,\s*\"([^\"]+)\"\)", code)
        if not m:
            continue
        var, key = m.group(1), m.group(2)
        for j in range(k + 1, min(k + 4, b1 + 1)):
            c2 = re.sub(r"//.*$", "", ls[j])
            if re.search(r"如果\s*\(\s*" + re.escape(var) + r"\s*==\s*0\s*\)", c2):
                nxt = "\n".join(re.sub(r"//.*$", "", ls[x]) for x in range(j + 1, min(j + 4, b1 + 1)))
                mm = re.search(re.escape(var) + r"\s*=\s*([^;\n]+)", nxt)
                if not mm:
                    break
                tool = owner_of(f, k + 1)
                desc = schema_desc.get(tool, {}).get(key, "")
                if ("默认" in desc) or ("0=" in desc) or ("0 =" in desc):
                    zero.append((f, k + 1, tool, key, desc[:70], mm.group(1).strip()[:30]))
                break
w("共 %d 处" % len(zero))
for (f, l, tool, key, desc, dflt) in zero:
    w("   %-24s:%-6d %-30s 参数 %-18s" % (f, l, tool, key))
    w("        schema: %s" % desc)
    w("        实现:  ==0 -> %s" % dflt)

p = out_report("report_L24b.txt", "\n".join(W))
print("written", p)
print("L2b 无条件成功 %d | L4b 0与缺省不分 %d" % (len(res), len(zero)))
