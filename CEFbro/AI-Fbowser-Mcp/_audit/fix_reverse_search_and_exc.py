# -*- coding: utf-8 -*-
"""两处修复(均由 diag_reverse_search_js.py 实测证实):

修复1 (MCP_Server_Core.wsv, browser_reverse_search 的注入 JS):
    `t.split('\\r\n')` -> `t.split('\\n')`
  依据: 该项目字符串转义惯例是 `\n`=真实换行、`\\`=一个反斜杠(有据, 见脚本注释),
  于是现状生成给 JS 的是 `'` + 反斜杠 + `r` + 真实换行 + `'` = 单引号串里含裸换行
  = 未终止字符串 = 解析期 SyntaxError。
  A/B 实测(干净页面): 现状 -> `SyntaxError: Invalid or unexpected token` col=170;
  改成 `'\\n'` -> 正常返回 `{"query":"sign","found":0,"results":[]}`。

修复2 (MCP_Server.wsv, 共享的 JS 异常格式化器):
  原来优先读 exceptionDetails.text —— 而 CDP 的该字段**固定就是 "Uncaught"**,
  真正原因在 exceptionDetails.exception.description。
  于是任何走这条路的 JS 异常都只报 "JS异常:Uncaught", 不可行动(横切可诊断性缺陷)。
  改为: 优先 exception.description -> 再退回 text, 并附上 line/col 便于定位。

本脚本用 chr(92) 拼接反斜杠, 避免任何转义歧义; 写前断言"目标串恰好出现 1 次"。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '逆向搜索转义与异常诊断-写入前')
B = chr(92)   # 反斜杠
Q = chr(34)   # 双引号

# ---------- 修复1 ----------
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
OLD1 = "t.split('" + B + B + "r" + B + "n')"     # 文件里是 t.split('\\r\n')
NEW1 = "t.split('" + B + B + "n')"               # 改成    t.split('\\n')

# ---------- 修复2 ----------
SRV = os.path.join(SRC, 'MCP_Server.wsv')
OLD2 = '            excText = yyjson取文本 (excObj, ' + Q + 'text' + Q + ')'
NEW2 = '\n'.join([
    '            excText = ""',
    '            // ★ 修(可诊断性, 实测): CDP 的 exceptionDetails.text **固定就是 "Uncaught"** ——',
    '            //   真正的原因在 exceptionDetails.exception.description',
    '            //   (例: "SyntaxError: Invalid or unexpected token")。',
    '            //   原实现优先读 text, 于是**所有**走这条路径的 JS 异常都只报 "JS异常:Uncaught",',
    '            //   完全不可行动: 实测 browser_reverse_search 就因此把真实的解析期错误掩盖成 "Uncaught"。',
    '            变量 excInnerJSON <类型 = 文本型>',
    '            excInnerJSON = yyjson取JSON文本 (excObj, "exception")',
    '            变量 excInner <类型 = YYJSON只读对象类>',
    '            如果 (excInnerJSON != "" && excInner.创建自文本 (excInnerJSON))',
    '            {',
    '                excText = yyjson取文本 (excInner, "description")',
    '            }',
    '            如果 (excText == "")',
    '            {',
    '                excText = yyjson取文本 (excObj, "text")',
    '            }',
    '            // 附上行列: 解析期错误只有行列号, 靠它才能定位到注入串里的具体位置',
    '            变量 excLine <类型 = 整数>',
    '            excLine = yyjson取整数 (excObj, "lineNumber")',
    '            变量 excCol <类型 = 整数>',
    '            excCol = yyjson取整数 (excObj, "columnNumber")',
    '            如果 (excLine != 0 || excCol != 0)',
    '            {',
    '                excText = excText + " @line " + 到文本 (excLine) + " col " + 到文本 (excCol)',
    '            }',
])

# 修复2b: 删掉紧随其后的、现在已成冗余的兜底块(它读的是 exceptionDetails.description, 该层并不存在该键)
OLD2B = '\n'.join([
    '            如果 (excText == "")',
    '            {',
    '                excText = yyjson取文本 (excObj, "description")',
    '            }',
])


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (CORE, SRV):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)

    # 修复1
    c = rd(CORE)
    n1 = c.count(OLD1)
    print("\n[修复1] 目标串出现次数 = %d" % n1)
    if n1 != 1:
        print("!! 预期恰好 1 次, 中止(不改任何文件)")
        return 1
    c2 = c.replace(OLD1, NEW1)
    assert c2.count(NEW1) == 1 and OLD1 not in c2
    crlf_ok = ('\r\n' in c)
    wr(CORE, c2)
    print("  OK: %r -> %r" % (OLD1, NEW1))
    print("  (该文件原本使用 CRLF=%s, 写入保持原样)" % crlf_ok)

    # 修复2
    s = rd(SRV)
    n2 = s.count(OLD2)
    n2b = s.count(OLD2B)
    print("\n[修复2] 目标串出现次数 = %d ; 冗余兜底块 = %d" % (n2, n2b))
    if n2 != 1 or n2b != 1:
        print("!! 预期各恰好 1 次, 中止(不改任何文件)")
        return 1
    s2 = s.replace(OLD2, NEW2).replace(OLD2B, '')
    assert 'yyjson取文本 (excObj, "description")' not in s2, "冗余块未删净"
    assert s2.count('excText = yyjson取文本 (excInner, "description")') == 1
    wr(SRV, s2)
    print("  OK: 格式化器改为优先 exception.description, 并附 line/col; 冗余兜底块已删")

    # 复核: 反斜杠数量与编码未被破坏
    for p in (CORE, SRV):
        t = rd(p)
        with io.open(p, 'rb') as f:
            raw = f.read()
        print("\n复核 %s: BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'),
                 b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
