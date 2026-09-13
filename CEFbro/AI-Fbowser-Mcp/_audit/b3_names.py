# -*- coding: utf-8 -*-
r"""B3 — 生成完整英文名表 (去重 + 保留清单 + 冲突检测)

规则:
  * 虚拟覆盖方法 (@虚拟方法 = 可覆盖) / 启动类  -> 保留编译器生成的符号名, 不改
  * 类名       : 项目内唯一
  * 方法+变量  : 类内唯一 (C++ 中同属类作用域)
  * 参数       : 方法内唯一 (C++ 形参名不可重复)
"""
import sys, os, re, json, collections, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("b2", os.path.join(OUT, "b2_english.py"))
b2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b2)
compose, compose_class = b2.compose, b2.compose_class

inv = json.load(open(os.path.join(OUT, "inventory.json"), encoding="utf-8"))

CPP_KEYWORDS = {
    "alignas", "alignof", "and", "asm", "auto", "bool", "break", "case", "catch",
    "char", "class", "const", "constexpr", "continue", "default", "delete", "do",
    "double", "else", "enum", "explicit", "export", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable", "namespace",
    "new", "noexcept", "not", "nullptr", "operator", "or", "private", "protected",
    "public", "register", "return", "short", "signed", "sizeof", "static", "struct",
    "switch", "template", "this", "throw", "true", "try", "typedef", "typeid",
    "typename", "union", "unsigned", "using", "virtual", "void", "volatile", "while",
    "xor", "and_eq", "or_eq", "not_eq", "bitand", "bitor", "compl",
}


def uniq(name, used):
    """冲突则加数字后缀"""
    if name and name not in used and name.lower() not in CPP_KEYWORDS:
        used.add(name); return name, False
    base = name or "Member"
    i = 2
    while ("%s%d" % (base, i)) in used or ("%s%d" % (base, i)).lower() in CPP_KEYWORDS:
        i += 1
    n = "%s%d" % (base, i)
    used.add(n)
    return n, True


out = {"classes": {}, "methods": {}, "vars": {}, "params": {}}
conflicts = []
kept = []

# ---- 类 ----
used_cls = set()
for c in inv["classes"]:
    if c["keep"]:
        kept.append(("类", c["name"], "", c["keep_reason"]))
        out["classes"][c["name"]] = {"en": "", "file": c["file"], "line": c["line"], "keep": True}
        continue
    en, dup = uniq(compose_class(c["name"]), used_cls)
    if dup:
        conflicts.append(("类", c["name"], en))
    out["classes"][c["name"]] = {"en": en, "file": c["file"], "line": c["line"], "keep": False}

# ---- 方法 + 成员变量 (类作用域去重) ----
used_by_cls = collections.defaultdict(set)
for c in inv["classes"]:
    used_by_cls[c["name"]]  # 初始化

for m in inv["methods"]:
    if m["keep"]:
        kept.append(("方法", "%s.%s" % (m["cls"], m["name"]), "", m["keep_reason"]))
        out["methods"]["%s.%s" % (m["cls"], m["name"])] = {
            "en": "", "file": m["file"], "line": m["line"], "keep": True,
            "virtual": True, "static": m["static"], "cls": m["cls"]}
        continue
    en, dup = uniq(compose(m["name"]), used_by_cls[m["cls"]])
    if dup:
        conflicts.append(("方法", "%s.%s" % (m["cls"], m["name"]), en))
    out["methods"]["%s.%s" % (m["cls"], m["name"])] = {
        "en": en, "file": m["file"], "line": m["line"], "keep": False,
        "virtual": False, "static": m["static"], "cls": m["cls"]}

for v in inv["vars"]:
    en, dup = uniq(compose(v["name"]), used_by_cls[v["cls"]])
    if dup:
        conflicts.append(("变量", "%s.%s" % (v["cls"], v["name"]), en))
    out["vars"]["%s.%s" % (v["cls"], v["name"])] = {
        "en": en, "file": v["file"], "line": v["line"], "kind": v["kind"],
        "static": v["static"], "cls": v["cls"]}

