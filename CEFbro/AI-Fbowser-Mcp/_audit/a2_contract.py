# -*- coding: utf-8 -*-
"""A2 — 工具契约检查: schema(广告)  <->  实现(实际读取)  双向交叉
含跨辅助方法的传递闭包解析 (分支->helper 的键读取也计入)。

这是本项目最高产的缺陷类别（前任审计的 1 个 HIGH 族 + 多数 MED 均出自此）。
"""
import sys, re, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

W = []
def w(s=""):
    W.append(s)

SERVER = "MCP_Server.wsv"

# ---- 1. 解析 schema ----
srv_lines, _ = lines_of(SERVER)
schema = {}          # tool -> {param: type}
schema_req = {}      # tool -> [required]
schema_line = {}     # tool -> 行号
schema_desc = {}

def parse_schema_line(line):
    """返回 (params{name:type}, required[], has_schema_bool)"""
    ps = collections.OrderedDict()
    req = []
    if "空Schema文本" in line:
        return ps, req, True
    for m in re.finditer(r'属性项JSON\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"', line):
        ps[m.group(1)] = m.group(2)
    for m in re.finditer(r'单参数Schema文本\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"', line):
        ps[m.group(1)] = m.group(2)
    for m in re.finditer(r'双XY_Schema文本\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"', line):
        ps[m.group(1)] = "integer"; ps[m.group(2)] = "integer"
    # required 列表: 多属性Schema文本 的第2参 -> "\"url\"" 形式
    mm = re.search(r'多属性Schema文本\s*\((.*)$', line)
    if mm:
        tail = mm.group(1)
        rm = re.findall(r'\\"([A-Za-z0-9_]+)\\"', tail)
        # 只取最后一个引号串组（required 参数位于末尾）
        if rm:
            # required 是逗号分隔的最后一段；简单取所有出现且属于参数名的
            req = [x for x in rm if x in ps]
    return ps, req, len(ps) > 0 or "空Schema文本" in line

tool_order = []
for i, ln in enumerate(srv_lines):
    m = re.search(r'添加工具JSON\s*\(\s*"([^"]+)"', ln)
    if not m:
        continue
    name = m.group(1)
    if name in schema:
        continue
    ps, req, ok = parse_schema_line(ln)
    schema[name] = ps
    schema_req[name] = req
    schema_line[name] = i + 1
    dm = re.search(r'添加工具JSON\s*\(\s*"[^"]+"\s*,\s*"([^"]*)"', ln)
    schema_desc[name] = dm.group(1) if dm else ""
    tool_order.append(name)

# 工具名 -> 所在行（用于注册表）
reg = {}
for i, ln in enumerate(srv_lines):
    for m in re.finditer(r'置整数值\s*\(\s*"([^"]+)"\s*,\s*(\d+)', ln):
        reg[m.group(1)] = int(m.group(2))

# ---- 2. 全局横切参数（每个工具都可能合法读取，不计入"未广告"） ----
GLOBAL_KEYS = {
    "max_ms", "async_only", "sync_wait", "browser_id", "_compact", "timeout_ms",
    "confirm", "compact",
}

# ---- 3. 方法索引（跨文件） ----
method_idx = {}   # name -> list of (file, b0, b1)
for f in FILES:
    for (i0, mname, sig, b0, b1) in find_methods(f):
        method_idx.setdefault(mname, []).append((f, b0, b1))

ACCESSOR_RE = re.compile(
    r'yyjson取(文本|整数|小数|长整数|逻辑|逻辑_默认|JSON文本)\s*\(\s*([A-Za-z0-9_\u4e00-\u9fff]+)\s*,\s*"([^"]+)"')
# 对象/数组型访问器 —— 首版遗漏, 导致 browser_retry.args 等被误报为"未读取"
OBJ_ACCESSOR_RE = re.compile(
    r'(?:yyjson)?取(对象成员_安全|对象成员|对象|数组|路径对象)\s*\(\s*([A-Za-z0-9_\u4e00-\u9fff]+)\s*,\s*"([^"]+)"')
CALL_RE = re.compile(r'(?:[A-Za-z0-9_\u4e00-\u9fff]+\.)?([A-Za-z0-9_\u4e00-\u9fff]+)\s*\(')


PARAM_OBJ_HINT = ("参数JSON", "工具参数字典", "参数对象", "直接参数", "参数字典",
                  "命令参数", "参数", "commandParams")

CALL_FULL = re.compile(r'([A-Za-z0-9_\u4e00-\u9fff]+)\s*\(')


