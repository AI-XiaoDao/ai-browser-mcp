# -*- coding: utf-8 -*-
"""只读提取: MCP 工具名全集 + 类库方法全集(含参数表) + 分派器分支。

不改任何 .wsv, 不联网, 不编译。
输出 JSON 到 _audit/_cg2_data.json
"""
import io
import json
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"


def read(p):
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with io.open(p, encoding=enc, errors="strict") as f:
                return f.read()
        except Exception:
            continue
    with io.open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


# ---------- 1. 工具名全集: 添加工具JSON ("名字" ----------
TOOL_RE = re.compile(r'添加工具JSON\s*\(\s*"([^"]+)"\s*,')
ALT_RE = re.compile(r'(?:添加工具|注册工具|添加工具JSON)\s*\(\s*"([^"]+)"')

tools = {}   # name -> [files]
regs = []
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".wsv") or "~vbak" in fn:
        continue
    txt = read(os.path.join(SRC, fn))
    lines = txt.split("\n")
    for i, ln in enumerate(lines):
        for m in TOOL_RE.finditer(ln):
            n = m.group(1)
            tools.setdefault(n, [])
            if fn not in tools[n]:
                tools[n].append(fn)
            regs.append({"file": fn, "line": i + 1, "name": n, "text": ln.strip()[:160]})
        # 备用口径: 其它注册调用
        if "添加工具JSON" not in ln:
            for m in ALT_RE.finditer(ln):
                n = m.group(1)
                regs.append({"file": fn, "line": i + 1, "name": n, "alt": True,
                             "text": ln.strip()[:160]})

# ---------- 2. 分派器: 方法名 == "xxx" ----------
DISP_RE = re.compile(r'方法名\s*==\s*"([^"]+)"')
DISP_NAME_RE = re.compile(r'方法\s+([^\s<（(]+)')
dispatchers = {}
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".wsv") or "~vbak" in fn:
        continue
    txt = read(os.path.join(SRC, fn))
    lines = txt.split("\n")
    cur = None
    depth_start = None
    for i, ln in enumerate(lines):
        m = DISP_NAME_RE.match(ln.strip())
        if m and ("分派" in m.group(1) or "执行" in m.group(1)):
            cur = m.group(1)
            dispatchers.setdefault((fn, cur), [])
        m2 = DISP_RE.search(ln)
        if m2 and cur:
            dispatchers.setdefault((fn, cur), []).append(m2.group(1))

disp_out = []
for (fn, cur), vals in dispatchers.items():
    disp_out.append({"file": fn, "method": cur, "count": len(vals), "values": sorted(set(vals))})

# ---------- 3. 类库方法(含参数表) ----------
CLS_RE = re.compile(r'^\s*类\s+([^\s<（(]+)')
METH_RE = re.compile(r'^\s*方法\s+([^\s<（(<]+)')
PARAM_RE = re.compile(r'^\s*参数\s+([^\s<（(<]+)(.*)$')

classlib = []
for fn in sorted(os.listdir(LIB)):
    if not fn.endswith(".wsv"):
        continue
    lines = read(os.path.join(LIB, fn)).split("\n")
    cls = ""
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        mc = CLS_RE.match(lines[i])
        if mc:
            cls = mc.group(1)
            i += 1
            continue
        mm = METH_RE.match(lines[i])
        if mm:
            name = mm.group(1)
            decl = lines[i].strip()
            params = []
            j = i + 1
            while j < len(lines) and j < i + 40:
                t = lines[j].strip()
                if not t:
                    j += 1
                    continue
                mp = PARAM_RE.match(lines[j])
                if mp:
                    params.append((mp.group(1), (mp.group(2) or "").strip()))
                    j += 1
                    continue
                break
            # 备注行(方法上方 \\ 注释)捕获
            note = ""
            k = i - 1
            buf = []
            while k >= 0 and lines[k].strip().startswith("\\"):
                buf.append(lines[k].strip().lstrip("\\").strip())
                k -= 1
            note = " ".join(reversed(buf))[:200]
            classlib.append({"file": fn, "cls": cls, "method": name,
                             "decl": decl[:200], "params": params, "note": note,
                             "line": i + 1})
            i = j
            continue
        i += 1

data = {
    "tools": sorted(tools.keys()),
    "tool_files": tools,
    "regs": regs,
    "dispatchers": disp_out,
    "classlib": classlib,
}
with io.open(os.path.join(HERE, "_cg2_data.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print("工具名(去重) = %d" % len(tools))
print("注册点 = %d" % len(regs))
print("分派器 = %d" % len(disp_out))
for d in sorted(disp_out, key=lambda x: -x["count"]):
    print("   %-28s %-24s %d" % (d["file"], d["method"], d["count"]))
print("类库方法(原始) = %d" % len(classlib))
bycls = {}
for c in classlib:
    bycls.setdefault(c["cls"], set()).add(c["method"])
print("类库类数 = %d" % len(bycls))
for c in sorted(bycls, key=lambda k: -len(bycls[k])):
    print("   %-40s %d" % (c, len(bycls[c])))
