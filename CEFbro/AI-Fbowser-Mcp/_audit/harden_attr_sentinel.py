# -*- coding: utf-8 -*-
"""补强"元素存在但属性不存在"的场景。

现象(真机): browser_fill_attr_get {selector:"h1", attribute:"textContent"}
  -> {"type":"object","subtype":"null","value":null}
根因: getAttribute 对不存在的属性返回 null, CDP 把 null 序列化成对象描述;
      我的哨兵只在"元素不存在"时触发, 故此场景漏过 -> 又把难读的对象描述当答案返回。
  (注: 该用例本身期望写错了 —— textContent 是 property 不是 attribute, 返回 null 是正确的;
   但**返回形式**仍应可读, 而不是 CDP 内部描述。)

修法: 让 JS 自己区分两种情况并返回哨兵:
  元素不存在 -> '__MCP_NO_ELEM__'
  属性不存在 -> '__MCP_NO_ATTR__'
再各自给出可行动报错。
"""
import io
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

CORE = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv"
FORM = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Form.wsv"

# 目标: (文件, 表达式变量名, 属性变量名)
TARGETS = [
    (CORE, "js查询码", "attribute"),
    (FORM, "js属性码", "attr"),
]

for path, code_var, attr_var in TARGETS:
    raw = io.open(path, "rb").read()
    crlf = raw.count(b"\r\n") > 0
    t = raw.decode("utf-8").replace("\r\n", "\n")

    # 1) 改写 getAttribute 那一行: 用嵌套三元区分"元素不存在"与"属性不存在"
    pat = re.compile(r'( *)%s = "\(function\(\)\{var e=document\.querySelector\(\'" \+ '
                     r'MCP命令服务器\.简单转义JS \(selector\) \+ "\'\);return e\?e\.getAttribute\(\'" \+ '
                     r'MCP命令服务器\.简单转义JS \(%s\) \+ "\'\):\'__MCP_NO_ELEM__\'\}\)\(\)"' % (re.escape(code_var), attr_var))
    m = pat.search(t)
    if not m:
        print("  !! %s 在 %s 中未匹配到 getAttribute 表达式" % (code_var, path.split("\\")[-1]))
        continue
    indent = m.group(1)
    newline = (indent + code_var + ' = "(function(){var e=document.querySelector(\'" + '
               'MCP命令服务器.简单转义JS (selector) + "\');if(!e)return \'__MCP_NO_ELEM__\';'
               'var v=e.getAttribute(\'" + MCP命令服务器.简单转义JS (' + attr_var + ') + "\');'
               'return v===null?\'__MCP_NO_ATTR__\':v})()"')
    t = t[:m.start()] + newline + t[m.end():]
    print("  %-10s 表达式已改写为双哨兵" % code_var)

    # 2) 在该变量的哨兵判定里追加属性哨兵分支
    val_var = code_var.replace("码", "值")
    anchor = indent + '如果 (%s == "__MCP_NO_ELEM__")' % val_var
    if t.count(anchor) != 1:
        print("      !! 哨兵锚点不唯一(%d), 跳过追加" % t.count(anchor))
    else:
        brace_end = t.find("\n" + indent + "}", t.find(anchor))
        add = (indent + '如果 (%s == "__MCP_NO_ATTR__")\n' % val_var + indent + "{\n" +
               indent + '    返回 (MCP_响应构建.命令失败 (命令ID, "属性不存在: 元素已找到, 但没有该 HTML 属性 | '
               '提示: textContent/innerText/value 等是 DOM 属性(property)而非 HTML 属性, '
               '取它们请用 browser_get_text 或 browser_dom_query 的 selector 模式"))\n' +
               indent + "}\n")
        t = t[:brace_end + len("\n" + indent + "}") + 1] + add + t[brace_end + len("\n" + indent + "}") + 1:]
        print("      已追加 __MCP_NO_ATTR__ 判定")

    out = t.replace("\n", "\r\n") if crlf else t
    io.open(path, "wb").write(out.encode("utf-8"))
    print("  -> 写回 %s" % path.split("\\")[-1])
