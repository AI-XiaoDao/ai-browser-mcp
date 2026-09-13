# -*- coding: utf-8 -*-
"""
deadscan.py — 只读死代码候选探测器 (火山视窗 .wsv)

主判据 (探测 A): 同一花括号容器内, 一个**叶子** `返回`/`跳出循环`/`继续循环`/`到循环尾`
                 无条件执行 → 它在该容器内的后续兄弟语句永不可达。

副判据 (探测 B, 低置信度): 容器内存在一条**完整 if/else 链**且每个分支都以
                 无条件跳转收尾 → 该链之后的兄弟语句永不可达。
                 (需要"存在 否则"才判, 避免漏掉隐式 case。)

火山语法处理要点:
  * 花括号层级栈逐行扫描。
  * `@` 开头行 = 内嵌 C++ 原文, 其中 { } 完全跳过。
  * `#` / `//` / `'` 开头整行 = 注释, 跳过。
  * 先做字符串字面量掩码再剥行内 `//`/`\\\\` 注释 → 字符串与注释里的 { } 不计数。
  * 花括号头部若为 `参数 ...` 则回溯到 `方法`/`类`/`事件定义` 行。
  * 语句可跨行(括号未闭合或行尾运算符则续行)。
  * `否则` 是分支续接, 遇到即撤销死区 → 从结构上免疫"否则分支被误报"。

只读: 不写任何 src 文件。
"""
import os, re, sys, json, collections
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_DEFAULT_SRC = os.path.join(ROOT, 'src')
# 允许传入自定义目录(仅用于 _audit 下的合成校准样本); 默认仍是 src
SRC = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else _DEFAULT_SRC
IS_REAL_SRC = (os.path.abspath(SRC) == os.path.abspath(_DEFAULT_SRC))

# ---------------------------------------------------------------- 读取/清理


def read_lines(path):
    raw = open(path, 'rb').read()
    if raw[:2] == b'\xff\xfe':
        txt = raw.decode('utf-16-le')
    elif raw[:2] == b'\xfe\xff':
        txt = raw.decode('utf-16-be')
    elif raw[:3] == b'\xef\xbb\xbf':
        txt = raw.decode('utf-8-sig')
    else:
        txt = raw.decode('utf-8')
    return txt.replace('\r\n', '\n').replace('\r', '\n').split('\n')


def mask_strings(s):
    out = []
    i, n = 0, len(s)
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


def strip_line(line):
    """-> (清理后文本, 是否跳过, 原始种类)"""
    s = line.strip()
    if not s:
        return '', True, 'blank'
    if s.startswith('@'):
        return '', True, 'cpp'
    if s.startswith('#'):
        return '', True, 'comment'
    if s.startswith("'") or s.startswith('//'):
        return '', True, 'comment'
    m = mask_strings(line)
    cut = len(m)
    for marker in ('//', '\\\\'):
        p = m.find(marker)
        if p >= 0:
            cut = min(cut, p)
    return m[:cut].strip(), False, 'code'


def paren_delta(t):
    d = 0
    for ch in t:
        if ch in '([':
            d += 1
        elif ch in ')]':
            d -= 1
    return d


def looks_continued(t):
    t = t.rstrip()
    if not t:
        return False
    if t.endswith('&&') or t.endswith('||'):
        return True
    return t.endswith(('+', ',', '='))


# ---------------------------------------------------------------- 语法分类

RE_METHOD = re.compile(r'^方法\s')
RE_CLASS = re.compile(r'^类\s')
RE_EVENTDEF = re.compile(r'^(定义事件|事件定义)\s')
RE_PARAM = re.compile(r'^参数\s')
RE_IF = re.compile(r'^(如果|如果真)\s*\(')
RE_ELSE = re.compile(r'^否则(\s*\(|\s*$)')
RE_ELSE_BARE = re.compile(r'^否则\s*$')

RE_RETURN = re.compile(r'^返回(\s*$|\s*\(|\s)')
RE_BREAK = re.compile(r'^跳出循环(\s*$|\s*\()')
RE_CONT = re.compile(r'^(继续循环|到循环尾)(\s*$|\s*\()')
UNCOND_JUMPS = (('返回', RE_RETURN), ('跳出循环', RE_BREAK), ('继续循环/到循环尾', RE_CONT))

LOOP_KWS = ('循环判断首', '计次循环', '判断循环', '变量循环', '循环')


def is_jump(t):
    for label, rx in UNCOND_JUMPS:
        if rx.match(t):
            return label
    return None


