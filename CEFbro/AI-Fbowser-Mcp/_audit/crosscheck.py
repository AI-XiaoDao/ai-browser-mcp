# -*- coding: utf-8 -*-
"""
crosscheck.py — 与 deadscan.py **相互独立**的第二实现, 用于交叉验证探测 A。

思路完全不同(不用块树): 对每一个"叶子 返回/跳出循环/继续循环/到循环尾"行, 记录它的
花括号嵌套深度 d, 然后**向前**逐行累加花括号深度, 找到下一个非注释非空代码行:
  * 若该行的深度 == d  → 它是同级兄弟语句 → 死代码 (无条件跳转后不可达)
  * 若该行深度 < d     → 本容器已闭合 → 没有死代码
(因为火山里"块头行"总在 "{" 之前, 所以返回之后的第一个同级代码行不可能是新块的 "{"。)

字符串掩码 / 注释剥离 / @ 行跳过的规则与 deadscan.py 相同。
只读: 不写任何 src 文件。
"""
import os, re, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'src')

RE_RETURN = re.compile(r'^返回(\s*$|\s*\(|\s)')
RE_BREAK = re.compile(r'^跳出循环(\s*$|\s*\()')
RE_CONT = re.compile(r'^(继续循环|到循环尾)(\s*$|\s*\()')


def read_lines(path):
    raw = open(path, 'rb').read()
    txt = raw.decode('utf-16-le') if raw[:2] == b'\xff\xfe' else raw.decode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8')
    return txt.replace('\r\n', '\n').replace('\r', '\n').split('\n')


def mask(s):
    o, i, n = [], 0, len(s)
    while i < n:
        if s[i] == '"':
            o.append('"'); i += 1
            while i < n:
                if s[i] == '\\' and i + 1 < n:
                    o.append('  '); i += 2; continue
                if s[i] == '"':
                    o.append('"'); i += 1; break
                o.append(' '); i += 1
            continue
        o.append(s[i]); i += 1
    return ''.join(o)


def clean(line):
    s = line.strip()
    if not s or s[0] in "#'@" or s.startswith('//'):
        return None
    m = mask(line)
    c = len(m)
    for mk in ('//', '\\\\'):
        p = m.find(mk)
        if p >= 0:
            c = min(c, p)
    t = m[:c].strip()
    return t or None


def depth_delta(t):
    return t.count('{') - t.count('}')


def scan(path):
    fname = os.path.basename(path)
    lines = read_lines(path)
    depth = 0
    info = []            # (lineno, depth_before, cleaned_text)
    for i, raw in enumerate(lines, 1):
        t = clean(raw)
        if t is None:
            continue
        if t == '{':
            depth += 1
        elif t == '}':
            depth -= 1
        info.append((i, depth, t))
    # 找叶子跳转
    hits = []
    for k, (ln, d, t) in enumerate(info):
        if t in ('{', '}'):
            continue
        if not (RE_RETURN.match(t) or RE_BREAK.match(t) or RE_CONT.match(t)):
            continue
        # 向前找下一个同级代码行
        j = k + 1
        found = None
        while j < len(info):
            ln2, d2, t2 = info[j]
            if d2 < d:
                break
            if d2 == d and t2 not in ('{', '}'):
                found = (ln2, t2)
                break
            if d2 == d and t2 == '}':
                break
            if d2 > d:
                # 进入了更深的块: 说明存在同级块头? 不可能(块头在 { 之前), 保守跳出
                break
            j += 1
        if found:
            hits.append((ln, d, t, found[0], found[1]))
    return fname, hits


def main():
    names = [n for n in sorted(os.listdir(SRC)) if n.endswith('.wsv') and '.~vbak.' not in n]
    total_jumps = 0
    allhits = []
    for n in names:
        fname, hits = scan(os.path.join(SRC, n))
        allhits.extend([(fname,) + h for h in hits])
    print('### crosscheck: 同级兄弟不可达候选 %d 处' % len(allhits))
    for h in allhits:
        fn, jl, d, jt, nl, nt = h
        print('  %s' % fn)
        print('     跳转行 : L%d  (嵌套深度 %d)' % (jl, d))
        print('              %s' % jt[:130])
        print('     随后同级代码行: L%d' % nl)
        print('              %s' % nt[:130])
        print()
    with open(os.path.join(HERE, '_crosscheck.txt'), 'w', encoding='utf-8') as fp:
        fp.write('file\tjump_line\tdepth\tnext_line\tjump_text\tnext_text\n')
        for fn, jl, d, jt, nl, nt in allhits:
            fp.write('%s\t%d\t%d\t%d\t%s\t%s\n' % (fn, jl, d, nl, jt, nt))


if __name__ == '__main__':
    main()
