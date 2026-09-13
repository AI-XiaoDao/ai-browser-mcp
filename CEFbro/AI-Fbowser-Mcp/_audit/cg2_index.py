# -*- coding: utf-8 -*-
"""构建证据索引:
- 311 工具的注册调用全文(名字/描述/schema 属性名/枚举值)
- src 全量字符串字面量及其文件/行
- 候选类库方法在 src 中的直接调用点
- 每个工具的分派分支(方法名 == "xxx" / 动作 == "xxx" 等)
输出 _cg2_index.json
"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")


def read(p):
    with io.open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith(".wsv") and "~vbak" not in fn:
        files[fn] = read(os.path.join(SRC, fn))

SRC_ALL = {fn: t.split("\n") for fn, t in files.items()}


def balanced(text, start):
    """从 text[start] 处的 '(' 起返回配对括号内的内容"""
    d = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == '"':
            i += 1
            while i < len(text):
                if text[i] == '"':
                    break
                i += 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return text[start + 1:i]
        i += 1
    return text[start + 1:]


# ---------- 工具注册 ----------
TOOLS = {}
for fn, t in files.items():
    for m in re.finditer(r'添加工具JSON\s*\(', t):
        body = balanced(t, m.end() - 1)
        nm = re.match(r'\s*"([^"]+)"', body)
        if not nm:
            continue
        name = nm.group(1)
        line = t[:m.start()].count("\n") + 1
        desc = ""
        d = re.search(r',\s*"((?:[^"\\]|\\.)*)"', body)
        if d:
            desc = d.group(1)
        props = re.findall(r'属性项JSON\s*\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*"((?:[^"\\]|\\.)*)"', body)
        TOOLS[name] = {"file": fn, "line": line, "desc": desc,
                       "schema": [{"name": p[0], "type": p[1], "desc": p[2]} for p in props],
                       "body": body}

# ---------- 工具的分派分支 ----------
# 在每个 src 文件里, 找 方法名 == "x" / 动作 == "x" / 名 == "x" 等比较, 并归属到所在的 方法
CMP = re.compile(r'([\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]{0,20})\s*==\s*"([^"]+)"')
CLSMRK = re.compile(r'^\s*方法\s+([^\s<（(]+)')
branch = {n: [] for n in TOOLS}
allsym = {}   # (sym, value) -> [(file,line)]
for fn, lines in SRC_ALL.items():
    cur = ""
    for i, ln in enumerate(lines, 1):
        cm = CLSMRK.match(ln)
        if cm:
            cur = cm.group(1)
        for m in CMP.finditer(ln):
            sym, val = m.group(1), m.group(2)
            allsym.setdefault(sym, {}).setdefault(val, []).append("%s:%d" % (fn, i))
            if val in branch:
                branch[val].append({"file": fn, "line": i, "sym": sym,
                                    "in": cur, "text": ln.strip()[:200]})

# ---------- 字符串字面量全局索引 ----------
LIT = re.compile(r'"((?:[^"\\]|\\.){1,120})"')
lit_index = {}
for fn, t in files.items():
    for i, ln in enumerate(t.split("\n"), 1):
        for m in LIT.finditer(ln):
            lit_index.setdefault(m.group(1), []).append("%s:%d" % (fn, i))

# ---------- 类库方法在 src 中的直接调用 ----------
def call_sites(method):
    pat = re.compile(re.escape(method) + r"\s*\(")
    out = []
    for fn, t in files.items():
        for i, ln in enumerate(t.split("\n"), 1):
            if pat.search(ln):
                out.append("%s:%d: %s" % (fn, i, ln.strip()[:160]))
    return out


data = {"tools": TOOLS, "branch": branch, "lit": {k: v[:6] for k, v in lit_index.items()},
        "symbols": {k: {kk: vv[:4] for kk, vv in v.items()} for k, v in allsym.items()}}
json.dump(data, io.open(os.path.join(HERE, "_cg2_index.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)

print("工具数 =", len(TOOLS))
print("有 schema 的工具 =", sum(1 for v in TOOLS.values() if v["schema"]))
print("有分派分支的工具 =", sum(1 for n in TOOLS if branch[n]))
print("字符串字面量(去重) =", len(lit_index))
print("比较符号数 =", len(allsym))