def classify_header(t):
    if not t:
        return 'unknown'
    if RE_METHOD.match(t):
        return 'method'
    if RE_CLASS.match(t):
        return 'class'
    if RE_EVENTDEF.match(t):
        return 'event'
    if RE_PARAM.match(t):
        return 'param'
    if RE_IF.match(t):
        return 'if'
    if RE_ELSE.match(t):
        return 'else'
    for kw in LOOP_KWS:
        if t.startswith(kw):
            return 'loop'
    if t.startswith('判断'):
        return 'switch'
    return 'unknown'


# ---------------------------------------------------------------- 帧


class Frame(object):
    __slots__ = ('idx', 'kind', 'header_line', 'header_text', 'header_raw',
                 'brace_line', 'close_line', 'parent', 'file', 'children',
                 'blocks', 'dead_at', 'dead_stmt', 'dead_kind', 'dead_children',
                 'inherited_dead', 'ok')

    def __init__(self, idx, kind, hline, htext, brace_line, parent, fname, hraw=''):
        self.idx = idx
        self.kind = kind
        self.header_line = hline
        self.header_text = htext          # 字符串已被掩码(用于分类)
        self.header_raw = hraw or htext   # 原文(用于报告展示)
        self.brace_line = brace_line
        self.close_line = None
        self.parent = parent
        self.file = fname
        self.children = []       # (lineno, text, tag)  tag: stmt|block|else
        self.blocks = []         # 直接子块 Frame
        self.dead_at = None
        self.dead_stmt = None
        self.dead_kind = None
        self.dead_children = []
        self.inherited_dead = False
        self.ok = True           # 该块内所有分支都以跳转收尾 (探测 B 用)

    def method_name(self):
        f = self
        while f is not None:
            if f.kind == 'method':
                m = re.match(r'^方法\s+([^\s<]+)', f.header_text)
                return m.group(1) if m else f.header_text[:40]
            f = f.parent
        return '<类/文件级>'

    def class_name(self):
        f = self
        while f is not None:
            if f.kind == 'class':
                m = re.match(r'^类\s+([^\s<]+)', f.header_text)
                return m.group(1) if m else f.header_text[:40]
            f = f.parent
        return ''

    def chain(self):
        out = []
        f = self.parent
        while f is not None and f.kind != 'root':
            out.append('%s(L%d)' % (f.kind, f.header_line))
            f = f.parent
        return ' < '.join(reversed(out)) if out else '(顶层)'


# ---------------------------------------------------------------- 扫描