def call_args(code, m):
    """从 m.end()-1 处的 '(' 起, 取到配对的 ')'，返回实参文本"""
    i = m.end() - 1
    depth = 0
    j = i
    in_str = False
    while j < len(code):
        c = code[j]
        if in_str:
            if c == "\\":
                j += 2; continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return code[i + 1:j]
        j += 1
    return code[i + 1:]


def collect_keys(file, b0, b1, depth=0, seen=None, expand_all=False):
    """收集 [b0,b1] 行范围内的键读取。
    depth==0: 分支内直接读取, 外加"把参数对象整体交给 helper"的传递展开
    (仅当实参里出现参数对象变量名时才展开, 否则 helper 内部读的是任务对象字段,
     不属于本工具的参数 —— 这是上一版产生 8411 条噪声的原因)。
    """
    if seen is None:
        seen = set()
    ls, _ = lines_of(file)
    out = collections.defaultdict(set)
    if depth > 3:
        return out
    for k in range(b0, b1 + 1):
        if k >= len(ls):
            break
        line = ls[k]
        if classify(line) == "EMBED":
            continue
        code = re.sub(r"//.*$", "", line)      # 只剥行注释, 保留字符串
        for m in ACCESSOR_RE.finditer(code):
            acc, obj, key = m.group(1), m.group(2), m.group(3)
            out[key].add(acc)
        for m in OBJ_ACCESSOR_RE.finditer(code):
            acc, obj, key = "对象成员", m.group(2), m.group(3)
            out[key].add(acc)
        if depth >= 1 and not expand_all:
            continue
        for m in CALL_FULL.finditer(code):
            fn = m.group(1)
            if fn.startswith("yyjson取"):
                continue
            args = call_args(code, m)
            if depth == 0:
                # 仅当实参里出现"参数对象"才视为参数转发
                if not any(h in args for h in PARAM_OBJ_HINT):
                    continue
            for (ff, fb0, fb1) in method_idx.get(fn, []):
                tag = (ff, fb0)
                if tag in seen:
                    continue
                seen.add(tag)
                sub = collect_keys(ff, fb0, fb1, depth + 1, seen, expand_all)
                for kk, vv in sub.items():
                    out[kk] |= vv
    return out


# ---- 4. 解析各分派器的工具分支 ----
BRANCH_RE = re.compile(r'(?:如果|否则)\s*\(\s*(?:方法名|工具名)\s*==\s*"(browser_[a-z0-9_]+)"')
branches = {}   # tool -> [(file, b0, b1)]
for f in sorted(DISPATCHERS):
    ls, _, da = brace_map(f)
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        # 用原始行匹配(字符串内容必须保留)
        m = BRANCH_RE.search(re.sub(r"//.*$", "", ln))
        if not m:
            continue
        # 分支体: 从该行之后第一个 '{' 开始（可能是下一行）
        j = i
        while j < len(ls) and "{" not in strip_strings_and_comment(ls[j])[0]:
            j += 1
        if j >= len(ls):
            continue
        b0, b1, _ = extract_block(f, j)
        branches.setdefault(m.group(1), []).append((f, b0, b1, i + 1))

# ---- 5. 交叉 ----
TYPE_OF = {"文本": "string", "整数": "integer", "长整数": "long", "小数": "number",
           "逻辑": "boolean", "逻辑_默认": "boolean", "JSON文本": "json",
           "对象成员": "object"}

HARD_MISMATCH = {
    # (声明类型, 读取器类型) -> 判定
    ("boolean", "string"): "HIGH: 布尔节点被 取文本 读取 -> 恒得空串, 非默认值全部被静默忽略",
    ("string", "number"): "HIGH: 字符串型输入被 取小数 读取 -> 恒得 0",
    ("string", "integer"): "HIGH: 字符串型输入被 取整数 读取 -> 恒得 0",
    ("string", "long"): "HIGH: 字符串型输入被 取长整数 读取 -> 恒得 0",
}
SOFT_MISMATCH = {
    ("integer", "string"): "INFO: 数值型参数用 取文本 读取 (可能是有意的双表示兼容, 需人工确认)",
    ("number", "string"): "INFO: 数值型参数用 取文本 读取 (需人工确认)",
    ("boolean", "boolean"): None,
}

w("=" * 100)
w("A2 工具契约检查: schema(广告) <-> 实现(实际读取)  双向交叉 + 类型一致性")
w("方法: 解析 265 条 添加工具JSON 的 schema 声明；对 7 个分派器的工具分支做")
w("      花括号精确分块；键读取含跨辅助方法的传递闭包(深度<=4)。")
w("=" * 100)
w()
w("schema 解析结果: %d 个工具" % len(schema))
no_schema = [t for t in tool_order if not schema[t]]
w("  其中无参数 schema (空Schema文本 或无第3参): %d 个" % len(no_schema))
w()

