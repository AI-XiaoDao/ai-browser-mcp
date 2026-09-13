# -*- coding: utf-8 -*-
r"""B1 — 英文命名清单 + 中文词素频率统计

产出:
  inventory.json  每个 类/方法/成员变量/参数 的完整清单与标记
                  (是否 @虚拟方法 = 可覆盖 / 是否静态 / 是否启动类 / 所属文件行号)
  频次报告        为构建 中文->英文 术语词典排序依据
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

OUT = os.path.dirname(os.path.abspath(__file__))

# 排除清单: 改名会破坏语义
KEEP_REASON = {}

inv = {"classes": [], "methods": [], "vars": [], "params": []}
mor = collections.Counter()          # 中文词素频次
mor_ctx = collections.defaultdict(set)

CN = re.compile(r"[\u4e00-\u9fff]+")

def runs(name):
    """提取中文连续段"""
    return CN.findall(name)

for f in FILES:
    ls, _, da = brace_map(f)
    cls = None
    cls_line = None
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        clean = strip_strings_and_comment(ln)[0]
        m = re.match(r"\s*类\s+(\S+)", clean)
        if m:
            cls = m.group(1); cls_line = i + 1
            attr = ln
            base = re.search(r"基础类\s*=\s*(\S+)", attr)
            inv["classes"].append({
                "name": cls, "file": f, "line": cls_line,
                "base": base.group(1) if base else "",
                "global_cls": "@全局类" in attr,
                "keep": cls.startswith("类_FBrowser") or cls == "启动类",
                "keep_reason": "编译器固定入口 startup_class" if cls == "启动类" else "",
            })
            continue
        if cls is None or da[i] != 1:
            continue
        mm = re.match(r"\s*方法\s+(\S+)", clean)
        if mm:
            mname = mm.group(1)
            is_virtual = "@虚拟方法" in ln
            is_static = "静态" in ln.split(">")[0]
            # 属性表可能跨行 -> 向前后各取 2 行合并判断
            merged = ln
            j = i + 1
            while j < len(ls) and ">" not in merged:
                merged += ls[j]; j += 1
            is_virtual = "@虚拟方法" in merged
            rtype = re.search(r"类型\s*=\s*(\S+?)[\s>]", merged)
            inv["methods"].append({
                "cls": cls, "name": mname, "file": f, "line": i + 1,
                "virtual": is_virtual, "static": "静态" in merged.split("类型")[0],
                "rtype": rtype.group(1) if rtype else "",
                "recv": "接收事件" in merged,
                "keep": is_virtual,
                "keep_reason": "虚拟覆盖: 改名会使 C++ virtual 覆盖失效" if is_virtual else "",
            })
            for r in runs(mname):
                mor[r] += 1; mor_ctx[r].add("方法")
            # 参数
            k = i + 1
            while k < len(ls) and re.match(r"\s*参数\s+\S+", ls[k]):
                pm = re.match(r"\s*参数\s+(\S+)", ls[k])
                pt = re.search(r"类型\s*=\s*(\S+?)[\s>]", ls[k])
                inv["params"].append({"cls": cls, "method": mname, "name": pm.group(1),
                                      "type": pt.group(1) if pt else "", "file": f, "line": k + 1})
                for r in runs(pm.group(1)):
                    mor[r] += 1; mor_ctx[r].add("参数")
                k += 1
            continue
        mv = re.match(r"\s*(变量|常量)\s+(\S+)", clean)
        if mv:
            kind, vname = mv.group(1), mv.group(2)
            is_static = "静态" in ln
            inv["vars"].append({"cls": cls, "kind": kind, "name": vname, "file": f,
                                "line": i + 1, "static": is_static, "keep": False})
            for r in runs(vname):
                mor[r] += 1; mor_ctx[r].add(kind)

cls_keep = [c["name"] for c in inv["classes"] if c["keep"]]
m_keep = [m for m in inv["methods"] if m["keep"]]
print("=" * 100)
print("B1 英文命名清单")
print("=" * 100)
print()
print("类        : %3d  (其中需保留原名 %d: %s)" % (len(inv["classes"]), len(cls_keep), ", ".join(cls_keep)))
print("方法      : %3d  (其中 @虚拟方法=可覆盖 需保留原名 %d)" % (len(inv["methods"]), len(m_keep)))
print("  可改名  : %3d" % (len(inv["methods"]) - len(m_keep)))
print("成员变量/常量: %3d" % len(inv["vars"]))
print("参数      : %3d" % len(inv["params"]))
print()
print("按文件分布（可改名方法数）:")
per = collections.Counter()
for m in inv["methods"]:
    if not m["keep"]:
        per[m["file"]] += 1
for k, v in per.most_common():
    print("   %-26s %3d" % (k, v))
print()
print("--- 需保留原名的虚拟覆盖方法（按类） ---")
per2 = collections.Counter(m["cls"] for m in m_keep)
for k, v in per2.most_common():
    print("   %-32s %3d" % (k, v))
print()
print("--- 中文词素频次 TOP 120（术语词典构建依据） ---")
print("   " + "  ".join("%s(%d)" % (k, v) for k, v in mor.most_common(120)))
print()
print("不同词素总数: %d" % len(mor))

json.dump(inv, open(os.path.join(OUT, "inventory.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"mor": mor.most_common(), "ctx": {k: sorted(v) for k, v in mor_ctx.items()}},
          open(os.path.join(OUT, "morphemes.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print()
print("已写 inventory.json / morphemes.json")
