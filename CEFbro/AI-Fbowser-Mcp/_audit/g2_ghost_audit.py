# -*- coding: utf-8 -*-
"""
g2_ghost_audit.py — 幽灵注册分诊 (只读, 基于 _audit/_ghost_snapshot 冻结快照)

判定模型 (来自 MCP_Server.wsv 执行浏览器命令 的实际代码):
  A. MCP tools/list 注册面 = 添加工具JSON(名称, ...) 的唯一来源 = 方法 填充工具列表
  B. 命令注册表(字典) 注册面 = 构建命令注册表 / 注册命令双变体
  C. 分派链 = 前缀直投(7个分派器) + result==""回退链(核心→填表→VIP→系统→编排→内核)
     每个分派器内部用 `方法名 == "xxx"` / `否则 (方法名 == ...)` 分支; 命中则返回非空文本。
     分派器末尾 `返回 ("")` 表示未命中, 交给下一个。
"""
import json
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

ROOT = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
SNAP = os.path.join(ROOT, "_audit", "_ghost_snapshot")
OUT = os.path.join(ROOT, "_audit")

FILES = ["main.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv", "MCP_Constants.wsv",
         "MCP_Kernel.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv",
         "MCP_Server_Form.wsv", "MCP_Server_HTTP.wsv", "MCP_Server_Reverse.wsv",
         "MCP_Server_System.wsv", "MCP_Server_Utils.wsv", "MCP_Server_VIP.wsv",
         "MCP_Server_Workflow.wsv", "MCP_Stdio.wsv"]

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

REG_CALL = "添加工具JSON"


def read(fn):
    return open(os.path.join(SNAP, fn + ".snapshot.txt"), "r", encoding="utf-8", errors="replace").read()


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def line_comment_pos(text, pos):
    ls = text.rfind("\n", 0, pos) + 1
    seg = text[ls:pos]
    return seg.find("//")


def parse_str(text, i):
    if text[i] != '"':
        return None, None
    j, buf = i + 1, []
    while j < len(text):
        c = text[j]
        if c == "\\" and j + 1 < len(text):
            buf.append(text[j:j + 2]); j += 2; continue
        if c == '"':
            return "".join(buf), j
        if c == "\n":
            return None, None
        buf.append(c); j += 1
    return None, None


def unesc(s):
    return s.replace('\\"', '"').replace("\\\\", "\\")


def method_index(text):
    out = []
    for m in re.finditer(r"(?m)^[ \t]*(类|方法)[ \t]+([^\s<>]+)", text):
        out.append((line_of(text, m.start()), m.group(1), m.group(2)))
    return out


def owner(methods, line):
    cur = None
    for ln, kind, name in methods:
        if ln <= line:
            cur = (kind, name, ln)
        else:
            break
    return cur


def registrations(text):
    out = []
    for m in re.finditer(re.escape(REG_CALL), text):
        pos = m.start()
        ln = line_of(text, pos)
        cp = line_comment_pos(text, pos)
        if cp != -1:
            out.append({"name": None, "line": ln, "note": "IN_COMMENT",
                        "snippet": text[pos:pos + 70].split("\n")[0]})
            continue
        i = m.end()
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != "(":
            out.append({"name": None, "line": ln, "note": "NOT_A_CALL(可能是方法定义)",
                        "snippet": text[pos:pos + 70].split("\n")[0]})
            continue
        i += 1
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        v, e = parse_str(text, i)
        if v is None:
            out.append({"name": None, "line": ln, "note": "UNPARSED",
                        "snippet": text[pos:pos + 70].split("\n")[0]})
            continue
        raw = text[m.start():e + 1]
        out.append({"name": unesc(v), "line": ln, "note": "OK",
                    "raw": re.sub(r"\s+", " ", raw)})
    return out


def build_registry():
    tool_names, dict_names = {}, {}
    for fn in FILES:
        text = read(fn)
        methods = method_index(text)
        for r in registrations(text):
            r["file"] = fn
            if r["note"] == "OK":
                ow = owner(methods, r["line"])
                r["owner"] = ow[1] if ow else None
                tool_names.setdefault(r["name"], []).append(r)
        lines = text.split("\n")
        for ln, raw in enumerate(lines, 1):
            code = raw.split("//")[0]
            for m in re.finditer(r'命令注册表\.置整数值\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)', code):
                dict_names.setdefault(unesc(m.group(1)), []).append(
                    {"file": fn, "line": ln, "id": int(m.group(2)), "how": "置整数值",
                     "raw": code.strip()[:160]})
            for m in re.finditer(r'注册命令双变体\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)\s*(?:,\s*(真|假))?', code):
                base, cid, short = unesc(m.group(1)), int(m.group(2)), (m.group(3) != "假")
                for v in (["browser." + base, "browser_" + base] + ([base] if short else [])):
                    dict_names.setdefault(v, []).append(
                        {"file": fn, "line": ln, "id": cid,
                         "how": "注册命令双变体(" + base + ")" + ("" if short else " 不带短名"),
                         "raw": code.strip()[:160]})
    return tool_names, dict_names


def dispatcher_bodies():
    res = {}
    for dname, dfn in DISPATCHERS:
        text = read(dfn)
        lines = text.split("\n")
        methods = method_index(text)
        d = None
        for ln, kind, name in methods:
            if name == dname:
                d = ln; break
        if d is None:
            res[dname] = None; continue
        end = len(lines)
        for ln, kind, name in methods:
            if ln > d:
                end = ln - 1; break
        res[dname] = (dfn, d, end, lines, text)
    return res