hard, soft, unadvertised, unread = [], [], [], []

for tool in tool_order:
    bl = branches.get(tool)
    if not bl:
        continue
    keys_direct = collections.defaultdict(set)   # 仅分支内直接读取 (用于"未广告")
    keys_full = collections.defaultdict(set)     # 含参数对象转发展开 (用于"类型不匹配", 求最大召回)
    for (f, b0, b1, bline) in bl:
        for k, v in collect_keys(f, b0, b1, 0, set(), False).items():
            keys_direct[k] |= v
            keys_full[k] |= v
        for k, v in collect_keys(f, b0, b1, 0, set(), True).items():
            keys_full[k] |= v
    adv = schema[tool]
    # 5a 实现读但未广告 (直接读取, 精确)
    for k in sorted(keys_direct):
        if k in adv or k in GLOBAL_KEYS:
            continue
        unadvertised.append((tool, k, keys_direct[k], bl[0]))
    # 5b 广告但整个项目未读 (用最大召回判"确实没读")
    for k in sorted(adv):
        if k in GLOBAL_KEYS:
            continue
        if k not in keys_full:
            unread.append((tool, k, adv[k], schema_line[tool]))
    # 5c 类型一致性 (用最大召回)
    for k, accs in keys_full.items():
        if k not in adv:
            continue
        dt = adv[k]
        for a in accs:
            at = TYPE_OF.get(a)
            key = (dt, at)
            if key in HARD_MISMATCH:
                hard.append((tool, k, dt, a, bl[0], schema_line[tool]))
            elif key in SOFT_MISMATCH and SOFT_MISMATCH[key]:
                soft.append((tool, k, dt, a, bl[0], schema_line[tool]))

# 去重
def dedup(rows):
    seen, out = set(), []
    for r in rows:
        s = tuple(str(x) for x in r)
        if s in seen:
            continue
        seen.add(s); out.append(r)
    return out

hard = dedup(hard); soft = dedup(soft)
unadvertised = dedup(unadvertised); unread = dedup(unread)

w("#" * 100)
w("# [HIGH 候选] schema 声明类型 与 实现读取器 不兼容  —— 共 %d 处" % len(hard))
w("#" * 100)
for (tool, k, dt, a, bl, sl) in hard:
    w("  %-42s 参数 %-18s schema声明=%-8s 实现=yyjson取%s" % (tool, k, dt, a))
    w("      分支 %s:%d   schema 声明 %s:%d" % (bl[0], bl[1], SERVER, sl))
    w("      -> %s" % HARD_MISMATCH[(dt, TYPE_OF[a])])
w()

w("#" * 100)
w("# [INFO] 需人工确认的软性不匹配 —— 共 %d 处" % len(soft))
w("#" * 100)
for (tool, k, dt, a, bl, sl) in soft:
    w("  %-42s 参数 %-18s schema=%-8s 实现=yyjson取%s   (分支 %s:%d)" % (tool, k, dt, a, bl[0], bl[1]))
w()

w("#" * 100)
w("# [MED 候选] 实现读取了 schema 未广告的参数 —— 共 %d 处" % len(unadvertised))
w("#" * 100)
for (tool, k, accs, bl) in unadvertised:
    w("  %-42s 读取 %-20s 方式=%s" % (tool, k, ",".join(sorted(accs))))
    w("      分支 %s:%d   schema 声明 %s:%d" % (bl[0], bl[1], SERVER, schema_line.get(tool, 0)))
w()

w("#" * 100)
w("# [MED 候选] schema 广告了但整个项目从未读取 —— 共 %d 处" % len(unread))
w("#" * 100)
for (tool, k, dt, sl) in unread:
    w("  %-42s 参数 %-20s 声明=%-8s (schema %s:%d)" % (tool, k, dt, SERVER, sl))
w()

w("=" * 100)
w("汇总: 硬性类型不匹配 %d | 软性不匹配 %d | 未广告参数 %d | 广告未读 %d" %
  (len(hard), len(soft), len(unadvertised), len(unread)))
w("注: 未广告/未读列表含跨分裂分支的噪声(同一工具在多个分派器有分支)，需人工复核。")
w("=" * 100)

p = out_report("report_A2.txt", "\n".join(W))
print("written", p, "| hard=%d soft=%d unadv=%d unread=%d" % (len(hard), len(soft), len(unadvertised), len(unread)))
