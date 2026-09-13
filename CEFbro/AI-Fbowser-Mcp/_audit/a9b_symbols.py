# -*- coding: utf-8 -*-
r"""A9b — 建立 火山成员名 -> C++ 输出名 的权威映射

方法:
  1) 从 .wsv 取每个类的 方法/变量(按定义顺序)
  2) 从 generated-cpp/*.h 取 rg_ 符号(按声明顺序)
  3) 用"兼容性谓词 + 最长公共子序列"做单调对齐(容忍生成快照陈旧导致的增删)
       兼容性谓词: ASCII 连续段(纯大写或纯小写)必须相等,
                   且汉字段的字数 == 对应拼音段的音节数
  4) 由对齐结果反推 汉字->拼音音节 字典, 并用一致性(每字唯一音节)自校验
  5) 用字典为**快照中不存在**的新成员推导输出名
"""
import sys, re, os, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

GEN = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\generated-cpp\release-x64"
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- 名称切分 ----------
def syllables(cpp):
    """把 C++ 名(去 rg_ 前缀)切成 token: ASCII 串 或 单个拼音音节"""
    if cpp.startswith("rg_"):
        cpp = cpp[3:]
    toks = []
    i = 0
    while i < len(cpp):
        c = cpp[i]
        if c == "_":
            toks.append("_"); i += 1; continue
        if c.isdigit():
            j = i
            while j < len(cpp) and cpp[j].isdigit():
                j += 1
            toks.append(cpp[i:j]); i = j; continue
        if c.isupper():
            # 连续大写 = ASCII 缩写段
            j = i
            while j < len(cpp) and cpp[j].isupper():
                j += 1
            if j - i >= 2:
                toks.append(cpp[i:j]); i = j; continue
            # 单大写 + 后续小写 = 一个拼音音节
            j = i + 1
            while j < len(cpp) and cpp[j].islower():
                j += 1
            toks.append(cpp[i:j]); i = j; continue
        # 小写开头: 归入前一音节或自成一 token
        j = i
        while j < len(cpp) and cpp[j].islower():
            j += 1
        toks.append(cpp[i:j]); i = j
    return toks


def wsv_tokens(name):
    """把火山名切成 token: '_' / ASCII 串 / 单汉字"""
    toks = []
    i = 0
    while i < len(name):
        c = name[i]
        if c == "_":
            toks.append("_"); i += 1; continue
        if re.match(r"[A-Za-z]", c):
            j = i
            while j < len(name) and re.match(r"[A-Za-z0-9]", name[j]):
                j += 1
            toks.append(name[i:j]); i = j; continue
        if re.match(r"[0-9]", c):
            j = i
            while j < len(name) and name[j].isdigit():
                j += 1
            toks.append(name[i:j]); i = j; continue
        toks.append(c); i += 1
    return toks


def compatible(wname, hname):
    """判断 火山名 与 C++符号名 是否可能对应"""
    wt = wsv_tokens(wname)
    ht = syllables(hname)
    # 去掉尾部数字后缀(C++ 侧重名消歧)
    while ht and ht[-1].isdigit():
        ht.pop()
    wi = hi = 0
    while wi < len(wt) and hi < len(ht):
        w, h = wt[wi], ht[hi]
        if w == "_":
            if h != "_":
                return False
            wi += 1; hi += 1; continue
        if re.match(r"^[A-Za-z]", w):
            # ASCII: C++ 侧可能被切成多个 token(如 MCP -> MCP; 或 MFCP -> M,C,P)
            joined = ""
            hj = hi
            while hj < len(ht) and ht[hj] != "_" and not re.match(r"^[A-Z][a-z]", ht[hj]):
                joined += ht[hj]; hj += 1
            if joined.upper() != w.upper():
                return False
            wi += 1; hi = hj; continue
        if re.match(r"^[0-9]", w):
            joined = ""
            hj = hi
            while hj < len(ht) and ht[hj].isdigit():
                joined += ht[hj]; hj += 1
            if joined != w:
                return False
            wi += 1; hi = hj; continue
        # 单汉字: 需要恰好一个拼音音节
        if not re.match(r"^[A-Z][a-z]", h):
            return False
        wi += 1; hi += 1
    return wi == len(wt) and hi == len(ht)


