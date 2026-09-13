# -*- coding: utf-8 -*-
r"""A9 — 火山方法名 -> C++ 输出名 映射提取

原理（已实证）：火山编译器为每个类生成 vcls_rg_<Pinyin>.h，
其中 `static ... CALLBACK rg_<Pinyin> (...)` 声明的**顺序**与 .wsv 中
该类的方法定义顺序严格一致，参数名亦逐位对应（重名参数加数字后缀）。

因此可用"顺序对齐"建立权威映射，并反向推导汉字->拼音字典做全局校验。
"""
import sys, re, os, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

GEN = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\generated-cpp\release-x64"

W = []
def w(s=""):
    W.append(s)

# ---------- 1. 解析 .wsv: 每个类的方法/变量（按定义顺序） ----------
classes = collections.OrderedDict()   # name -> dict(file, methods[], vars[])
for f in FILES:
    ls, _, da = brace_map(f)
    cls = None
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        clean = strip_strings_and_comment(ln)[0]
        m = re.match(r"\s*类\s+(\S+)", clean)
        if m:
            cls = m.group(1)
            classes[cls] = {"file": f, "line": i + 1, "methods": [], "vars": [],
                            "b0": i, "b1": None}
            continue
        if cls is None:
            continue
        # 只取类体直属层级 (depth == 类体基准+1)
        if da[i] != 1:
            continue
        mm = re.match(r"\s*方法\s+(\S+)", clean)
        if mm:
            classes[cls]["methods"].append((mm.group(1), i + 1))
            continue
        mv = re.match(r"\s*变量\s+(\S+)", clean)
        if mv:
            classes[cls]["vars"].append((mv.group(1), i + 1))
            continue
        mc = re.match(r"\s*常量\s+(\S+)", clean)
        if mc:
            classes[cls]["vars"].append(("常量:" + mc.group(1), i + 1))

# 事件接收方法名带下划线且第1参=事件类，同样作为方法计入
w("# 1. .wsv 类清单")
w("%-34s %-26s %6s %6s" % ("类名", "文件", "方法数", "变量数"))
w("-" * 80)
for c, d in classes.items():
    w("%-34s %-26s %6d %6d" % (c, d["file"], len(d["methods"]), len(d["vars"])))
w("合计 %d 个类" % len(classes))

# ---------- 2. 解析生成头 ----------
hdr_info = {}
for fn in os.listdir(GEN):
    if not (fn.startswith("vcls_rg_") and fn.endswith(".h")):
        continue
    p = os.path.join(GEN, fn)
    txt = open(p, encoding="utf-8", errors="replace").read()
    if "rg_volcano_app" not in txt:
        continue        # 只看项目自身包的类
    cm = re.search(r"class\s+(rg_[A-Za-z0-9_]+)\s*:\s*public\s+\w+", txt)
    if not cm:
        continue
    cname = cm.group(1)
    methods, variables = [], []
    # 方法声明区: 到 "inline_ rg_...()" 为止
    stop = txt.find("inline_ %s ()" % cname)
    body = txt[:stop] if stop > 0 else txt
    for m in re.finditer(r"static\s+[\w:<>&\s\*]+?\s+CALLBACK\s+(rg_[A-Za-z0-9_]+)\s*\(([^)]*)\)", body):
        methods.append((m.group(1), m.group(2).strip()))
    # 变量区: 方法区之后的 static 声明
    varpart = txt[stop:] if stop > 0 else ""
    for m in re.finditer(r"static\s+[\w:<>&\s\*]+?\s+(rg_[A-Za-z0-9_]+)\s*;", varpart):
        variables.append(m.group(1))
    hdr_info[fn] = {"class": cname, "methods": methods, "vars": variables}

w()
w("# 2. 生成头清单（仅 rg_volcano_app 命名空间）: %d 个" % len(hdr_info))
w("%-46s %-34s %6s %6s" % ("头文件", "C++类名", "方法数", "变量数"))
w("-" * 96)
for fn, d in sorted(hdr_info.items()):
    w("%-46s %-34s %6d %6d" % (fn, d["class"], len(d["methods"]), len(d["vars"])))

# ---------- 3. 顺序对齐（按 方法数 精确匹配） ----------
w()
w("# 3. 顺序对齐")
by_count = collections.defaultdict(list)
for fn, d in hdr_info.items():
    by_count[len(d["methods"])].append(fn)

align = {}
unmatched = []
for c, d in classes.items():
    cands = by_count.get(len(d["methods"]), [])
    if len(cands) == 1:
        align[c] = cands[0]
    elif len(cands) > 1:
        # 用 ASCII 片段消歧: 取方法名中的 ASCII 串集合
        def ascii_set(names):
            s = set()
            for n, _ in names:
                for x in re.findall(r"[A-Za-z][A-Za-z0-9]*", n):
                    if len(x) >= 2:
                        s.add(x.lower())
            return s
        want = ascii_set(d["methods"])
        best, bs = None, -1
        for fn in cands:
            got = set()
            for mn, _ in hdr_info[fn]["methods"]:
                for x in re.findall(r"[A-Za-z][A-Za-z0-9]*", mn):
                    if len(x) >= 2:
                        got.add(x.lower())
            sc = len(want & got)
            if sc > bs:
                bs, best = sc, fn
        align[c] = best
    else:
        unmatched.append(c)

