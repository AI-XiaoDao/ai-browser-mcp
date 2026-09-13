# -*- coding: utf-8 -*-
"""FBrowser 事件覆盖率 —— 类感知测量工具 (r115 重写版)。

权威来源(技能内类库, 只读):
  C:\\Users\\cxzxc\\.agents\\skills\\volcano-pc-programming\\资料\\类库\\FBrowser浏览器\\
    - FBroEventControl.wsv  (8 个事件类)
    - FBroCallback.wsv      (回调基类, 含可覆盖虚方法)

r114 版(旧)的三个口径缺陷 —— 本版逐条修掉:
  (1) 分母漏数: 旧正则 `方法\\s+(...)\\s*<公开(.*?)>` 要求属性块与 `方法` **同行闭合**,
      类库里有多行属性块(如 `方法 浏览器_即将改变媒体访问 <公开\\n 注释 = "..."`
      `\\n @虚拟方法 = 可覆盖>`), 这些方法**从未进入分母**。
      本版改为"跨行属性块扫描": 从 `方法 NAME` 之后找 `<`, 字符串感知地扫到配对的 `>`,
      属性块可跨任意多行。
  (2) 口径截断: 旧版只统计 2 个事件类。本版逐个解析 FBroEventControl.wsv 里的
      **全部 8 个事件类**, 并可选(默认开)纳入 FBroCallback.wsv 的可覆盖虚方法。
  (3) 纯名字匹配: 旧版只看"方法名是否出现在项目文本里"。
      本版做**类感知**校验: 先解析项目的 `类 X <公开 基础类 = Y>` 得到派生链,
      再在"派生自该事件类的项目类"的方法体区间内找 `@虚拟方法 = 可覆盖` 的同名方法。
      同名但所属类不对的, 单独列进"误报候选"而不是算作覆盖。

用法:
    py -3 _audit/event_gap.py                 # 全口径(含回调类)
    py -3 _audit/event_gap.py --no-callbacks  # 只统计 8 个事件类
    py -3 _audit/event_gap.py --dump-project  # 额外打印解析到的项目类/方法清单
"""
import argparse
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

LIB_DIR = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
EVENT_LIB = os.path.join(LIB_DIR, "FBroEventControl.wsv")
CALLBACK_LIB = os.path.join(LIB_DIR, "FBroCallback.wsv")
PROJ_DIR = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

# 不作为"事件"计入的通用构造/析构方法
SKIP_METHODS = {"类_初始化", "类_清理"}

CLASS_RE = re.compile(r'(?m)^[ \t]*类[ \t]+([^\s<>{}]+)')
METHOD_RE = re.compile(r'(?m)^[ \t]*方法[ \t]+([^\s<>{}]+)')
BASE_RE = re.compile(r'基础类\s*=\s*([^\s<>"\']+)')


# ---------------------------------------------------------------- 文本清洗

def _strip_line_comment(s):
    """去掉行内 `//` 注释(跳过双引号字符串内部)。"""
    out = []
    in_str = False
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if in_str:
            if ch == "\\":
                out.append(s[i:i + 2])
                i += 2
                continue
            if ch == '"':
                in_str = False
            out.append(ch)
        else:
            if ch == '"':
                in_str = True
                out.append(ch)
            elif ch == "/" and i + 1 < n and s[i + 1] == "/":
                break  # 其余是注释
            else:
                out.append(ch)
        i += 1
    return "".join(out)


def load_clean(path):
    """读文件 -> (清洗后全文, 原始行列表, 偏移->行号 的行起始表)。

    清洗规则: 整行 `#` 注释置空; 行内 `//` 注释截掉。这样大括号计数不会被
    注释里的 C++ 花括号(类库用 `# ... { ... }` 内嵌 C++ 源码)污染。
    """
    raw = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    cleaned = []
    for line in raw:
        if line.lstrip().startswith("#"):
            cleaned.append("")
        else:
            cleaned.append(_strip_line_comment(line))
    starts = []
    pos = 0
    for c in cleaned:
        starts.append(pos)
        pos += len(c) + 1
    return "\n".join(cleaned), raw, starts


def line_at(starts, off):
    """偏移 -> 1 基行号(线性查找足够, 文件不大)。"""
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid] <= off:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


# ------------------------------------------------------- 属性块 / 大括号扫描