def branches_of(text, d, end, lines):
    """返回 [(行号, 种类, 值, 代码片段)]"""
    pats = [
        (re.compile(r'方法名\s*==\s*"((?:[^"\\]|\\.)*)"'), "方法名==字面量"),
        (re.compile(r'"((?:[^"\\]|\\.)*)"\s*==\s*方法名'), "字面量==方法名"),
        (re.compile(r'是否以\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "前缀(是否以)"),
        (re.compile(r'包含\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "包含"),
        (re.compile(r'寻找文本\s*\(\s*方法名\s*,\s*"((?:[^"\\]|\\.)*)"'), "寻找文本"),
        (re.compile(r'==\s*"((?:[^"\\]|\\.)*)"'), "其它变量==字面量"),
    ]
    out = []
    for ln in range(d, min(end, len(lines)) + 1):
        raw = lines[ln - 1]
        s = raw.strip()
        if s.startswith("//") or s.startswith("#"):
            continue
        code = raw.split("//")[0]
        for rx, kind in pats:
            if kind == "其它变量==字面量" and "方法名" in code:
                continue
            for m in rx.finditer(code):
                out.append((ln, kind, unesc(m.group(1)), re.sub(r"\s+", " ", code.strip())[:200]))
    return out


def main():
    tool_names, dict_names = build_registry()
    disp = dispatcher_bodies()
    all_branches = {}
    for dname, info in disp.items():
        if info is None:
            all_branches[dname] = []
            continue
        dfn, d, end, lines, text = info
        all_branches[dname] = branches_of(text, d, end, lines)
        # catch-all 检测
        bare_else = [(ln, lines[ln - 1].strip()) for ln in range(d, end + 1)
                     if lines[ln - 1].strip() == "否则" or lines[ln - 1].strip().startswith("否则")
                     and "(" not in lines[ln - 1]]
        info_extra = bare_else
        disp[dname] = (dfn, d, end, lines, text, info_extra)

    result = {"snapshot": SNAP, "tool_list_count": len(tool_names), "dict_count": len(dict_names),
              "dispatcher_info": {}, "rows": []}
    for dname, info in disp.items():
        if info is None:
            continue
        dfn, d, end, lines, text, bare = info
        result["dispatcher_info"][dname] = {"file": dfn, "def_line": d, "end_line": end,
                                            "branch_literals": len(all_branches[dname]),
                                            "bare_else_lines": [b[0] for b in bare]}
        # 末尾返回
        tail = [l for l in lines[max(d, end - 4):end] if "返回" in l]
        result["dispatcher_info"][dname]["tail"] = [t.strip() for t in tail]

    for c in CANDIDATES:
        row = {"tool": c}
        # A. tools/list
        if c in tool_names:
            row["tools_list"] = [{"file": r["file"], "line": r["line"], "owner": r.get("owner"),
                                  "raw": r["raw"][:150]} for r in tool_names[c]]
        else:
            row["tools_list"] = None
        # B. dict registry
        if c in dict_names:
            row["dict_registry"] = dict_names[c]
        else:
            row["dict_registry"] = None
        # C. dispatch
        base = c[len("browser_"):] if c.startswith("browser_") else c
        hits = []
        for dname, brs in all_branches.items():
            for (ln, kind, val, code) in brs:
                if val == c or val == base:
                    hits.append({"dispatcher": dname, "line": ln, "kind": kind, "value": val, "code": code})
                elif kind == "前缀(是否以)" and val and c.startswith(val):
                    hits.append({"dispatcher": dname, "line": ln, "kind": "前缀匹配" + val, "value": val, "code": code})
        row["dispatch_hits"] = hits
        result["rows"].append(row)

    with open(os.path.join(OUT, "g2_ghost_findings.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    # 文本证据
    L = []
    L.append("快照: %s" % SNAP)
    L.append("tools/list(添加工具JSON) 去重工具名数 = %d" % len(tool_names))
    L.append("命令注册表(字典) 去重条目数 = %d" % len(dict_names))
    L.append("")
    L.append("== 7 个分派器结构 ==")
    for k, v in result["dispatcher_info"].items():
        L.append("  %-18s %-24s L%d..L%d 条件字面量=%d 裸否则行=%s 末尾=%s"
                 % (k, v["file"], v["def_line"], v["end_line"], v["branch_literals"],
                    v["bare_else_lines"], v["tail"]))
    L.append("")
    L.append("== 16 个候选逐项 ==")
    for row in result["rows"]:
        L.append("-" * 90)
        L.append("工具名: %s" % row["tool"])
        if row["tools_list"]:
            for x in row["tools_list"]:
                L.append("  [A] tools/list 已注册: %s:%d 方法=%s" % (x["file"], x["line"], x["owner"]))
                L.append("      原文: %s" % x["raw"])
        else:
            L.append("  [A] tools/list: 未注册 (301 项中无此名)")
        if row["dict_registry"]:
            for x in row["dict_registry"]:
                L.append("  [B] 命令注册表: %s:%d id=%d 方式=%s" % (x["file"], x["line"], x["id"], x["how"]))
                L.append("      原文: %s" % x["raw"])
        else:
            L.append("  [B] 命令注册表: 未注册")
        if row["dispatch_hits"]:
            for h in row["dispatch_hits"]:
                L.append("  [C] 分派命中: %s L%d [%s] %s" % (h["dispatcher"], h["line"], h["kind"], h["value"]))
                L.append("      原文: %s" % h["code"])
        else:
            L.append("  [C] 分派命中: 全部分派方法均无 (7/7 均无 方法名== 该名或基名的分支)")
    with open(os.path.join(OUT, "g2_ghost_evidence.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("OK -> _audit/g2_ghost_findings.json , _audit/g2_ghost_evidence.txt")
    print("tools/list names =", len(tool_names), " dict names =", len(dict_names))


if __name__ == "__main__":
    main()
