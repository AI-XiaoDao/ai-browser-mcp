# -*- coding: utf-8 -*-
r"""A9c — 火山成员名 -> C++ 输出名 权威映射（迭代式精化对齐）

问题: 纯结构对齐会把"填表分派(4字)/逆向分派(4字)"、"缓存过滤器/篡改过滤器"
      这类**音节数相同但内容不同**的类互换。
方案: EM 式迭代
      R0 结构对齐 -> 取"高分且唯一最优"的对建立种子字典
      Rk 用字典做**内容校验**重新对齐 (已知字必须拼音一致) -> 收敛
最后用收敛字典音译生成全部成员输出名，并标注置信度。
"""
import sys, re, os, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

GEN = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\generated-cpp\release-x64"
OUT = os.path.dirname(os.path.abspath(__file__))


def syllables(cpp):
    """切分为 token: ASCII 缩写串 / 单个拼音音节 / '_' / 数字串。
    关键: 连续大写串后若紧跟小写, 则末位大写属于下一个音节
          (如 'MCPMingLingFuWuQi' -> MCP + Ming + Ling + Fu + Wu + Qi, 而非 MCPM+ing+...)"""
    if cpp.startswith("rg_"):
        cpp = cpp[3:]
    toks, i, n = [], 0, len(cpp)
    while i < n:
        c = cpp[i]
        if c == "_":
            toks.append("_"); i += 1; continue
        if c.isdigit():
            j = i
            while j < n and cpp[j].isdigit():
                j += 1
            toks.append(cpp[i:j]); i = j; continue
        if c.isupper():
            j = i
            while j < n and cpp[j].isupper():
                j += 1
            run = j - i
            if run >= 2:
                if j < n and cpp[j].islower():
                    # 末位大写归属下一音节
                    if run - 1 >= 2:
                        toks.append(cpp[i:j - 1]); i = j - 1; continue
                    # 缩写仅 1 位, 整体按音节处理
                    k = j
                    while k < n and cpp[k].islower():
                        k += 1
                    toks.append(cpp[i:k]); i = k; continue
                toks.append(cpp[i:j]); i = j; continue
            k = i + 1
            while k < n and cpp[k].islower():
                k += 1
            toks.append(cpp[i:k]); i = k; continue
        j = i
        while j < n and cpp[j].islower():
            j += 1
        toks.append(cpp[i:j]); i = j
    return toks


def wsv_tokens(name):
    toks, i = [], 0
    while i < len(name):
        c = name[i]
        if c == "_":
            toks.append("_"); i += 1; continue
        if re.match(r"[A-Za-z]", c):
            j = i
            while j < len(name) and re.match(r"[A-Za-z0-9]", name[j]):
                j += 1
            toks.append(name[i:j]); i = j; continue
        if c.isdigit():
            j = i
            while j < len(name) and name[j].isdigit():
                j += 1
            toks.append(name[i:j]); i = j; continue
        toks.append(c); i += 1
    return toks


def align_parts(wname, hname):
    """把 火山名 与 C++名 逐位配对; 返回 [(汉字, 音节)] 或 None(不兼容)"""
    wt = wsv_tokens(wname)
    ht = syllables(hname)
    while ht and ht[-1].isdigit():
        ht.pop()
    out, wi, hi = [], 0, 0
    while wi < len(wt) and hi < len(ht):
        w, h = wt[wi], ht[hi]
        if w == "_":
            if h != "_":
                return None
            wi += 1; hi += 1; continue
        if re.match(r"^[A-Za-z]", w):
            joined, hj = "", hi
            while hj < len(ht):
                cand = joined + ht[hj]
                if len(cand) <= len(w) and w.upper().startswith(cand.upper()):
                    joined = cand; hj += 1
                    if joined.upper() == w.upper():
                        break
                else:
                    break
            if joined.upper() != w.upper():
                return None
            wi += 1; hi = hj; continue
        if re.match(r"^[0-9]", w):
            joined, hj = "", hi
            while hj < len(ht) and ht[hj].isdigit():
                joined += ht[hj]; hj += 1
            if joined != w:
                return None
            wi += 1; hi = hj; continue
        if not re.match(r"^[A-Z][a-z]", h):
            return None
        out.append((w, h))
        wi += 1; hi += 1
    if wi == len(wt) and hi == len(ht):
        return out
    return None


def compatible(wname, hname, det=None):
    parts = align_parts(wname, hname)
    if parts is None:
        return False
    if det:
        for ch, syl in parts:
            if ch in det and det[ch] != syl:
                return False
    return True