def scan_file(path, diags):
    fname = os.path.basename(path)
    lines = read_lines(path)
    root = Frame(0, 'root', 0, '', 0, None, fname)
    root.close_line = len(lines)
    frames = [root]
    stack = [root]
    cur = root
    prev_headers = []
    counter = [0]

    i, n = 0, len(lines)
    while i < n:
        lineno = i + 1
        text, skipped, kind_raw = strip_line(lines[i])
        if skipped:
            i += 1
            continue

        # 关闭块
        if text == '}':
            if len(stack) <= 1:
                diags['unbalanced'].append((fname, lineno, '多余的 }'))
                i += 1
                continue
            closed = stack.pop()
            closed.close_line = lineno
            cur = stack[-1]
            prev_headers.append((lineno, '}', lines[lineno - 1].strip()))
            i += 1
            continue
        if text.startswith('}'):
            diags['brace_line_odd'].append((fname, lineno, lines[i].strip()))

        # 打开块
        if text == '{':
            # 头部 = 向前回溯: 跳过 `参数 ...` 行 与 多行头部的续行(如 `注释 = "..." @输出名 = ...>`)
            hj = len(prev_headers) - 1
            while hj >= 0:
                cand = prev_headers[hj][1]
                if cand.startswith('参数') or cand.startswith('注释') or re.match(r'^\S+\s*=', cand):
                    hj -= 1
                    continue
                if classify_header(cand) == 'unknown' and hj > 0 and not cand.startswith(('{', '}')):
                    hj -= 1
                    continue
                break
            if hj < 0:
                hline, htext, hraw = lineno, '', ''
                diags['brace_without_header'].append((fname, lineno, lines[i].strip()))
            else:
                hline, htext, hraw = prev_headers[hj]
            bkind = classify_header(htext)
            if bkind == 'unknown':
                diags['unknown_block_header'].append((fname, hline, hraw[:100]))
            counter[0] += 1
            f = Frame(counter[0], bkind, hline, htext, lineno, cur, fname, hraw)
            f.inherited_dead = (cur.dead_at is not None) or cur.inherited_dead
            frames.append(f)
            cur.blocks.append(f)
            stack.append(f)
            cur = f
            prev_headers.append((lineno, '{', lines[lineno - 1].strip()))
            i += 1
            continue

        # 一条语句 (可跨行)
        start = lineno
        seg = [text]
        rawseg = [lines[lineno - 1].strip()]
        depth = paren_delta(mask_strings(text))
        guard = 0
        while (depth > 0 or looks_continued(seg[-1])) and i + 1 < n and guard < 40:
            i += 1
            guard += 1
            t2, sk2, _ = strip_line(lines[i])
            if not t2:
                continue
            seg.append(t2)
            rawseg.append(lines[i].strip())
            depth += paren_delta(mask_strings(t2))
        if guard:
            diags['multiline_stmt'].append((fname, start, ' | '.join(seg)[:200]))
        stmt = ' '.join(seg)
        raw_stmt = ' '.join(rawseg)

        prev_headers.append((start, stmt, raw_stmt))
        if len(prev_headers) > 10:
            prev_headers.pop(0)

        if RE_ELSE.match(stmt):
            if cur.dead_at is not None:
                diags['else_after_bare_jump'].append(
                    (fname, start, stmt[:90], cur.dead_at, (cur.dead_stmt or '')[:90]))
                cur.dead_at = None
                cur.dead_stmt = None
                cur.dead_kind = None
                cur.dead_children = []
            cur.children.append((start, stmt, 'else'))
            i += 1
            continue

        cur.children.append((start, stmt, 'stmt'))
        if cur.dead_at is not None:
            cur.dead_children.append((start, stmt))
        if cur.dead_at is None and not cur.inherited_dead:
            lab = is_jump(stmt)
            if lab:
                cur.dead_at = start
                cur.dead_stmt = stmt
                cur.dead_kind = lab
        i += 1

    # ---- 基石假设检查: 每个块头(如果/否则/循环*/方法/类)后面必须紧跟 `{`
    code_idx = []
    for k, raw in enumerate(lines, 1):
        t, sk, _ = strip_line(raw)
        if not sk:
            code_idx.append((k, t))
    for a in range(len(code_idx) - 1):
        k, t = code_idx[a]
        nk, nt = code_idx[a + 1]
        if t in ('{', '}'):
            continue
        if t.startswith('循环判断尾'):
            continue          # 循环体"尾部"关键字, 不是块头
        kd = classify_header(t)
        if kd in ('method', 'class', 'event'):
            # 方法/类 头后面可能还有 参数 行
            continue
        if kd in ('if', 'else', 'loop', 'switch'):
            if nt != '{':
                diags['header_not_followed_by_brace'].append((fname, k, t[:90], nk, nt[:90]))

    if len(stack) != 1:
        diags['unbalanced'].append((fname, n, 'EOF 时栈深=%d (花括号不配平)' % len(stack)))

    # ---- 探测 B: 完整 if/else 链且全分支跳转收尾 -> 后续兄弟不可达
    probe_b = []
    for f in frames:
        if f.kind in ('root',):
            continue
        blocks = f.blocks
        # 收集连续的 if/else 链
        j = 0
        consumed_upto = None
        while j < len(blocks):
            b = blocks[j]
            if b.kind != 'if':
                j += 1
                continue
            chain = [b]
            k = j + 1
            while k < len(blocks) and blocks[k].kind == 'else':
                chain.append(blocks[k])
                k += 1
            # 必须存在**兜底** `否则 {` (无条件的), 否则链不穷尽 -> 后续仍可达
            catchall = len(chain) > 1 and RE_ELSE_BARE.match(chain[-1].header_text.strip())
            all_jump = all(c.dead_at is not None and c.dead_kind == '返回' for c in chain)
            if catchall and all_jump:
                probe_b.append((f, chain))
            j = k
    return root, frames, probe_b


# ---------------------------------------------------------------- 报告

def raw_kind(lines, ln):
    t = lines[ln - 1].strip()
    if not t:
        return 'blank'
    if t.startswith('@'):
        return 'cpp'
    if t.startswith('#') or t.startswith("'") or t.startswith('//'):
        return 'comment'
    return 'code'


