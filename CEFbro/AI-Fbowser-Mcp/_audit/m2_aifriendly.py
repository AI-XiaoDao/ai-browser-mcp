# -*- coding: utf-8 -*-
r"""M2 — AI 代理可用性审计（基于 tools/list 真实返回）

维度:
  A 上下文成本   工具清单总字节/token —— 每次对话都会注入, 直接影响 AI 可用上下文
  B schema 完备性 有无 inputSchema / properties / required / 参数描述
  C 描述质量     长度分布, 是否说明"何时用/返回什么/默认值"
  D 命名一致性   动词前缀分布, 命名族是否规整
  E 冗余重叠     描述高度相似的工具有多少
  F 错误引导     由 M1 探针的结果补充
"""
import json, os, re, sys, collections, io, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
OUT = os.path.dirname(os.path.abspath(__file__))

req = urllib.request.Request(BASE + "/tools/list")
tools = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))["tools"]

W = []
def w(s=""):
    W.append(s)

# ---------- A 上下文成本 ----------
raw = json.dumps({"tools": tools}, ensure_ascii=False, separators=(",", ":"))
utf8 = len(raw.encode("utf-8"))
# 粗略 token 估算: 中文按 1 字 ≈ 0.7 token, ASCII 按 4 字符 ≈ 1 token
cn = len(re.findall(r"[\u4e00-\u9fff]", raw))
other = len(raw) - cn
tokens = int(cn / 0.7) + int(other / 4)
w("=" * 100)
w("M2 AI 代理可用性审计")
w("=" * 100)
w()
w("## A 上下文成本（每次对话都要注入 tools/list）")
w()
w("   工具数            : %d" % len(tools))
w("   tools/list 总字节 : %d (%.1f KB)" % (utf8, utf8 / 1024))
w("   估算 token        : ~%d" % tokens)
desc_bytes = sum(len((t.get("description") or "").encode("utf-8")) for t in tools)
schema_bytes = sum(len(json.dumps(t.get("inputSchema") or {}, ensure_ascii=False).encode("utf-8")) for t in tools)
w("   其中 描述        : %d 字节 (%.0f%%)" % (desc_bytes, 100.0 * desc_bytes / max(1, utf8)))
w("   其中 schema      : %d 字节 (%.0f%%)" % (schema_bytes, 100.0 * schema_bytes / max(1, utf8)))

# ---------- B schema 完备性 ----------
w()
w("## B schema 完备性")
w()
no_schema = [t for t in tools if not (t.get("inputSchema") or {}).get("properties")]
has_req = [t for t in tools if (t.get("inputSchema") or {}).get("required")]
noparamdesc = []
tot_params = 0
for t in tools:
    props = (t.get("inputSchema") or {}).get("properties") or {}
    for pn, pv in props.items():
        tot_params += 1
        if not (pv or {}).get("description"):
            noparamdesc.append((t["name"], pn))
w("   无参数 schema 的工具 : %d / %d" % (len(no_schema), len(tools)))
w("   声明了 required 的    : %d / %d" % (len(has_req), len(tools)))
w("   参数总数             : %d" % tot_params)
w("   缺 description 的参数 : %d (%.0f%%)" % (len(noparamdesc), 100.0 * len(noparamdesc) / max(1, tot_params)))
notype = []
for t in tools:
    for pn, pv in ((t.get("inputSchema") or {}).get("properties") or {}).items():
        if not (pv or {}).get("type"):
            notype.append((t["name"], pn))
w("   缺 type 的参数        : %d" % len(notype))