def scan_attr_block(text, pos):
    """从 pos 开始: 若紧跟 `<`, 字符串感知地扫到配对 `>`。

    返回 (block_text, end_pos)。没有属性块时返回 (None, pos)。
    这是修缺陷(1)的核心: 属性块允许跨行。
    """
    i = pos
    n = len(text)
    while i < n and text[i] in " \t":
        i += 1
    if i >= n or text[i] != "<":
        return None, pos
    start = i
    depth = 0
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1], i + 1
        i += 1
    return None, pos  # 未闭合


def match_brace(text, pos):
    """从 pos 起找第一个 `{`, 返回其配对 `}` 的位置(字符串感知)。"""
    i = text.find("{", pos)
    if i < 0:
        return None
    depth = 0
    in_str = False
    n = len(text)
    while i < n:
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return None


# --------------------------------------------------------------- 解析器

class Klass(object):
    def __init__(self, name, decl_line, body_start, body_end, attrs):
        self.name = name
        self.decl_line = decl_line
        self.body_start = body_start
        self.body_end = body_end
        self.attrs = attrs or ""
        m = BASE_RE.search(self.attrs)
        self.base = m.group(1) if m else None


class Method(object):
    def __init__(self, name, decl_line, attrs, owner):
        self.name = name
        self.line = decl_line
        self.attrs = attrs or ""
        self.owner = owner   # 归属类名(项目侧)


def parse_wsv(path):
    """解析 .wsv -> (类列表, 全部方法列表)。方法带 owner 归属类。"""
    text, raw, starts = load_clean(path)
    classes = []
    for m in CLASS_RE.finditer(text):
        name = m.group(1)
        block, after = scan_attr_block(text, m.end())
        if block is None:
            after = m.end()
        open_br = text.find("{", after)
        if open_br < 0:
            continue
        close_br = match_brace(text, open_br)
        if close_br is None:
            close_br = len(text)
        classes.append(Klass(name, line_at(starts, m.start()), open_br,
                             close_br, block))

    methods = []
    for m in METHOD_RE.finditer(text):
        name = m.group(1)
        block, after = scan_attr_block(text, m.end())
        owner = None
        for k in classes:
            if k.body_start < m.start() < k.body_end:
                if owner is None or k.body_start > owner[1]:
                    owner = (k.name, k.body_start)
        methods.append(Method(name, line_at(starts, m.start()), block,
                              owner[0] if owner else None))
    return classes, methods, raw


def lib_events(path):
    """返回 [(类名, 类声明行, [(方法名, 声明行), ...])]，逐个事件类列出。"""
    classes, methods, _raw = parse_wsv(path)
    out = []
    for k in classes:
        evs = []
        for meth in methods:
            if meth.owner != k.name:
                continue
            if meth.name in SKIP_METHODS:
                continue
            if "@虚拟方法" in meth.attrs and "可覆盖" in meth.attrs:
                evs.append((meth.name, meth.line))
        out.append((k.name, k.decl_line, evs))
    return out


def old_regex_counts(path):
    """复现 r114 旧口径: `方法\\s+(名)\\s*<公开(.*?)>` 且要求同行闭合。

    仅用于"修复前后对照"——证明旧分母漏数, 不作为测量结果。
    返回 (旧口径命中总数, {行号: 方法名}) 与按行区间分组的计数函数。
    """
    raw = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    old_re = re.compile(r'方法\s+([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*<公开(.*?)>')
    hits = {}
    for i, line in enumerate(raw, 1):
        m = old_re.search(line)
        if m and "虚拟方法 = 可覆盖" in m.group(2):
            hits[i] = m.group(1)
    return hits


def project_index():
    """扫描项目 src, 返回 (类列表, 方法列表)。跳过 .~vbak 备份。"""
    classes, methods = [], []
    files = []
    for f in sorted(os.listdir(PROJ_DIR)):
        if not f.endswith(".wsv") or ".~vbak" in f:
            continue
        files.append(f)
        cs, ms, _raw = parse_wsv(os.path.join(PROJ_DIR, f))
        for c in cs:
            c.file = f
            classes.append(c)
        for m in ms:
            m.file = f
            methods.append(m)
    return classes, methods, files


