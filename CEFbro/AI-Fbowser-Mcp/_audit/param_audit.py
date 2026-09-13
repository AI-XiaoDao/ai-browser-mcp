# -*- coding: utf-8 -*-
"""工具「schema 声明参数」 vs 「实现实际读取参数」 一致性审计。

对每个注册工具:
  A. schema 声明了但实现从不读 → AI 传了也没用 (静默忽略)
  B. 实现读了但 schema 没声明 → AI 无从发现该参数
  C. 类型不一致 → schema 说 integer, 实现却按文本读 (或反之)

方法:
  1) 解析 添加工具JSON(name, desc, schema表达式) 的参数列表(括号配对)
  2) 从 schema 表达式里抽出 属性项JSON/单参数Schema文本 的 (名, 类型)
  3) 建立 工具名 -> 分支体 的映射: 方法名=="X" 后紧跟的 {} 块
  4) 在分支体内收集 yyjson取*(参数JSON, "key") 的读取
  5) 对 别名转发 (分类分派_X (命令ID,"tool",参数JSON)) 跟随一跳
  6) 前缀分派 (是否以(方法名,"browser_fill_")) 单独标记为"动态, 跳过"
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

TEXT = {}
LINES = {}
for f in PROJ:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    t = io.open(p, encoding="utf-8").read()
    TEXT[f] = t
    LINES[f] = t.split("\n")


# ---------- 通用: 括号配对取实参 ----------
def split_args(s, start):
    """s[start] == '('; 返回 (实参列表, 结束位置)。跳过字符串与注释。"""
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
            elif c == "/" and s[i:i + 2] == "//":
                j = s.find("\n", i)
                i = len(s) if j < 0 else j
                continue
            elif c == "(":
                depth += 1
                if depth > 1:
                    cur.append(c)
            elif c == ")":
                depth -= 1
                if depth == 0:
                    args.append("".join(cur)); cur = []
                    return args, i
                cur.append(c)
            elif c == "," and depth == 1:
                args.append("".join(cur)); cur = []
            else:
                cur.append(c)
        i += 1
    return args, -1


# ---------- 1) 解析 添加工具JSON ----------
REGS = {}   # name -> {"desc","schema","file","line"}
for f in PROJ:
    t = TEXT[f]
    for m in re.finditer(r'添加工具JSON\s*\(', t):
        args, end = split_args(t, m.end() - 1)
        if len(args) < 2:
            continue
        name = args[0].strip().strip('"')
        if not re.fullmatch(r'[A-Za-z0-9_.\-]+', name):
            continue
        desc = args[1].strip()
        schema = args[2] if len(args) > 2 else ""
        line = t[:m.start()].count("\n") + 1
        REGS[name] = {"desc": desc, "schema": schema, "file": f, "line": line}

# ---------- 2) 从 schema 表达式抽参数名/类型 ----------
ITEM = re.compile(r'属性项JSON\s*\(([^)]*)\)')
SINGLE = re.compile(r'单参数Schema文本\s*\(([^)]*)\)')


def schema_params(expr):
    """返回 {参数名: 类型}"""
    out = {}
    for m in ITEM.finditer(expr):
        a, _ = split_args("(" + m.group(1) + ")", 0)
        a = [x.strip() for x in a]
        if len(a) >= 2:
            nm = a[0].strip('"'); tp = a[1].strip().strip('"')
            if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', nm):
                out[nm] = tp
    for m in SINGLE.finditer(expr):
        a, _ = split_args("(" + m.group(1) + ")", 0)
        a = [x.strip() for x in a]
        if len(a) >= 2:
            nm = a[0].strip('"'); tp = a[1].strip().strip('"')
            if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', nm):
                out[nm] = tp
    return out


# ---------- 3) 建 工具名 -> 分支体 映射 ----------
DISPATCH_RE = re.compile(r'(?:方法名|工具名|命令名)\s*==\s*"([A-Za-z0-9_.\-]+)"')
# 别名转发:  分类分派_X (命令ID, "tool", ...)
ALIAS_RE = re.compile(r'分类分派_\w+\s*\(\s*\w+\s*,\s*"([A-Za-z0-9_.\-]+)"')

# 全文本 token 化: 找出每个 方法名=="X" 后面紧跟的 {...} 块
BRANCH_BODIES = collections.defaultdict(list)   # tool -> [(file,line,body)]
PREFIX_DYN = set()
for f in PROJ:
    t = TEXT[f]
    ln0 = 0
    for m in DISPATCH_RE.finditer(t):
        name = m.group(1)
        # 找该比较之后第一个 '{'
        j = t.find("{", m.end())
        if j < 0 or j - m.end() > 60:
            # 可能是 否则(...) 多条件合并, 或紧邻下一个比较; 尝试从上一个 '(' 起找
            continue
        # 括号配对取块
        depth, i, in_str = 0, j, False
        while i < len(t):
            c = t[i]
            if in_str:
                if c == "\\":
                    i += 2; continue
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
                        break
            i += 1
        body = t[j:i + 1]
        line = t[:m.start()].count("\n") + 1
        BRANCH_BODIES[name].append((f, line, body))
        # 合并条件: 否则 (方法名=="a" || 方法名=="b")  → 第一个只有 a, b 需单独处理
    for m in re.finditer(r'是否以\s*\(\s*(?:方法名|工具名)\s*,\s*"([^"]+)"', t):
        PREFIX_DYN.add(m.group(1))
    # 别名转发: 这些比较的右值
    for m in ALIAS_RE.finditer(t):
        ALIAS_TARGETS = None

# 别名表: 别名工具 -> 目标工具
ALIAS = {}
for f in PROJ:
    t = TEXT[f]
    for m in re.finditer(r'(?:方法名|工具名)\s*==\s*"([A-Za-z0-9_.\-]+)"\s*\)\s*\{?\s*[\r\n\s]*返回\s*\(\s*分类分派_\w+\s*\(\s*\w+\s*,\s*"([A-Za-z0-9_.\-]+)"', t):
        ALIAS[m.group(1)] = m.group(2)

# ---------- 3b) 方法表 (用于跟随委托) ----------
METHOD_BODIES = {}   # 方法名 -> 方法体文本
METH_DEF = re.compile(r'方法\s+([\u4e00-\u9fff_A-Za-z][\u4e00-\u9fff_A-Za-z0-9_]*)\s*<')
for f in PROJ:
    t = TEXT[f]
    for m in METH_DEF.finditer(t):
        j = t.find("{", m.end())
        if j < 0:
            continue
        depth, i, in_str = 0, j, False
        while i < len(t):
            c = t[i]
            if in_str:
                if c == "\\":
                    i += 2; continue
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
                        break
            i += 1
        METHOD_BODIES.setdefault(m.group(1), t[j:i + 1])

# ---------- 4) 收集读取 ----------
# 关键: 首参必须是"入参对象", 否则会把响应对象的读取 (如 结果对象,"success") 误判为参数。
PARAM_OBJ = r'(?:参数JSON|参数对象|请求JSON|请求参数|参数)'
# 访问器形态一 (函数式):  yyjson取文本 (参数JSON, "key")   /  取对象成员 (参数JSON, "key")
# 访问器形态二 (方法式):  参数JSON.取数组 ("key")
READ_A = re.compile(
    r'(?:yyjson)?取(文本|整数|小数|逻辑|逻辑_默认|JSON文本|对象成员|数组|对象)\s*\(\s*'
    + PARAM_OBJ + r'\s*,\s*"([^"]+)"\s*[,)]')
READ_B = re.compile(
    r'' + PARAM_OBJ + r'\s*\.\s*取(文本|整数|小数|逻辑|逻辑_默认|JSON文本|对象成员|数组|对象)\s*\(\s*"([^"]+)"\s*[,)]')
READ_KIND = {"文本": "string", "JSON文本": "string", "整数": "integer", "小数": "number",
             "逻辑": "boolean", "逻辑_默认": "boolean",
             "数组": "array", "对象": "object", "对象成员": "object"}
# 委托调用: 凡实参列表中出现"入参对象"标识符的调用, 一律跟随 (不限参数位置/个数)。
# 覆盖: 解码JS代码 (参数JSON)  /  执行CDP命令 (命令ID, 方法, 参数JSON)  /  分派_X (命令ID, 参数JSON)
CALL_HEAD = re.compile(r'([\u4e00-\u9fff_A-Za-z][\u4e00-\u9fff_A-Za-z0-9_.]{1,40})\s*\(')
PARAM_OBJ_ALT = "参数JSON|参数对象|请求JSON|请求参数"
# 路由器/聚合器: 方法体内有大量 方法名=="X" 分支的方法。跟随进去会把"几乎所有参数"都
# 算成该工具的参数, 造成大规模假阳性 (实测 browser_collect 曾一次误报约 150 个参数名)。
ROUTERS = set()
for _mn, _mb in METHOD_BODIES.items():
    if len(re.findall(r'(?:方法名|工具名|命令名)\s*==', _mb)) >= 3:
        ROUTERS.add(_mn)


def _callee_args(body):
    for m in CALL_HEAD.finditer(body):
        args, end = split_args(body, m.end() - 1)
        if end < 0:
            continue
        yield m.group(1), args


def reads_of(body, depth=0, _seen=None):
    """收集 body 内对入参对象的读取; 跟随委托调用 (任意参数位置)。"""
    if _seen is None:
        _seen = set()
    out = collections.defaultdict(set)
    for RX in (READ_A, READ_B):
        for m in RX.finditer(body):
            out[m.group(2)].add(READ_KIND[m.group(1)])
    if depth < 3:
        for callee, args in _callee_args(body):
            if not any(re.fullmatch(r'(?:%s)' % PARAM_OBJ_ALT, a.strip()) for a in args):
                continue
            short = callee.split(".")[-1]
            if short in ROUTERS:
                continue
            sub = METHOD_BODIES.get(short)
            if not sub or short in _seen or len(sub) > 400000:
                continue
            _seen.add(short)
            for k, v in reads_of(sub, depth + 1, _seen).items():
                out[k] |= v
    return out


# ---------- 5) 主循环 ----------
rows_ignored, rows_undeclared, rows_type = [], [], []
dyn, unresolved = [], []

for name, info in sorted(REGS.items()):
    decl = schema_params(info["schema"])
    branches = BRANCH_BODIES.get(name, [])
    if not branches:
        # 别名转发?
        tgt = ALIAS.get(name)
        if tgt and tgt in BRANCH_BODIES:
            branches = BRANCH_BODIES[tgt]
        elif any(name.startswith(p) or p.rstrip("_") in name for p in PREFIX_DYN):
            dyn.append(name); continue
        else:
            unresolved.append(name); continue
    r = collections.defaultdict(set)
    for f, line, body in branches:
        for k, v in reads_of(body).items():
            r[k] |= v
    if not decl and name in ("ping",):
        continue

    ignored = [k for k in decl if k not in r]
    undecl = [k for k in r if k not in decl]
    tm = []
    for k in r:
        if k in decl:
            dt = decl[k]
            for rt in r[k]:
                if dt == "integer" and rt == "string":
                    tm.append((k, dt, "文本"))
                elif dt == "string" and rt in ("integer", "number", "boolean"):
                    tm.append((k, dt, rt))
    if ignored:
        rows_ignored.append((name, ignored, info["file"], info["line"]))
    if undecl:
        rows_undeclared.append((name, sorted(undecl), info["file"], info["line"]))
    if tm:
        rows_type.append((name, tm, info["file"], info["line"]))

print("=" * 100)
print("工具参数一致性审计 (schema 声明 vs 实现读取)")
print("=" * 100)
print("  注册工具: %d" % len(REGS))
print("  已定位分支: %d   前缀动态分派跳过: %d   未定位: %d"
      % (len(REGS) - len(dyn) - len(unresolved), len(dyn), len(unresolved)))
print()
print("-" * 100)
print("A. schema 声明了但实现从不读取 (AI 传了静默无效) — %d" % len(rows_ignored))
print("-" * 100)
for n, ks, f, l in rows_ignored:
    print("  %-40s %-22s %s" % (n, ",".join(ks), "%s:%d" % (f, l)))
print()
print("-" * 100)
print("B. 实现读取了但 schema 未声明 (AI 无从发现) — %d" % len(rows_undeclared))
print("-" * 100)
for n, ks, f, l in rows_undeclared:
    print("  %-40s %-34s %s" % (n, ",".join(ks), "%s:%d" % (f, l)))
print()
print("-" * 100)
print("C. 类型不一致 (schema 类型 vs 实现读取方式) — %d" % len(rows_type))
print("-" * 100)
for n, tm, f, l in rows_type:
    print("  %-40s %-30s %s" % (n, "; ".join("%s: schema=%s impl=读为%s" % x for x in tm), "%s:%d" % (f, l)))
print()
print("-" * 100)
print("前缀动态分派(无法静态判定, 跳过) — %d" % len(dyn))
print("-" * 100)
print("  " + (", ".join(sorted(dyn)[:40]) if dyn else "(无)"))
print()
print("未定位实现的注册工具 — %d" % len(unresolved))
print("  " + (", ".join(unresolved) if unresolved else "(无)"))

json.dump({"ignored": rows_ignored, "undeclared": rows_undeclared, "type": rows_type,
           "dynamic": sorted(dyn), "unresolved": unresolved},
          io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_param_audit.json"),
                  "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print()
print("saved _param_audit.json")
