# -*- coding: utf-8 -*-
"""
g1_ghost_triage.py — 只读静态审计: 注册表 vs 分派链 交叉核对 (幽灵注册检测)
只读 src/*.wsv, 绝不写入任何 .wsv。输出 JSON + 文本分诊证据到 _audit/。
"""
import json
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

ROOT = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "_audit")

ACTIVE = [
    "main.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv", "MCP_Constants.wsv",
    "MCP_Kernel.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv",
    "MCP_Server_Form.wsv", "MCP_Server_HTTP.wsv", "MCP_Server_Reverse.wsv",
    "MCP_Server_System.wsv", "MCP_Server_Utils.wsv", "MCP_Server_VIP.wsv",
    "MCP_Server_Workflow.wsv", "MCP_Stdio.wsv",
]

# 注册调用名 (MCP tools/list 的唯一来源)
REG_CALL = "添加工具JSON"

# 分派方法全集 (执行浏览器命令 直投 + 回退链 中出现的 7 个分派器)
DISPATCHERS = [
    ("分类分派_核心操作", "MCP_Server_Core.wsv"),
    ("分类分派_填表操作", "MCP_Server_Form.wsv"),
    ("分类分派_VIP操作", "MCP_Server_VIP.wsv"),
    ("分类分派_系统操作", "MCP_Server_System.wsv"),
    ("分类分派_编排操作", "MCP_Server_Workflow.wsv"),
    ("分类分派_逆向操作", "MCP_Server_Reverse.wsv"),
    ("分类分派_内核操作", "MCP_Kernel.wsv"),
]

CANDIDATES = [
    "browser_aliases", "browser_batch", "browser_create_tab", "browser_debugger_pause",
    "browser_fingerprint_languages", "browser_fingerprint_webgl_vendor", "browser_font_randomize",
    "browser_reverse_cookie_cdp", "browser_reverse_css_coverage", "browser_reverse_detect_traps",
    "browser_reverse_emulate_focus", "browser_reverse_input_cdp", "browser_reverse_layer_tree",
    "browser_reverse_network_conditions", "browser_reverse_trace", "browser_task_runner_post",
]


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def in_line_comment(text, pos):
    """该位置是否落在行注释 // 之后 (按行首到 pos 之间是否出现 //)。"""
    ls = text.rfind("\n", 0, pos) + 1
    seg = text[ls:pos]
    return "//" in seg


def parse_string_literal(text, i):
    """text[i] 必须是 '"'。返回 (值, 结束位置/或 None)。"""
    assert text[i] == '"'
    j = i + 1
    buf = []
    while j < len(text):
        c = text[j]
        if c == "\\":
            if j + 1 < len(text):
                buf.append(text[j:j + 2])
                j += 2
                continue
            return None, None
        if c == '"':
            return "".join(buf), j
        if c == "\n":
            return None, None
        buf.append(c)
        j += 1
    return None, None


def unescape(s):
    return s.replace('\\"', '"').replace("\\\\", "\\")


def build_method_index(text):
    """返回按出现顺序的 (行号, 名称, 类型[类|方法]) 列表。"""
    out = []
    for m in re.finditer(r"(?m)^[ \t]*(类|方法)[ \t]+([^\s<>]+)", text):
        out.append((line_of(text, m.start()), m.group(1), m.group(2)))
    return out


def owner_of(methods, line):
    cur = None
    for ln, kind, name in methods:
        if ln <= line:
            cur = (kind, name, ln)
        else:
            break
    return cur


def extract_registrations(text):
    """提取全部 添加工具JSON 调用的第一个字符串字面量参数。"""
    regs = []
    for m in re.finditer(re.escape(REG_CALL), text):
        pos = m.start()
        # 跳过 "方法 添加工具JSON" 定义行 与 注释中的提及
        if in_line_comment(text, pos):
            regs.append({"name": None, "line": line_of(text, pos),
                         "note": "COMMENTED_MENTION",
                         "snippet": text[pos:pos + 60].split("\n")[0]})
            continue
        i = m.end()
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != "(":
            regs.append({"name": None, "line": line_of(text, pos),
                         "note": "NO_PAREN(疑似定义行或注释)",
                         "snippet": text[pos:pos + 60].split("\n")[0]})
            continue
        i += 1
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != '"':
            regs.append({"name": None, "line": line_of(text, pos),
                         "note": "FIRST_ARG_NOT_LITERAL",
                         "snippet": text[pos:pos + 60].split("\n")[0]})
            continue
        val, end = parse_string_literal(text, i)
        if val is None:
            regs.append({"name": None, "line": line_of(text, pos),
                         "note": "UNPARSED_LITERAL",
                         "snippet": text[pos:pos + 60].split("\n")[0]})
            continue
        regs.append({"name": unescape(val), "line": line_of(text, pos),
                     "note": "OK",
                     "raw": text[m.start():end + 1].replace("\n", " ")})
    return regs