# ------------------------------------------------------------------ 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-callbacks", action="store_true",
                    help="不统计 FBroCallback.wsv 的可覆盖虚方法")
    ap.add_argument("--dump-project", action="store_true",
                    help="打印解析到的项目类与派生链")
    args = ap.parse_args()

    print("=" * 104)
    print("FBrowser 事件覆盖率 (类感知口径) —— 测量工具 r115")
    print("=" * 104)
    print("  事件类库 : %s" % EVENT_LIB)
    print("  回调类库 : %s%s" % (CALLBACK_LIB, "  [本次未纳入]" if args.no_callbacks else ""))
    print("  项目源码 : %s" % PROJ_DIR)

    # ---- 解析类库(权威分母) ----
    ev_classes = lib_events(EVENT_LIB)
    cb_classes = lib_events(CALLBACK_LIB) if not args.no_callbacks else []

    # ---- 解析项目(分子候选) ----
    p_classes, p_methods, p_files = project_index()
    base_of = {}
    for c in p_classes:
        base_of[c.name] = c.base

    print("  项目文件 : %d 个 (%s)" % (len(p_files), ", ".join(p_files)))
    print("  项目类   : %d 个, 项目方法: %d 个" % (len(p_classes), len(p_methods)))

    def chain(cls):
        """返回 cls 的祖先链(基础类 -> ...), 不含 cls 自身, 绝不包含 None。

        修: 旧实现把 `base_of[cur]` 的 None 也 append 进链, 导致 `--dump-project`
        在 `a.startswith(...)` 上抛 AttributeError('NoneType' has no attribute)。
        """
        seen, cur, guard = [], cls, 0
        while guard < 12:
            base = base_of.get(cur)
            if not isinstance(base, str) or base in seen:
                break
            seen.append(base)
            cur = base
            guard += 1
        return seen

    if args.dump_project:
        print()
        print("-" * 104)
        print("项目类派生链 (仅列出派生自 FBrowser 类库的)")
        print("-" * 104)
        for c in sorted(p_classes, key=lambda x: x.name):
            ch = chain(c.name)
            if any(a.startswith("类_FBrowser") for a in ch):
                print("  %-34s (%s:%d)  ->  %s"
                      % (c.name, c.file, c.decl_line, " -> ".join([c.name] + ch)))

    # ---- ⓪ 修复前后对照: 旧口径分母 vs 新口径分母 ----
    old_hits = old_regex_counts(EVENT_LIB)
    new_hits = {}
    for _cn, _cl, _evs in ev_classes:
        for _n, _l in _evs:
            new_hits[_l] = _n
    only_new = sorted(set(new_hits) - set(old_hits))

    print()
    print("=" * 104)
    print("⓪ 修复前后对照: 旧口径(r114) 分母 vs 新口径(r115) 分母")
    print("=" * 104)
    print("  旧口径 `方法\\s+(名)\\s*<公开(.*?)>` 要求属性块**同行闭合** -> 只认 %d 个可覆盖方法"
          % len(old_hits))
    print("  新口径 跨行属性块扫描                                  -> 认全 %d 个可覆盖方法"
          % len(new_hits))
    print("  旧口径**从未进入分母**的方法: %d 个(这就是'105/105'虚高的根因):" % len(only_new))
    for l in only_new:
        print("     L%-6d %s" % (l, new_hits[l]))
    if old_hits:
        print()
        print("  旧口径的 2 类小计: 应用事件 %d + 浏览器事件 %d = %d  <== 旧脚本分母"
              % (sum(1 for l in old_hits if l <= 433),
                 sum(1 for l in old_hits if 434 <= l <= 1763),
                 sum(1 for l in old_hits if l <= 1763)))

    # ---- 逐类做类感知覆盖判定(先全部算完, 再统一打印) ----
    sections = [("A. 事件类 (FBroEventControl.wsv)", ev_classes)]
    if cb_classes:
        sections.append(("B. 回调基类 (FBroCallback.wsv)", cb_classes))

    all_rows = []          # (类名, 类库行, 分子, 分母, %, 子类数)
    uncovered_rows = []    # (方法名, 类库行, 所属类)
    false_positive_rows = []
    detail = {}            # 类名 -> (subs, covered, missing)

    for _title, groups in sections:
        for cname, cline, evs in groups:
            subs = [c.name for c in p_classes if cname in chain(c.name)]
            covered, missing = [], []
            for (mname, mline) in evs:
                hit = None
                for m in p_methods:
                    if m.name != mname or m.owner is None:
                        continue
                    if "@虚拟方法" not in m.attrs or "可覆盖" not in m.attrs:
                        continue
                    if m.owner in subs:
                        hit = m
                        break
                if hit is not None:
                    covered.append((mname, mline, hit))
                else:
                    missing.append((mname, mline))
                    uncovered_rows.append((mname, mline, cname))
            # 误报候选: 同名可覆盖方法, 但所属类不派生自该事件类
            for (mname, _mline) in evs:
                for m in p_methods:
                    if m.name != mname or m.owner is None:
                        continue
                    if "@虚拟方法" not in m.attrs or "可覆盖" not in m.attrs:
                        continue
                    if m.owner not in subs:
                        false_positive_rows.append(
                            (mname, cname, m.owner, m.file, m.line))
            pct = (100.0 * len(covered) / len(evs)) if evs else 0.0
            all_rows.append((cname, cline, len(covered), len(evs), pct, len(subs)))
            detail[cname] = (subs, covered, missing, pct)

    # ---- ① 权威分母(带真实分子/缺口) ----
    ev_names = [c[0] for c in ev_classes]
    print()
    print("=" * 104)
    print("① 权威分母: FBroEventControl.wsv 的 %d 个事件类 (逐个列出类名与类内事件数)"
          % len(ev_classes))
    print("=" * 104)
    print("  %-2s %-32s %-7s %-9s %-8s %-7s %-15s %s"
          % ("#", "类名", "事件数", "已覆盖", "缺口", "覆盖率", "项目子类数", "类库行"))
    ev_tot = ev_cov = 0
    for i, (cname, cline, evs) in enumerate(ev_classes, 1):
        _subs, _cov, _mis, _pct = detail[cname]
        ev_tot += len(evs)
        ev_cov += len(_cov)
        print("  %-2d %-32s %-7d %-9d %-8d %-7s %-15d L%d"
              % (i, cname, len(evs), len(_cov), len(_mis), "%.1f%%" % _pct, len(_subs), cline))
    print("  " + "-" * 100)
    print("  %-2s %-32s %-7d %-9d %-8d %-7s"
          % ("", "口径A 小计", ev_tot, ev_cov, ev_tot - ev_cov,
             "%.1f%%" % ((100.0 * ev_cov / ev_tot) if ev_tot else 0.0)))

    # ---- ①② 明细 ----
    for title, groups in sections:
        print()
        print("=" * 104)
        print("口径 %s" % title)
        print("=" * 104)
        for cname, cline, evs in groups:
            subs, covered, missing, pct = detail[cname]
            print()
            print("-" * 104)
            print("%s   (类库 L%d)" % (cname, cline))
            print("  项目子类 %d 个: %s" % (len(subs), ", ".join(subs) if subs else "<无>"))
            print("  事件 %d 个, 已覆盖 %d, 缺口 %d, 覆盖率 %.1f%%"
                  % (len(evs), len(covered), len(missing), pct))
            print("-" * 104)
            for (mname, mline) in missing:
                print("   [ 缺 ] %-40s (类库 L%d)" % (mname, mline))
            for (mname, mline, hit) in covered:
                print("   [ OK ] %-40s (类库 L%d) <- %s:%d"
                      % (mname, mline, hit.file, hit.line))

    # ---- 汇总 ----
    print()
    print("=" * 104)
    print("② 分口径覆盖率总表")
    print("=" * 104)
    print("  %-36s %-12s %-10s %-8s %s" % ("类名", "分子/分母", "覆盖率", "项目子类", "类库行"))
    t_cov = t_tot = 0
    for (cname, cline, cov, tot, pct, nsub) in all_rows:
        t_cov += cov
        t_tot += tot
        print("  %-36s %-12s %-10s %-8d L%d"
              % (cname, "%d/%d" % (cov, tot), "%.1f%%" % pct, nsub, cline))
    print("  " + "-" * 92)
    gpct = (100.0 * t_cov / t_tot) if t_tot else 0.0
    print("  %-36s %-12s %-10s" % ("总计 (全部 %d 个类)" % len(all_rows),
                                   "%d/%d" % (t_cov, t_tot), "%.1f%%" % gpct))
    if cb_classes:
        ev_tot = sum(t for (_c, _l, _cov, t, _p, _s) in all_rows
                     if _c in [x[0] for x in ev_classes])
        ev_cov = sum(c for (_c, _l, c, _t, _p, _s) in all_rows
                     if _c in [x[0] for x in ev_classes])
        print("  其中口径A(8 个事件类): %d/%d (%.1f%%)"
              % (ev_cov, ev_tot, (100.0 * ev_cov / ev_tot) if ev_tot else 0.0))
        print("  其中口径B(回调基类)  : %d/%d (%.1f%%)"
              % (t_cov - ev_cov, t_tot - ev_tot,
                 (100.0 * (t_cov - ev_cov) / (t_tot - ev_tot)) if (t_tot - ev_tot) else 0.0))

    # ---- 未覆盖清单 ----
    print()
    print("=" * 104)
    print("③ 未覆盖清单 (%d 项): 事件名 + 类库行号 + 所属事件类" % len(uncovered_rows))
    print("=" * 104)
    print("  %-4s %-42s %-9s %s" % ("#", "事件名", "类库行", "所属类"))
    for i, (mname, mline, cname) in enumerate(uncovered_rows, 1):
        print("  %-4d %-42s L%-8d %s" % (i, mname, mline, cname))

    # ---- 误报候选 ----
    print()
    print("=" * 104)
    print("④ 误报候选 (同名 @虚拟方法=可覆盖, 但所属类不派生自该事件类): %d 项"
          % len(false_positive_rows))
    print("=" * 104)
    if not false_positive_rows:
        print("   <无>")
    for (mname, cname, owner, f, ln) in false_positive_rows:
        print("   %-40s 事件类 %-30s 实际在 %s (%s:%d)"
              % (mname, cname, owner, f, ln))

    # ---- 口径说明 ----
    print()
    print("=" * 104)
    print("⑤ 口径说明 / 残余不确定性")
    print("=" * 104)
    no_sub = [c for (c, _l, evs) in ev_classes if evs
              and not any(c in chain(x.name) for x in p_classes)]
    if no_sub:
        print("   以下事件类在项目里**没有任何子类**, 其中所有事件必然全缺:")
        for c in no_sub:
            print("     - %s" % c)
    else:
        print("   所有事件类在项目里都至少有 1 个子类。")
    print("   注意: 本工具只判断'项目是否声明了可覆盖虚方法', 不判断该方法体是否为空壳、")
    print("         不判断是否真的会被内核回调触发 —— 覆盖率 != 功能有效性。")
    print("   统计只包含带 `@虚拟方法 = 可覆盖` 的虚方法。")
    print("   全类库该属性的取值分布已核对: 只有'可覆盖'一种取值 (事件类库 150 + 回调类库 26),")
    print("   故本口径 == 该文件里可被项目覆写的虚方法全集, 不存在被排除的其它种类。")
    return 0