# ---------- C 描述质量 ----------
w()
w("## C 描述质量")
w()
lens = sorted((len(t.get("description") or ""), t["name"]) for t in tools)
w("   描述长度: 最短 %d / 中位 %d / 最长 %d" % (lens[0][0], lens[len(lens) // 2][0], lens[-1][0]))
w()
w("   [C1] 描述过短(<12字)—— AI 难以判断何时调用: 共 %d" % sum(1 for l, _ in lens if l < 12))
for l, n in lens[:20]:
    if l < 12:
        d = next(t.get("description") or "" for t in tools if t["name"] == n)
        w("        %-42s %2d 字  %s" % (n, l, d))
w()
w("   [C2] 描述过长(>200字)—— 单条占用过大: 共 %d" % sum(1 for l, _ in lens if l > 200))
for l, n in sorted(lens, reverse=True)[:12]:
    if l > 200:
        w("        %-42s %d 字" % (n, l))
w()
KEY_HINT = {"何时用": ["用于", "调用", "建议", "场景", "推荐", "must", "Use "],
            "返回什么": ["返回", "得到", "return", "输出"],
            "默认值": ["默认", "default"],
            "示例": ["示例", "如:", "例如", "e.g"]}
cov = collections.Counter()
for t in tools:
    d = t.get("description") or ""
    for k, pats in KEY_HINT.items():
        if any(p in d for p in pats):
            cov[k] += 1
w()
w("   描述覆盖要素的工具占比:")
for k in KEY_HINT:
    w("        %-8s %3d / %d  (%.0f%%)" % (k, cov[k], len(tools), 100.0 * cov[k] / len(tools)))

# ---------- D 命名一致性 ----------
w()
w("## D 命名一致性")
w()
pref = collections.Counter()
for t in tools:
    n = t["name"]
    m = re.match(r"^browser_([a-z]+)_", n) or re.match(r"^browser_([a-z]+)$", n)
    pref[m.group(1) if m else "(other)"] += 1
w("   第二段前缀分布 (browser_<X>_...):")
for k, v in pref.most_common(28):
    w("        %-16s %d" % (k, v))
VERB = ["get_", "set_", "is_", "can_", "clear_", "delete_", "create_", "close_", "find_",
        "wait", "enable_", "disable_", "print_", "load_", "unload_"]
w()
w("   动词前缀使用:")
for v in VERB:
    c = sum(1 for t in tools if t["name"].startswith("browser_" + v))
    if c:
        w("        browser_%-14s %d" % (v, c))
inhomog = [t["name"] for t in tools if re.match(r"^browser_(get|set)_", t["name"])]
w("   get_/set_ 命名族: %d 个 (具名一致)" % len(inhomog))

# ---------- E 冗余重叠 ----------
w()
w("## E 冗余重叠（描述高度相似 -> AI 选择困难）")
w()

def toks(s):
    return set(re.findall(r"[A-Za-z_]{3,}|[\u4e00-\u9fff]{2,}", s or ""))

pairs = []
for i in range(len(tools)):
    for j in range(i + 1, len(tools)):
        a, b = tools[i], tools[j]
        ta, tb = toks(a.get("description")), toks(b.get("description"))
        if not ta or not tb:
            continue
        jac = len(ta & tb) / float(len(ta | tb))
        if jac >= 0.55:
            pairs.append((jac, a["name"], b["name"]))
pairs.sort(reverse=True)
w("   描述 Jaccard 相似度 >= 0.55 的工具对: %d" % len(pairs))
for jac, a, b in pairs[:25]:
    w("        %.2f  %-40s <-> %s" % (jac, a, b))

# ---------- 落盘 ----------
json.dump({"total_bytes": utf8, "est_tokens": tokens,
           "no_schema": [t["name"] for t in no_schema],
           "no_required": [t["name"] for t in tools],
           "noparamdesc": noparamdesc,
           "pairs": pairs},
          open(os.path.join(OUT, "aifriendly.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

p = os.path.join(OUT, "report_M2_aifriendly.txt")
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(W))
print("written", p)
print("bytes=%d est_tokens=%d noSchema=%d noParamDesc=%d dupPairs=%d"
      % (utf8, tokens, len(no_schema), len(noparamdesc), len(pairs)))