BRANCH_PATTERNS = [
    # 方法名 == "xxx"    (含 || 串联)
    (re.compile(r'方法名\s*==\s*"((?:[^"\\]|\\.)*)"'), "EQ"),
    (re.compile(r'"((?:[^"\\]|\\.)*)"\s*==\s*方法名'), "EQ_REV"),
    (re.compile(r'是否以\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "STARTSWITH"),
    (re.compile(r'包含\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "CONTAINS"),
    (re.compile(r'寻找文本\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "FINDTEXT"),
    (re.compile(r'子文本替换\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "NORMALIZE"),
    # 其他可能的别名变量比较 (如 短名 == "xxx")
    (re.compile(r'短名\s*==\s*"((?:[^"\\]|\\.)*)"'), "SHORT_EQ"),
    (re.compile(r'规范化\w*\s*==\s*"((?:[^"\\]|\\.)*)"'), "NORM_EQ"),
]


def extract_branches(text, start_line, end_line, all_lines):
    res = []
    for ln in range(start_line, min(end_line, len(all_lines)) + 1):
        raw = all_lines[ln - 1]
        stripped = raw.strip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        code = raw.split("//")[0]
        for rx, kind in BRANCH_PATTERNS:
            for m in rx.finditer(code):
                res.append({"line": ln, "kind": kind, "value": unescape(m.group(1)),
                            "code": code.strip()[:200]})
    return res


def main():
    files = {}
    for fn in ACTIVE:
        p = os.path.join(SRC, fn)
        if os.path.exists(p):
            files[fn] = read(p)

    report = {"files": {}, "registry": [], "registry_names": [], "dispatchers": {}}

    # 1) 注册表全集
    regs_all = []
    for fn, text in files.items():
        methods = build_method_index(text)
        for r in extract_registrations(text):
            r["file"] = fn
            if r.get("name"):
                ow = owner_of(methods, r["line"])
                r["owner"] = (ow[1] if ow else None)
            regs_all.append(r)
    report["registry"] = regs_all

    names = {}
    for r in regs_all:
        if r.get("note") == "OK":
            names.setdefault(r["name"], []).append({"file": r["file"], "line": r["line"],
                                                    "owner": r.get("owner"), "raw": r.get("raw")})
    report["registry_names"] = sorted(names.keys())
    report["registry_index"] = names

    # 2) 命令注册表 (字典) 全集 — 构建命令注册表 + 注册命令双变体
    dict_regs = {}
    for fn, text in files.items():
        lines = text.split("\n")
        methods = build_method_index(text)
        for ln, raw in enumerate(lines, 1):
            code = raw.split("//")[0]
            m = re.search(r'命令注册表\.置整数值\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)', code)
            if m:
                dict_regs.setdefault(unescape(m.group(1)), []).append(
                    {"file": fn, "line": ln, "id": int(m.group(2)), "kind": "EXPLICIT"})
            m2 = re.search(r'注册命令双变体\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)\s*(?:,\s*(真|假))?', code)
            if m2:
                base = unescape(m2.group(1))
                cid = int(m2.group(2))
                short = (m2.group(3) != "假")
                variants = ["browser." + base, "browser_" + base]
                if short:
                    variants.append(base)
                for v in variants:
                    dict_regs.setdefault(v, []).append(
                        {"file": fn, "line": ln, "id": cid,
                         "kind": "DUALVARIANT" + ("" if short else "/no-short")})
    report["dict_registry_index"] = dict_regs
    report["dict_registry_names"] = sorted(dict_regs.keys())

    # 3) 分派器分支
    for dname, dfn in DISPATCHERS:
        text = files.get(dfn, "")
        if not text:
            report["dispatchers"][dname] = {"file": dfn, "missing": True}
            continue
        lines = text.split("\n")
        methods = build_method_index(text)
        mdef = None
        for ln, kind, name in methods:
            if name == dname:
                mdef = ln
                break
        if mdef is None:
            report["dispatchers"][dname] = {"file": dfn, "missing": True}
            continue
        end = len(lines)
        for ln, kind, name in methods:
            if ln > mdef:
                end = ln - 1
                break
        br = extract_branches(text, mdef, end, lines)
        # 兜底检测: 该分派器方法体内是否存在 否则 { 且其后没有 方法名 == 比较 (粗略: 统计 否则 出现)
        has_else_default = False
        for ln in range(mdef, end + 1):
            s = lines[ln - 1].strip()
            if s.startswith("否则") and "(" not in s:
                has_else_default = True
        report["dispatchers"][dname] = {
            "file": dfn, "def_line": mdef, "end_line": end,
            "branch_count": len(br), "branches": br,
            "has_bare_else": has_else_default,
        }

    with open(os.path.join(OUT, "g1_registry.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    # 4) 交叉核对 16 个候选
    print("=" * 100)
    print("注册表(添加工具JSON)条目数 =", len([r for r in regs_all if r.get("note") == "OK"]))
    print("去重后工具名数 =", len(names))
    print("命令注册表(字典)条目数 =", len(dict_regs))
    print("=" * 100)
    for c in CANDIDATES:
        in_tools = names.get(c, [])
        in_dict = dict_regs.get(c, [])
        hits = []
        for dname, _ in DISPATCHERS:
            d = report["dispatchers"].get(dname, {})
            for b in d.get("branches", []):
                if b["value"] == c or (b["kind"] in ("STARTSWITH", "CONTAINS", "FINDTEXT")
                                       and b["value"] and c.startswith(b["value"])):
                    hits.append((dname, b))
        print("-" * 100)
        print("工具名:", c)
        print("  添加工具JSON:", ("是 @" + "; ".join("%s:%d(%s)" % (x["file"], x["line"], x["owner"]) for x in in_tools)) if in_tools else "否")
        print("  命令注册表   :", ("是 @" + "; ".join("%s:%d id=%d %s" % (x["file"], x["line"], x["id"], x["kind"]) for x in in_dict)) if in_dict else "否")
        if hits:
            for dn, b in hits:
                print("  分派命中     : %s L%d [%s] %s -> %s" % (dn, b["line"], b["kind"], b["value"], b["code"][:110]))
        else:
            print("  分派命中     : 全部分派方法均无")
    print("=" * 100)


if __name__ == "__main__":
    main()