# ---- 参数 (方法内去重) ----
used_by_m = collections.defaultdict(set)
for p in inv["params"]:
    key = "%s.%s" % (p["cls"], p["method"])
    en, dup = uniq(compose(p["name"]), used_by_m[key])
    if dup:
        conflicts.append(("参数", "%s(%s)" % (key, p["name"]), en))
    out["params"]["%s|%s|%s" % (p["cls"], p["method"], p["name"])] = {
        "en": en, "file": p["file"], "line": p["line"], "type": p["type"]}

json.dump(out, open(os.path.join(OUT, "english_names.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

W = []
def w(s=""):
    W.append(s)
w("=" * 108)
w("B3 英文输出名表 (PascalCase, 无前缀)")
w("=" * 108)
w()
w("类 %d (改名 %d, 保留 %d)" % (len(inv["classes"]),
                              sum(1 for v in out["classes"].values() if not v["keep"]),
                              sum(1 for v in out["classes"].values() if v["keep"])))
w("方法 %d (改名 %d, 保留虚拟覆盖 %d)" % (len(inv["methods"]),
                                      sum(1 for v in out["methods"].values() if not v["keep"]),
                                      sum(1 for v in out["methods"].values() if v["keep"])))
w("成员变量/常量 %d" % len(inv["vars"]))
w("参数 %d" % len(inv["params"]))
w()
w("因重名而加数字后缀的条目: %d" % len(conflicts))
for k in conflicts[:30]:
    w("   [%s] %s -> %s" % k)
if len(conflicts) > 30:
    w("   ... 另有 %d 条" % (len(conflicts) - 30))
w()
w("=" * 108)
w("一、类名映射")
w("=" * 108)
w("%-34s %-42s %s" % ("火山类名", "英文输出名", "说明"))
w("-" * 108)
for c in inv["classes"]:
    e = out["classes"][c["name"]]
    w("%-34s %-42s %s" % (c["name"], e["en"] or "(保留)", c["keep_reason"]))
w()
w("=" * 108)
w("二、方法映射 (按类分组)")
w("=" * 108)
cur = None
for m in inv["methods"]:
    if m["cls"] != cur:
        cur = m["cls"]
        w()
        w("### %s  ->  %s" % (cur, out["classes"][cur]["en"] or "(保留)"))
    e = out["methods"]["%s.%s" % (m["cls"], m["name"])]
    tag = "保留" if e["keep"] else ""
    w("    %-40s %-46s %s" % (m["name"], e["en"] or "(保留原名)", tag))
w()
w("=" * 108)
w("三、成员变量/常量映射")
w("=" * 108)
cur = None
for v in inv["vars"]:
    if v["cls"] != cur:
        cur = v["cls"]
        w()
        w("### %s" % cur)
    e = out["vars"]["%s.%s" % (v["cls"], v["name"])]
    w("    %-40s %-46s %s" % (v["name"], e["en"], v["kind"]))
w()
w("=" * 108)
w("四、参数映射 (样例, 全量见 english_names.json)")
w("=" * 108)
seen = 0
for p in inv["params"]:
    key = "%s|%s|%s" % (p["cls"], p["method"], p["name"])
    w("    %-30s %-30s -> %s" % (p["method"][:30], p["name"], out["params"][key]["en"]))
    seen += 1
    if seen >= 60:
        break

p = out_report("report_B3_names.txt", "\n".join(W))
print("written", p)
print("classes %d | methods %d (keep %d) | vars %d | params %d | conflicts %d"
      % (len(inv["classes"]), len(inv["methods"]),
         sum(1 for v in out["methods"].values() if v["keep"]),
         len(inv["vars"]), len(inv["params"]), len(conflicts)))
