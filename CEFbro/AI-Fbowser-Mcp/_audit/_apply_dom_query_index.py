# -*- coding: utf-8 -*-
r"""第127轮: 修掉 `browser_dom_query` 的 **index 静默失效**（"返回第 1 个匹配却当作第 N 个" —— 比报错更危险）。

缺陷依据（只读审计 `_audit/_schema_audit_A.md` Top 15 第 14 条 + 源码核实）:
  · schema 声明了 `index`，而实现只用 `document.querySelector`（永远第一个匹配），
    原生回退路径也把索引写死 0: `取元素属性 (selector, 0, ...)` / `取元素内容 (selector, 0, ...)`。
  ⇒ 传 index=3 会**静默拿到第 1 个**元素的值 = 静默错答案。

改法(按唯一子串定位, 不整块替换, 避免缩进猜错):
  1) 两条 JS 路径改用 `querySelectorAll(sel)[index]`；越界返回 `__MCP_NO_INDEX__:<匹配数>`;
  2) 宿主把越界转成**可行动失败**（点明"实际只有 N 个匹配"）；负索引明确拒绝;
  3) 原生回退把索引如实透传。

用法: py -3 _audit\_apply_dom_query_index.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

# 1) 属性路径的 JS
ATTR_OLD = '''js查询码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');if(!e)return '__MCP_NO_ELEM__';var v=e.getAttribute('" + MCP命令服务器.简单转义JS (attribute) + "');return v===null?'__MCP_NO_ATTR__':v})()"'''
ATTR_NEW = '''js查询码 = "(function(){var l=document.querySelectorAll('" + MCP命令服务器.简单转义JS (selector) + "');if(!l.length)return '__MCP_NO_ELEM__';var i=" + 到文本 (查询索引) + ";if(i>=l.length)return '__MCP_NO_INDEX__:'+l.length;var v=l[i].getAttribute('" + MCP命令服务器.简单转义JS (attribute) + "');return v===null?'__MCP_NO_ATTR__':v})()"'''

# 2) 文本路径的 JS
TEXT_OLD = '''js查询码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');return e?e.textContent:'__MCP_NO_ELEM__'})()"'''
TEXT_NEW = '''js查询码 = "(function(){var l=document.querySelectorAll('" + MCP命令服务器.简单转义JS (selector) + "');if(!l.length)return '__MCP_NO_ELEM__';var i=" + 到文本 (查询索引) + ";if(i>=l.length)return '__MCP_NO_INDEX__:'+l.length;return l[i].textContent})()"'''

# 3) 索引读取 + 负值拒绝(插在 js查询码 声明之前)
DECL_OLD = '''结合真实需求'''  # 占位(不用)
INDEX_ANCHOR = '''                    变量 js查询码 <类型 = 文本型>'''
INDEX_NEW = '''                    // ★ index 必须真的生效: 此前实现写死 querySelector(第 1 个匹配), 传 index=3 会**静默拿到第 1 个**
                    //   —— 属"静默错答案", 比报错更危险。改用 querySelectorAll[index]; 越界时如实报"实际有几个匹配"。
                    变量 查询索引 <类型 = 整数>
                    查询索引 = MCP命令服务器.yyjson取整数 (参数JSON, "index")
                    如果 (查询索引 < 0)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "index 不能为负: " + 到文本 (查询索引) + " | 索引从 0 开始(0=第 1 个匹配)"))
                    }
                    变量 js查询码 <类型 = 文本型>'''

# 4) 越界守卫(锚在 dom_query 特有的 NO_ATTR 守卫 + 成功返回之间; 单独的 NO_ELEM 文案在 Core 里有 5 处, 不可用)
NOELEM_OLD = '''                        如果 (js查询值 == "__MCP_NO_ATTR__")
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "属性不存在: 元素已找到, 但没有该 HTML 属性 | 提示: textContent/innerText/value 等是 DOM 属性(property)而非 HTML 属性, 取它们请用 browser_get_text 或 browser_dom_query 的 selector 模式"))
                        }
                        返回 (MCP_响应构建.命令成功 (命令ID, js查询值))'''
NOELEM_NEW = '''                        如果 (js查询值 == "__MCP_NO_ATTR__")
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "属性不存在: 元素已找到, 但没有该 HTML 属性 | 提示: textContent/innerText/value 等是 DOM 属性(property)而非 HTML 属性, 取它们请用 browser_get_text 或 browser_dom_query 的 selector 模式"))
                        }
                        // 索引越界: 如实报"实际有几个匹配", 绝不退回第一个(否则就是静默错答案)
                        如果 (是否以 (js查询值, "__MCP_NO_INDEX__:"))
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "index 越界: 请求 index=" + 到文本 (查询索引) + ", 但该选择器**实际只有 " + 取文本右边 (js查询值, 取文本长度 (js查询值) - 取文本长度 ("__MCP_NO_INDEX__:")) + " 个匹配** | 索引从 0 开始; 去掉 index 参数即取第 1 个匹配"))
                        }
                        返回 (MCP_响应构建.命令成功 (命令ID, js查询值))'''

# 5) 原生回退透传索引
FB_ATTR_OLD = '填表框架.取元素属性 (selector, 0, attribute, 填表回调)'
FB_ATTR_NEW = '填表框架.取元素属性 (selector, 查询索引, attribute, 填表回调)'
FB_TEXT_OLD = '填表框架.取元素内容 (selector, 0, 内容回调)'
FB_TEXT_NEW = '填表框架.取元素内容 (selector, 查询索引, 内容回调)'

# 6) schema 描述
DESC_OLD = '属性项JSON ("index", "integer", "索引")'
DESC_NEW = ('属性项JSON ("index", "integer", "取第几个匹配(从 0 开始; 缺省=第 1 个)。**越界会明确失败并告出实际匹配数**, '
            '不会静默返回第 1 个; 负值被拒绝")')


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def main():
    txt = io.open(CORE, encoding='utf-8').read()
    has_cr = '\r' in txt
    b0, n0 = balance(txt), len(txt.split('\n'))
    out = txt
    for tag, old, new in (('属性JS', ATTR_OLD, ATTR_NEW),
                          ('文本JS', TEXT_OLD, TEXT_NEW),
                          ('索引读取+负值拒绝', INDEX_ANCHOR, INDEX_NEW),
                          ('越界守卫', NOELEM_OLD, NOELEM_NEW),
                          ('原生回退-属性', FB_ATTR_OLD, FB_ATTR_NEW),
                          ('原生回退-内容', FB_TEXT_OLD, FB_TEXT_NEW)):
        cnt = out.count(old)
        assert cnt == 1, '%s 锚点 %d 次' % (tag, cnt)
        out = out.replace(old, new, 1)
        print('   · %s' % tag)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server_Core.wsv: 行数 %d -> %d (CR=%s); 括号净值 %s 不变'
          % (n0, len(out.split('\n')), has_cr, balance(out)))

    lines = io.open(SERVER, encoding='utf-8').read().split('\n')
    idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_dom_query"' in ln]
    assert len(idx) == 1, 'dom_query 注册行 %d' % len(idx)
    i = idx[0]
    assert lines[i].count(DESC_OLD) == 1, 'index 属性锚点 %d' % lines[i].count(DESC_OLD)
    lines[i] = lines[i].replace(DESC_OLD, DESC_NEW, 1)
    s_out = '\n'.join(lines)
    print('MCP_Server.wsv: index 属性描述已改准')

    if '--apply' in sys.argv:
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(out)
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        c = io.open(CORE, encoding='utf-8').read()
        assert 'querySelectorAll' in c and '__MCP_NO_INDEX__:' in c and ('\r' in c) == has_cr
        s = io.open(SERVER, encoding='utf-8').read()
        assert '不会静默返回第 1 个' in s and '\r' not in s
        print('已写入 Core + Server 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
