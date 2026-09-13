# -*- coding: utf-8 -*-
"""只读侦察: 统计 wsv 里可能干扰花括号层级扫描的语法结构 (不修改任何文件)"""
import os, re, sys, collections
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')

def real_wsv():
    out = []
    for n in sorted(os.listdir(SRC)):
        if n.endswith('.wsv') and '.~vbak.' not in n:
            out.append(n)
    return out

def read_lines(p):
    with open(p, 'rb') as f:
        raw = f.read()
    if raw[:2] == b'\xff\xfe':
        txt = raw.decode('utf-16-le')
    elif raw[:3] == b'\xef\xbb\xbf':
        txt = raw.decode('utf-8-sig')
    else:
        txt = raw.decode('utf-8')
    return txt.replace('\r\n', '\n').replace('\r', '\n').split('\n')

stat = collections.Counter()
interesting = collections.defaultdict(list)

def strip_strings(s):
    """把 "..." 内容替换为等长占位, 保留引号位; 处理 \\ 转义"""
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '"':
            out.append('"')
            i += 1
            while i < n:
                if s[i] == '\\' and i + 1 < n:
                    out.append('  ')
                    i += 2
                    continue
                if s[i] == '"':
                    out.append('"')
                    i += 1
                    break
                out.append(' ')
                i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)

for fn in real_wsv():
    lines = read_lines(os.path.join(SRC, fn))
    for idx, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.startswith('@'):
            stat['at_line'] += 1
            continue
        if s.startswith('#') or s.startswith("'") or s.startswith('//'):
            stat['comment_line'] += 1
            if '{' in s or '}' in s:
                interesting['comment_with_brace'].append((fn, idx, ln))
            continue
        st = strip_strings(ln)
        # 注释剥离后看剩下的花括号
        for m in ('//',):
            pos = st.find(m)
            if pos >= 0:
                stat['inline_comment'] += 1
                if '{' in st[pos:] or '}' in st[pos:]:
                    interesting['inline_comment_with_brace'].append((fn, idx, ln))
                break
        nc = strip_strings(ln).split('//')[0]
        if '{' in nc or '}' in nc:
            if nc.strip() not in ('{', '}'):
                stat['inline_brace'] += 1
                interesting['inline_brace'].append((fn, idx, ln))
        # 字符串里的花括号
        if strip_strings(ln) != ln and ('{' in ln or '}' in ln):
            # 判断花括号是否在字符串内
            ss = strip_strings(ln)
            cnt_raw = ln.count('{') + ln.count('}')
            cnt_st = ss.count('{') + ss.count('}')
            if cnt_raw != cnt_st:
                stat['brace_in_string'] += 1
                interesting['brace_in_string'].append((fn, idx, ln))
        if re.search(r'^\s*(如果|否则|循环|计次循环|判断循环|变量循环|跳出循环|继续循环|返回|到循环尾)', s):
            stat['kw_' + re.match(r'^\s*(\S+?)[\s(（]', s + ' ').group(1)] += 1

for k, v in sorted(stat.items()):
    print(f'{k}: {v}')
print()
for k, v in interesting.items():
    print(f'--- {k}: {len(v)} ---')
    for item in v[:25]:
        print('   ', item[0], item[1], item[2][:160])