def align_lcs(W, H, det=None):
    n, m = len(W), len(H)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = max(dp[i + 1][j], dp[i][j + 1])
            if compatible(W[i], H[j], det):
                best = max(best, 1 + dp[i + 1][j + 1])
            dp[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if compatible(W[i], H[j], det) and dp[i][j] == 1 + dp[i + 1][j + 1]:
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
            classes[cls] = {"file": f, "line": i + 1, "methods": [], "vars": []}
            continue
        if cls is None or da[i] != 1:
            continue
        mm = re.match(r"\s*方法\s+(\S+)", clean)
        if mm:
            classes[cls]["methods"].append((mm.group(1), i)); continue
        mv = re.match(r"\s*(?:变量|常量)\s+(\S+)", clean)
        if mv:
            classes[cls]["vars"].append((mv.group(1), i))

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
    cn = cm.group(1)
    stop = txt.find("inline_ %s ()" % cn)
    body = txt[:stop] if stop > 0 else txt
    ms = [(m.group(1), m.group(2)) for m in re.finditer(
        r"(?:static\s+)?[\w:<>&\s\*]+?\s+(?:CALLBACK\s+)?(rg_[A-Za-z0-9_]+)\s*\(([^)]*)\)\s*;", body)]
    ms = [x for x in ms if x[0] != cn and not x[0].startswith("DECLARE")]
    vp = txt[stop:] if stop > 0 else ""
    vs = re.findall(r"static\s+[\w:<>&\s\*]+?\s+(rg_[A-Za-z0-9_]+)\s*;", vp)
    hdrs[fn] = {"class": cn, "methods": ms, "vars": vs}


def norm_wsv_class(n):
    return n[2:] if n.startswith("类_") else n


def norm_cpp_class(n):
    if n.startswith("rg_"):
        n = n[3:]
    if n.startswith("class_"):
        n = n[6:]
    return n


def cand_pairs(det):
    """返回候选 (score, 火山类, 头文件, pairs)。"
    编译器对过长类名会**缩写**拼音(如 观察者->gchzh)，故类名不兼容时
    仍允许以方法名高相似度(>=0.8)对齐。"""
    res = []
    for c, d in classes.items():
        if not d["methods"]:
            continue
        W = [x[0] for x in d["methods"]]
        for fn, h in hdrs.items():
            if not h["methods"]:
                continue
            if c == "启动类" and h["class"] == "rg_startup_class":
                ok = True
            else:
                ok = compatible(norm_wsv_class(c), "rg_" + norm_cpp_class(h["class"]), det)
            H = [x[0] for x in h["methods"]]
            p = align_lcs(W, H, det)
            if not p:
                continue
            ratio = len(p) / float(len(W))
            if not ok and ratio < 0.8:
                continue          # 类名不兼容时要求高相似度作证据
            res.append((len(p), c, fn, p))
    return res


def bijection(cands, ratios=(0.5,)):
    cands = sorted(cands, key=lambda x: -x[0])
    al, uh, uc = {}, set(), set()
    for (sc, c, fn, p) in cands:
        if c in uc or fn in uh:
            continue
        if sc < max(1, int(ratios[0] * len(classes[c]["methods"]))):
            continue
        uc.add(c); uh.add(fn); al[c] = (fn, p, sc)
    return al


def build_dict(al, min_score=3):
    cm = collections.defaultdict(collections.Counter)
    for c, (fn, p, sc) in al.items():
        if sc < min_score:
            continue
        d, h = classes[c], hdrs[fn]
        for (wi, hi) in p:
            parts = align_parts(d["methods"][wi][0], h["methods"][hi][0])
            if parts:
                for ch, syl in parts:
                    cm[ch][syl] += 1
    return {ch: cnt.most_common(1)[0][0] for ch, cnt in cm.items()}, cm


# ---------- EM ----------
det = {}
history = []
for rnd in range(6):
    al = bijection(cand_pairs(det))
    nd, cm = build_dict(al)
    changed = sum(1 for k in set(nd) | set(det) if nd.get(k) != det.get(k))
    history.append((rnd, len(al), len(nd), changed))
    det = nd
    if changed == 0:
        break

conflicts = {ch: cnt for ch, cnt in cm.items() if len(cnt) > 1}

# 最终对齐（用收敛字典，允许较低阈值以覆盖陈旧快照）
final = bijection(cand_pairs(det), ratios=(0.3,))

W = []
def w(s=""):
    W.append(s)
w("=" * 108)
w("A9c — 火山成员名 -> C++ 输出名 权威映射 (迭代式内容校验对齐)")
w("=" * 108)
w()
w("EM 迭代历史 (轮次, 已对齐类数, 字典字数, 字典变化数):")
for h in history:
    w("   R%d  aligned=%d  dict=%d  changed=%d" % h)
w()
w("最终对齐: %d / %d 个类" % (len(final), len(classes)))
w("%-34s %-42s %6s %6s %6s" % ("火山类", "C++类", "wsv方法", "头方法", "命中"))
w("-" * 108)
for c, (fn, p, sc) in sorted(final.items(), key=lambda x: -x[1][2]):
    w("%-34s %-42s %6d %6d %6d" % (c, hdrs[fn]["class"], len(classes[c]["methods"]),
                                    len(hdrs[fn]["methods"]), sc))
nolo = [c for c in classes if c not in final]
w()
w("未对齐: %s" % ", ".join(nolo))
w()
w("字典: %d 字, 其中冲突 %d 个" % (len(det), len(conflicts)))
for ch, cnt in sorted(conflicts.items(), key=lambda x: -sum(x[1].values()))[:20]:
    w("   %s -> %s" % (ch, dict(cnt.most_common(4))))

json.dump(det, open(os.path.join(OUT, "char_pinyin.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def translit(name):
    out, unk, low = [], [], False
    for tok in wsv_tokens(name):
        if tok == "_":
            out.append("_")
        elif re.match(r"^[A-Za-z0-9]", tok):
            out.append(tok)
        else:
            s = det.get(tok)
            if s is None:
                unk.append(tok); out.append("?" + tok + "?")
            else:
                out.append(s)
                if tok in conflicts:
                    low = True
    return "".join(out), unk, low

# ---------- 完整映射 ----------
w()
w("=" * 108)
w("完整映射表 (provenance: 头核对 = 与生成头逐字一致; 字典推导 = 按收敛字典音译)")
w("=" * 108)
full = {}
stat = collections.Counter()
for c, d in classes.items():
    fn = final.get(c, (None, None, 0))[0]
    ns = "rg_volcano_app"
    cn = hdrs[fn]["class"] if fn else "rg_" + translit(c)[0]
    idx2name = {}
    if fn:
        for (wi, hi) in final[c][1]:
            idx2name[d["methods"][wi][0]] = hdrs[fn]["methods"][hi][0]
    W.append("")
    w("### 类 %s  (%s 第%d行)   ->  %s::%s" % (c, d["file"], d["line"], ns, cn))
    if d["methods"]:
        w("    %-42s %-6s %-48s %s" % ("火山方法", "行", "C++ 输出名", "来源"))
        w("    " + "-" * 102)
        for (mn, mi) in d["methods"]:
            if mn in idx2name:
                cpp, src = idx2name[mn], "头核对"; stat["核对"] += 1
            else:
                body, unk, low = translit(mn)
                cpp = "rg_" + body
                src = "字典推导" + ("[未知字:%s]" % "".join(unk) if unk else ("[多音字]" if low else ""))
                stat["推导"] += 1
                if unk:
                    stat["有未知字"] += 1
            full["%s.%s" % (c, mn)] = {"cls": "%s::%s" % (ns, cn), "cpp": cpp,
                                       "file": d["file"], "line": mi + 1, "src": src}
            w("    %-42s %-6d %-48s %s" % (mn, mi + 1, cpp, src))
    if d["vars"]:
        w("    -- 成员变量/常量 --")
        for (vn, vi) in d["vars"]:
            cand = None
            if fn:
                for hv in hdrs[fn]["vars"]:
                    if compatible(vn, hv, det):
                        cand = hv; break
            if cand:
                cpp, src = cand, "头核对"; stat["核对"] += 1
            else:
                body, unk, low = translit(vn)
                cpp = "rg_" + body
                src = "字典推导" + ("[未知字:%s]" % "".join(unk) if unk else ("[多音字]" if low else ""))
                stat["推导"] += 1
                if unk:
                    stat["有未知字"] += 1
            full["%s.[变量]%s" % (c, vn)] = {"cls": "%s::%s" % (ns, cn), "cpp": cpp,
                                             "file": d["file"], "line": vi + 1, "src": src}
            w("    %-42s %-6d %-48s %s" % ("[变量] " + vn, vi + 1, cpp, src))

w()
w("=" * 108)
w("统计: 头核对 %d | 字典推导 %d (其中含未知字 %d) | 映射总数 %d"
  % (stat["核对"], stat["推导"], stat["有未知字"], len(full)))
w("=" * 108)

json.dump(full, open(os.path.join(OUT, "symbol_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
p = out_report("report_A9_symbols.txt", "\n".join(W))
print("written", p)
print("aligned %d/%d | dict %d (conflicts %d) | map %d | verified %d derived %d unknown-char %d"
      % (len(final), len(classes), len(det), len(conflicts), len(full),
         stat["核对"], stat["推导"], stat["有未知字"]))