def main():
    diags = collections.defaultdict(list)
    names = [nm for nm in sorted(os.listdir(SRC))
             if nm.endswith('.wsv') and '.~vbak.' not in nm]
    baks = [nm for nm in sorted(os.listdir(SRC))
            if nm.endswith('.wsv') and '.~vbak.' in nm]

    all_frames, all_b, all_lines, method_total = [], [], {}, 0
    for nm in names:
        lines = read_lines(os.path.join(SRC, nm))
        all_lines[nm] = lines
        _, frames, pb = scan_file(os.path.join(SRC, nm), diags)
        all_frames.extend(frames)
        all_b.extend(pb)
        method_total += sum(1 for f in frames if f.kind == 'method')

    findings = [f for f in all_frames if f.dead_at is not None and f.dead_children]

    outA = []
    print('### 探测 A: 无条件跳转后的兄弟语句 (共 %d 处)' % len(findings))
    for f in sorted(findings, key=lambda x: (x.file, x.dead_at)):
        lines = all_lines[f.file]
        # 向上找最近一个形如 `否则 (方法名 == "xxx")` 的工具分支
        br = None
        g = f.parent
        while g is not None:
            if '方法名 ==' in g.header_raw:
                br = (g.kind, g.header_line, g.header_raw.strip())
                break
            g = g.parent
        rec = {
            'file': f.file, 'class': f.class_name(), 'method': f.method_name(),
            'container_kind': f.kind, 'container_header_line': f.header_line,
            'container_header': f.header_raw.strip(),
            'container_brace_line': f.brace_line,
            'container_close_line': f.close_line,
            'container_chain': f.chain(),
            'branch_kind': br[0] if br else '', 'branch_line': br[1] if br else 0,
            'branch_header': br[2] if br else '',
            'jump_line': f.dead_at, 'jump_kind': f.dead_kind,
            'jump_text': lines[f.dead_at - 1].strip(),
            'dead_region': [],
        }
        end = f.close_line or len(lines)
        for ln in range(f.dead_at + 1, end + 1):
            k = raw_kind(lines, ln)
            rec['dead_region'].append({'line': ln, 'kind': k, 'text': lines[ln - 1].strip()})
        outA.append(rec)

        print('-' * 74)
        print('文件      : %s' % f.file)
        print('类        : %s' % f.class_name())
        print('方法      : %s' % f.method_name())
        print('容器      : %s  L%d  %s' % (f.kind, f.header_line, f.header_text.strip()[:110]))
        print('容器花括号: L%d ... L%d' % (f.brace_line, f.close_line))
        print('容器链    : %s' % f.chain())
        print('无条件跳转: %s  L%d' % (f.dead_kind, f.dead_at))
        print('            %s' % lines[f.dead_at - 1].strip()[:190])
        print('紧随其后 (死区, 该容器内至 L%d):' % end)
        for d in rec['dead_region']:
            print('    L%-6d [%-7s] %s' % (d['line'], d['kind'], d['text'][:160]))
    print()

    print('### 探测 B: 完整 if/else 链(含兜底 否则)全分支返回 (穷尽链数 %d)' % len(all_b))
    outB = []
    n_terminal = 0
    for f, chain in sorted(all_b, key=lambda x: (x[0].file, x[0].header_line)):
        lines = all_lines[f.file]
        # 链后兄弟
        after = [c for c in f.children if c[0] > chain[-1].close_line]
        if not after:
            n_terminal += 1
            continue
        rec = {
            'file': f.file, 'method': f.method_name(), 'container': f.header_raw.strip(),
            'chain': [{'line': c.header_line, 'text': c.header_raw.strip()} for c in chain],
            'dead_children': [{'line': a[0], 'text': a[1].strip()} for a in after],
        }
        outB.append(rec)
        print('-' * 74)
        print('文件:%s  方法:%s' % (f.file, f.method_name()))
        print('容器:%s  L%d' % (f.kind, f.header_line))
        for c in chain:
            print('  链分支 L%-6d %s' % (c.header_line, c.header_raw.strip()[:110]))
        print('  链后兄弟(候选死代码):')
        for a in after:
            print('    L%-6d %s' % (a[0], a[1].strip()[:150]))
    print('  → 其中 %d 条穷尽链之后**没有任何**同级语句(链即容器末句) → 非死代码' % n_terminal)
    print('  → 剩余 %d 条穷尽链之后存在同级语句 → 候选' % len(outB))
    print()

    print('### 诊断')
    print('扫描文件数     : %d' % len(names))
    print('方法总数       : %d' % method_total)
    print('块类型分布     : %s' % dict(collections.Counter(f.kind for f in all_frames)))
    print('跳过的备份文件 : %d  %s' % (len(baks), ', '.join(baks)))
    for k in sorted(diags):
        print('%-22s: %d' % (k, len(diags[k])))
        for item in diags[k][:20]:
            print('     ', item)

    out_json = '_deadscan.json' if IS_REAL_SRC else '_deadscan_calib.json'
    with open(os.path.join(HERE, out_json), 'w', encoding='utf-8') as fp:
        json.dump({'A': outA, 'B': outB,
                   'stats': {'files': len(names), 'methods': method_total,
                             'findingsA': len(findings), 'findingsB': len(outB)}},
                  fp, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
