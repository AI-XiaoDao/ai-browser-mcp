# -*- coding: utf-8 -*-
"""补强 4 处守卫: 缺元素时 CDP 返回的<b>不是</b>字符串 "null", 而是
   {"type":"object","subtype":"null","value":null}
   导致守卫漏过, 最终把这段 CDP 对象描述当成"答案"返回给 AI —— 仍是"静默错误答案"。

修法(不依赖脆弱的转义匹配): 让 JS 在元素不存在时返回**哨兵串**, 再据此给可行动报错。
   原: return e?e.textContent:null      (CDP 会把 null 序列化成对象描述)
   新: return e?e.textContent:'__MCP_NO_ELEM__'
"""
import io
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

TARGETS = [
    (r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv",
     "js取文值", "js取文码"),
    (r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv",
     "js查询值", "js查询码"),
    (r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv",
     "js内码值", "js内码"),
    (r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Form.wsv",
     "js属性值", "js属性码"),
]

by_file = {}
for p, val_var, code_var in TARGETS:
    by_file.setdefault(p, []).append((val_var, code_var))

for p, items in by_file.items():
    raw = io.open(p, "rb").read()
    crlf = raw.count(b"\r\n") > 0
    t = raw.decode("utf-8").replace("\r\n", "\n")

    for val_var, code_var in items:
        # 1) JS 表达式尾部 :null})()  改  :'__MCP_NO_ELEM__'})()
        n_js = t.count(":null})()")
        t = t.replace(":null})()", ":'__MCP_NO_ELEM__'})()")
        print("  %-14s JS 表达式改哨兵: %d 处(全文件)" % (val_var, n_js))

        # 2) 在成功返回之前插入哨兵判定
        old = "                    如果 (%s != \"\" && %s != \"null\" && %s != \"undefined\"" % (
            val_var, val_var, val_var)
        # 兼容不同缩进: 用正则定位该守卫行
        pat = re.compile(r'( *)如果 \(%s != "" && %s != "null" && %s != "undefined".*?\n( *)\{\n' %
                         (re.escape(val_var), re.escape(val_var), re.escape(val_var)))
        m = pat.search(t)
        if not m:
            print("      !! %s 守卫行未匹配" % val_var)
            continue
        indent = m.group(1)
        inner = indent + "    "
        inject = (inner + "如果 (%s == \"__MCP_NO_ELEM__\")\n" % val_var +
                  inner + "{\n" +
                  inner + "    返回 (MCP_响应构建.命令失败 (命令ID, \"元素不存在或取不到值: \" + "
                  "MCP命令服务器.简单转义JS (selector) + \" | 建议: 先用 browser_fill_exists 或 "
                  "browser_snapshot 确认元素存在\"))\n" +
                  inner + "}\n")
        t = t[:m.end()] + inject + t[m.end():]
        print("      %s 已插入哨兵判定" % val_var)

    out = t.replace("\n", "\r\n") if crlf else t
    io.open(p, "wb").write(out.encode("utf-8"))
    print("  -> 写回 %s" % p.split("\\")[-1])