def align_lcs(W, H):
    """W/H 为名字列表; 返回匹配对 [(wi, hi)]，要求 ASCII/结构兼容"""
    n, m = len(W), len(H)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = max(dp[i + 1][j], dp[i][j + 1])
            if compatible(W[i], H[j]):
                best = max(best, 1 + dp[i + 1][j + 1])
            dp[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if compatible(W[i], H[j]) and dp[i][j] == 1 + dp[i + 1][j + 1]:
            pairs.append((i, j)); i += 1; j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs

# ---------- 读 .wsv ----------
classes = collections.OrderedDict()
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
            classes[cls] = {"file": f, "line": i + 1, "methods": [], "vars": [], "ci": i}
            continue
        if cls is None or da[i] != 1:
            continue
        mm = re.match(r"\s*方法\s+(\S+)", clean)
        if mm:
            classes[cls]["methods"].append((mm.group(1), i)); continue
        mv = re.match(r"\s*(?:变量|常量)\s+(\S+)", clean)
        if mv:
            classes[cls]["vars"].append((mv.group(1), i))

# 事件接收方法 (方法名_事件名 形式) 已含在 methods 中

# ---------- 读生成头 ----------
hdrs = {}
for fn in sorted(os.listdir(GEN)):
    if not (fn.startswith("vcls_rg_") and fn.endswith(".h")):
        continue
    txt = open(os.path.join(GEN, fn), encoding="utf-8", errors="replace").read()
    if "rg_volcano_app" not in txt:
        continue
    cm = re.search(r"class\s+(rg_[A-Za-z0-9_]+)\s*:", txt)
    if not cm:
        continue
    cname = cm.group(1)
    stop = txt.find("inline_ %s ()" % cname)
    body = txt[:stop] if stop > 0 else txt
    ms = [(m.group(1), m.group(2)) for m in
          re.finditer(r"(?:static\s+)?[\w:<>&\s\*]+?\s+(?:CALLBACK\s+)?(rg_[A-Za-z0-9_]+)\s*\(([^)]*)\)\s*;", body)]
    ms = [x for x in ms if x[0] != cname and not x[0].startswith("DECLARE")]
    vp = txt[stop:] if stop > 0 else ""
    vs = re.findall(r"static\s+[\w:<>&\s\*]+?\s+(rg_[A-Za-z0-9_]+)\s*;", vp)
    hdrs[fn] = {"class": cname, "methods": ms, "vars": vs}

# ---------- 对齐 (类 -> 头): 类名兼容性门禁 + 全局一一对应 ----------
def norm_wsv_class(n):
    return n[2:] if n.startswith("类_") else n

def norm_cpp_class(n):
    if n.startswith("rg_"):
        n = n[3:]
    if n.startswith("class_"):
        n = n[6:]
    return n

cand = []
for c, d in classes.items():
    if not d["methods"]:
        continue
    W = [x[0] for x in d["methods"]]
    for fn, h in hdrs.items():
        if not h["methods"]:
            continue
        # 特例: 启动类 -> 编译器固定使用 rg_startup_class
        if c == "启动类" and h["class"] == "rg_startup_class":
            ok = True
        else:
            ok = compatible(norm_wsv_class(c), "rg_" + norm_cpp_class(h["class"]))
        if not ok:
            continue
        H = [x[0] for x in h["methods"]]
        pairs = align_lcs(W, H)
        if pairs:
            cand.append((len(pairs), c, fn, pairs))

cand.sort(key=lambda x: -x[0])
class_align = {}
used_h, used_c = set(), set()
for (score, c, fn, pairs) in cand:
    if c in used_c or fn in used_h:
        continue
    if score < max(1, int(0.5 * len(classes[c]["methods"]))):
        continue
    used_c.add(c); used_h.add(fn)
    class_align[c] = (fn, pairs, score)

# ---------- 建 汉字->音节 字典 ----------
char_map = collections.defaultdict(collections.Counter)
conflicts = collections.defaultdict(collections.Counter)
for c, (fn, pairs, sc) in class_align.items():
    d, h = classes[c], hdrs[fn]
    for (wi, hi) in pairs:
        wn = d["methods"][wi][0]
        hn = h["methods"][hi][0]
        wt, ht = wsv_tokens(wn), syllables(hn)
        while ht and ht[-1].isdigit():
            ht.pop()
        # 逐位对齐
        wi2 = hi2 = 0
        while wi2 < len(wt) and hi2 < len(ht):
            w, hh = wt[wi2], ht[hi2]
            if w == "_":
                wi2 += 1; hi2 += 1; continue
            if re.match(r"^[A-Za-z0-9]", w):
                joined = ""
                hj = hi2
                while hj < len(ht) and ht[hj] != "_" and not re.match(r"^[A-Z][a-z]", ht[hj]):
                    joined += ht[hj]; hj += 1
                wi2 += 1; hi2 = hj; continue
            if re.match(r"^[A-Z][a-z]", hh):
                char_map[w][hh] += 1
                wi2 += 1; hi2 += 1; continue
            break

det = {}
for ch, cnt in char_map.items():
    if len(cnt) == 1:
        det[ch] = cnt.most_common(1)[0][0]
    else:
        # 多值: 取最高频, 记冲突
        det[ch] = cnt.most_common(1)[0][0]
        conflicts[ch] = cnt

def translit(name):
    """用字典把火山名音译为输出名主体 (不含 rg_ 前缀)"""
    out = []
    unknown = []
    for tok in wsv_tokens(name):
        if tok == "_":
            out.append("_")
        elif re.match(r"^[A-Za-z0-9]", tok):
            out.append(tok)
        else:
            s = det.get(tok)
            if s is None:
                unknown.append(tok); out.append("?" + tok + "?")
            else:
                out.append(s)
    return "".join(out), unknown

# ---------- 输出 ----------
W = []
def w(s=""):
    W.append(s)
w("=" * 104)
w("A9b — 火山成员名 -> C++ 输出名 映射 (正向: 字典音译 / 反向: 生成头核对)")
w("=" * 104)
w()
w("类对齐结果: %d / %d 个类成功对齐到生成头" % (len(class_align), len(classes)))
w("%-36s %-44s %6s %6s %6s" % ("火山类", "生成头(C++类)", "wsv方法", "头方法", "命中"))
w("-" * 104)
for c, (fn, pairs, sc) in class_align.items():
    w("%-36s %-44s %6d %6d %6d" % (c, hdrs[fn]["class"], len(classes[c]["methods"]),
                                    len(hdrs[fn]["methods"]), sc))
nol = [c for c in classes if c not in class_align]
if nol:
    w()
    w("未对齐的类(无方法或生成头缺失): %s" % ", ".join(nol))

w()
w("汉字->拼音音节 字典: %d 个字" % len(det))
w("存在多音冲突的字: %d 个" % len(conflicts))
for ch, cnt in sorted(conflicts.items(), key=lambda x: -sum(x[1].values()))[:25]:
    w("   %s -> %s" % (ch, dict(cnt.most_common(3))))

json.dump(det, open(os.path.join(OUT, "char_pinyin.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- 生成完整映射 ----------
w()
w("=" * 104)
w("完整映射表")
w("=" * 104)
full = {}
stat = collections.Counter()
for c, d in classes.items():
    fn = class_align.get(c, (None, None, 0))[0]
    ns = "rg_volcano_app"
    cn = hdrs[fn]["class"] if fn else ("rg_" + translit(c)[0])
    W.append("")
    w("### 类 %s   (%s 第%d行)" % (c, d["file"], d["line"]))
    w("    C++: namespace %s { class %s }" % (ns, cn))
    if d["methods"]:
        w("    %-44s %-8s %-46s %s" % ("火山方法", "wsv行", "C++ 输出名", "来源"))
        w("    " + "-" * 100)
        # 建 wsv方法名 -> C++名
        idx2name = {}
        if fn:
            for (wi, hi) in class_align[c][1]:
                idx2name[d["methods"][wi][0]] = hdrs[fn]["methods"][hi][0]
        for (mn, mi) in d["methods"]:
            if mn in idx2name:
                cpp, src = idx2name[mn], "生成头核对"
                stat["核对"] += 1
            else:
                body, unk = translit(mn)
                cpp, src = "rg_" + body, "字典推导" + ("(含未知字!)" if unk else "")
                stat["推导"] += 1
            full["%s.%s" % (c, mn)] = {"cpp_class": "%s::%s" % (ns, cn), "cpp": cpp,
                                       "file": d["file"], "line": mi + 1, "source": src}
            w("    %-44s %-8d %-46s %s" % (mn, mi + 1, cpp, src))
    if d["vars"]:
        w("    -- 变量/常量 --")
        hidx = {}
        if fn:
            for (wi, hi) in (class_align.get(c, (None, [], 0))[1] or []):
                pass  # 变量单独按名字匹配
            hv = {v: v for v in hdrs[fn]["vars"]}
        for (vn, vi) in d["vars"]:
            cand = None
            if fn:
                for hv in hdrs[fn]["vars"]:
                    if compatible(vn, hv):
                        cand = hv; break
            if cand:
                cpp, src = cand, "生成头核对"
            else:
                body, unk = translit(vn)
                cpp, src = "rg_" + body, "字典推导" + ("(含未知字!)" if unk else "")
            full["%s.%s" % (c, vn)] = {"cpp_class": "%s::%s" % (ns, cn), "cpp": cpp,
                                       "file": d["file"], "line": vi + 1, "source": src}
            w("    %-44s %-8d %-46s %s" % ("[变量] " + vn, vi + 1, cpp, src))
    w("")

w("=" * 104)
w("统计: 生成头核对 %d 条 | 字典推导 %d 条 | 合计 %d 条" % (stat["核对"], stat["推导"], len(full)))
w("=" * 104)

json.dump(full, open(os.path.join(OUT, "symbol_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
p = out_report("report_A9_symbols.txt", "\n".join(W))
print("written", p)
print("classes aligned %d/%d | chars %d | conflicts %d | map %d (verified %d, derived %d)"
      % (len(class_align), len(classes), len(det), len(conflicts), len(full),
         stat["核对"], stat["推导"]))