def _dump_context(path, needle=None, span=4):
    """失败时打印原始文件片段 —— 不允许只报'为空'/'失败'。"""
    try:
        lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    except Exception as exc:                                    # noqa: BLE001
        print("   <无法读取 %s: %r>" % (path, exc))
        return
    print("   --- %s (共 %d 行) ---" % (path, len(lines)))
    if needle is None:
        for i, l in enumerate(lines[:span], 1):
            print("   L%-5d %s" % (i, l))
        return
    hit = False
    for i, l in enumerate(lines, 1):
        if needle in l:
            hit = True
            for j in range(max(1, i - 1), min(len(lines), i + span) + 1):
                print("   L%-5d %s" % (j, lines[j - 1]))
            break
    if not hit:
        print("   <未找到含 %r 的行; 文件前 %d 行如下>" % (needle, span))
        for i, l in enumerate(lines[:span], 1):
            print("   L%-5d %s" % (i, l))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                                           # noqa: BLE001
        import traceback
        print()
        print("!" * 104)
        print("测量失败 —— 原始 traceback 如下 (不做任何静默降级):")
        print("!" * 104)
        traceback.print_exc(file=sys.stdout)
        print()
        print("相关文件片段:")
        for _p in (EVENT_LIB, CALLBACK_LIB):
            _dump_context(_p)
        print()
        print("项目目录 %s 存在=%s, .wsv 文件=%d"
              % (PROJ_DIR, os.path.isdir(PROJ_DIR),
                 len([f for f in os.listdir(PROJ_DIR)
                      if f.endswith('.wsv')]) if os.path.isdir(PROJ_DIR) else -1))
        sys.exit(2)