w("%-34s %-46s %s" % ("火山类", "生成头文件", "对齐"))
w("-" * 96)
for c in classes:
    w("%-34s %-46s %s" % (c, align.get(c, "(无匹配)"),
                          "OK" if c in align else "**未对齐**"))
if unmatched:
    w()
    w("未对齐的类: %s" % ", ".join(unmatched))

# ---------- 4. 方法映射表 ----------
w()
w("=" * 100)
w("# 4. 方法输出名映射表  (火山类.方法  ->  C++ 符号)")
w("=" * 100)
mapping = collections.OrderedDict()
dirty = []
for c, fn in align.items():
    d = classes[c]
    hm = hdr_info[fn]["methods"]
    wm = d["methods"]
    if len(hm) != len(wm):
        w("!! %s: 数量不一致 wsv=%d hdr=%d" % (c, len(wm), len(hm)))
        continue
    ns = "rg_volcano_app"
    cn = hdr_info[fn]["class"]
    rows = []
    for (wname, wline), (hname, hsig) in zip(wm, hm):
        rows.append((wname, wline, hname, hsig))
        mapping["%s.%s" % (c, wname)] = {
            "cpp_class": "%s::%s" % (ns, cn),
            "cpp_method": hname,
            "file": d["file"], "line": wline, "sig": hsig}
    w()
    w("### %s  (%s, 第%d行)" % (c, d["file"], d["line"]))
    w("    C++: namespace %s {  class %s  }" % (ns, cn))
    w("    %-38s %-6s %-52s" % ("火山方法名", "行", "C++ 输出名"))
    w("    " + "-" * 96)
    for (wname, wline, hname, hsig) in rows:
        w("    %-38s %-6d %-52s" % (wname, wline, hname))
        if len(hsig) > 100:
            w("        %s" % hsig[:100] + " ...")

# ---------- 5. 反推汉字->拼音字典并校验 ----------
w()
w("=" * 100)
w("# 5. 反推 汉字->拼音 字典（用于校验翻译规律，并覆盖未生成头的名字）")
w("=" * 100)
char_map = collections.defaultdict(collections.Counter)

def split_name_cpp(s):
    """把 C++ 名切成 token 序列: 汉字段->拼音段(首字母大写分片), ASCII 段整体"""
    # 去掉 rg_ 前缀
    if s.startswith("rg_"):
        s = s[3:]
    return s

# 用已对齐的 方法/变量 对建立映射: 汉字串 <-> 拼音串
pairs = []
for c, fn in align.items():
    d, h = classes[c], hdr_info[fn]
    for (wn, wl), (hn, hs) in zip(d["methods"], h["methods"]):
        pairs.append((wn, hn))
    for (vn, vl), hv in zip(d["vars"], h["vars"]):
        pairs.append((vn, hv))

for wn, hn in pairs:
    wn2 = wn
    hn2 = hn[3:] if hn.startswith("rg_") else hn
    # 逐字符: 汉字 -> 期望拼音; ASCII 原样
    i = j = 0
    # 简单对齐: 汉字产生 "Xxx" 段(1-6字母, 首字母大写, 后面小写)，ASCII 产生自身
    # 用正则切 hn2 为 token
    toks = re.findall(r"[A-Z][a-z]*|[A-Z]+(?![a-z])|_|[0-9]+", hn2)
    # 汉字逐个消费 token
    ti = 0
    ok = True
    wchars = list(wn2)
    for wc in wchars:
        if ti >= len(toks):
            ok = False; break
        if re.match(r"[\u4e00-\u9fff]", wc):
            t = toks[ti]
            if t == "_":
                ok = False; break
            # 合并可能的多次token? 拼音段一般单token
            char_map[wc][t] += 1
            ti += 1
        else:
            # ASCII 原样消费
            rest = "".join(toks[ti:])
            if rest.upper().startswith(wc.upper()):
                # 前进: 该 ASCII 字符可能落在某个 token 内
                # 简化: 只做整体性检查，跳过
                ti += 1 if ti < len(toks) else 0
            else:
                pass

amb = {k: v for k, v in char_map.items() if len(v) > 1}
w("反推出 %d 个汉字的拼音" % len(char_map))
w("其中 %d 个汉字出现多于一�种拼音（需人工确认或说明是建模噪声）:" % len(amb))
for k, v in sorted(amb.items(), key=lambda x: -sum(x[1].values()))[:40]:
    w("   %s -> %s" % (k, dict(v.most_common(4))))
w()
w("（确定性字典已写入 char_pinyin.json，可用于为未生成头文件的成员推导输出名）")

json.dump({k: v.most_common(1)[0][0] for k, v in char_map.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "char_pinyin.json"), "w",
               encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(mapping,
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "symbol_map.json"), "w",
               encoding="utf-8"), ensure_ascii=False, indent=1)

w()
w("映射条目总数: %d" % len(mapping))
p = out_report("report_A9_symbols.txt", "\n".join(W))
print("written", p, "| mapping:", len(mapping), "| classes:", len(classes),
      "| aligned:", len(align), "| chars:", len(char_map))
