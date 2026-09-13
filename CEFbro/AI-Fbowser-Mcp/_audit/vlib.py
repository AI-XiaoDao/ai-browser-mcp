# -*- coding: utf-8 -*-
r"""火山 .wsv 静态分析基础库 — 供本次全面审计的各检查器共用。

关键建模（依据技能书 参考/wsv文件格式.md + 参考/语法速查.md）：
  * `@` 引导行 = 嵌入 C++/嵌入语句行 -> 对火山解析器不透明，花括号/引号不参与配对
  * `#` 引导行 = 文档级/类级注释或嵌入行 -> 同样不透明
  * 方法体内注释为 `//`；字符串用双引号，转义 \\ \" \' \r \n \t \uXXXX \xXX
  * 因此花括号配对必须"字符串感知 + 注释感知 + 跳过 @/# 行"
"""
import os
import re
import io

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

FILES = [
    "main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
    "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
    "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
    "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
    "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv",
]

# 分派器文件（含 分类分派_* 大分支链）
DISPATCHERS = {
    "MCP_Server_Core.wsv", "MCP_Server_VIP.wsv", "MCP_Server_Form.wsv",
    "MCP_Server_System.wsv", "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv",
    "MCP_Kernel.wsv",
}


def read_wsv(name):
    """按字节读，自动识别 UTF-8 / UTF-16LE，返回 (文本, 编码, 行尾, 是否有BOM)。"""
    p = os.path.join(SRC, name)
    raw = open(p, "rb").read()
    bom = ""
    if raw[:2] == b"\xff\xfe":
        text = raw.decode("utf-16-le"); enc = "utf-16le"; bom = "FFFE"
    elif raw[:3] == b"\xef\xbb\xbf":
        text = raw[3:].decode("utf-8"); enc = "utf-8"; bom = "EFBBBF"
    else:
        text = raw.decode("utf-8"); enc = "utf-8"; bom = ""
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n")
    eol = "CRLF" if (lf and crlf == lf) else ("LF" if crlf == 0 else "MIXED")
    return text, enc, eol, bom, raw


def lines_of(name):
    text, enc, eol, bom, raw = read_wsv(name)
    return text.split("\n"), (enc, eol, bom, raw)


def classify(line):
    """返回 'EMBED' / 'HASH' / 'CODE' / 'BLANK'"""
    s = line.strip()
    if s == "":
        return "BLANK"
    if s[0] == "@":
        return "EMBED"
    if s[0] == "#":
        return "HASH"
    return "CODE"


def strip_strings_and_comment(code):
    """把 CODE 行中的字符串字面量与 // 注释替换为占位，便于括号/逗号计数。
    返回 (净化文本, 是否处于未闭合字符串)。"""
    out = []
    i, n = 0, len(code)
    in_str = False
    while i < n:
        c = code[i]
        if in_str:
            if c == "\\":
                out.append("  "); i += 2; continue
            if c == '"':
                in_str = False; out.append('"'); i += 1; continue
            out.append(" "); i += 1; continue
        if c == '"':
            in_str = True; out.append('"'); i += 1; continue
        if c == "/" and i + 1 < n and code[i + 1] == "/":
            break  # 行注释，其余忽略
        out.append(c); i += 1
    return "".join(out), in_str


def brace_map(name):
    """返回 depth_before[i] / depth_after[i]（仅对 CODE 行计数）。
    depth 从 0 开始。"""
    ls, _ = lines_of(name)
    db, da = [], []
    d = 0
    for ln in ls:
        db.append(d)
        k = classify(ln)
        if k == "CODE":
            clean, _ = strip_strings_and_comment(ln)
            d += clean.count("{") - clean.count("}")
        da.append(d)
    return ls, db, da


def extract_block(name, start_idx):
    """给定包含 '{' 的起始行索引，返回 (body_start, body_end, block_end_line)；
    找不到闭合返回 (start+1, len-1, len-1)。1-based 行号输出由调用方处理。"""
    ls, db, da = brace_map(name)
    base = db[start_idx]
    for j in range(start_idx, len(ls)):
        if da[j] <= base and j > start_idx:
            return start_idx + 1, j - 1, j
    return start_idx + 1, len(ls) - 1, len(ls) - 1


def find_methods(name):
    """返回 [(起始行idx, 方法名, 签名行, 方法体起, 方法体止)]（1-based 号由调用方 +1）。"""
    ls, _ = lines_of(name)
    res = []
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        m = re.match(r"\s*方法\s+(\S+)", ln)
        if not m:
            continue
        # 找到方法体的 '{'
        j = i
        while j < len(ls) and "{" not in strip_strings_and_comment(ls[j])[0]:
            j += 1
        if j >= len(ls):
            continue
        b0, b1, _ = extract_block(name, j)
        res.append((i, m.group(1), ln.strip(), b0, b1))
    return res


def find_classes(name):
    ls, _ = lines_of(name)
    res = []
    for i, ln in enumerate(ls):
        if classify(ln) != "CODE":
            continue
        m = re.match(r"\s*类\s+(\S+)", ln)
        if m:
            res.append((i, m.group(1), ln.strip()))
    return res


IDENT = r"[A-Za-z0-9_\u4e00-\u9fff]+"


def is_doc_header(line):
    return line.strip().startswith("<火山程序")


def method_body_set(name):
    """返回所有方法体内部行的索引集合（用于判定 '#' / '//' 的合法位置）。"""
    s = set()
    for (i0, mname, sig, b0, b1) in find_methods(name):
        for k in range(b0, b1 + 1):
            s.add(k)
    return s


def member_lines(name):
    """顶层/类级成员行（排除文档头、方法体内部行）。"""
    ls, _ = lines_of(name)
    body = method_body_set(name)
    return [(i, l) for i, l in enumerate(ls)
            if classify(l) == "CODE" and i not in body and not is_doc_header(l)]


def out_report(fname, text):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
    with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


def all_files_text():
    return {f: lines_of(f)[0] for f in FILES}


def line_of(name, idx0):
    return idx0 + 1
