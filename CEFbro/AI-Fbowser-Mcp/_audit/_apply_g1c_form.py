# -*- coding: utf-8 -*-
r"""G1-c: MCP_Server_Form.wsv —— "CDP 优先" 的 JS 求值改为**框架感知**入口。

背景
    src/MCP_Server_Form.wsv 里"填表/DOM"分支的 CDP 优先路径一律在主框架求值:
        js值 = MCP命令服务器.CDP执行JS并等待 (js码, 10000, 真)
    即使 Schema 收了 frame_id, 带 frame_id 调用也读不到 iframe 里的内容
    (静默在主框架求值 —— 最难发现的一类错误答案)。

    主代理已在 src/MCP_Server.wsv 增加 4 参入口(本脚本会先核对它存在且形参顺序正确):
        MCP命令服务器.CDP执行JS按框架 (浏览器, 参数JSON, JS代码, 最大毫秒)
    无 frame_id(或 main/主框架)时该入口内部直接转调 CDP执行JS并等待 -> 行为逐字一致;
    传了 frame_id 但解析不到时返回 {"error":...}, 明确失败而不是静默回主框架。

本脚本只做一件事: 把 3 参形式
        MCP命令服务器.CDP执行JS并等待 (X, Y, 真)
按 **行号 + 原文精确匹配** 双重定位, 逐点改写成
        MCP命令服务器.CDP执行JS按框架 (<browser>, 参数JSON, X, Y)

门禁(判定依据, 不是拍脑袋)
    1) 命中点必须落在 `方法名 == "..."` 的工具分派分支里, 且该分支的浏览器变量/参数JSON 在作用域内;
    2) 该工具在 MCP_Server.wsv 的 `添加工具JSON ("<工具名>" ...)` 注册里**确实含 "frame_id"** 才改写;
       注册里没有 frame_id 的分支 -> 打印原因后**跳过**(收了 frame_id 也无处可取);
    3) 落在辅助方法(如 前置存在校验)里、作用域内没有 browser / 参数JSON 的调用点 -> 跳过并打印原因。

安全断言(任何一条不满足就报错退出, 绝不"尽量替换")
    替换前: 行号命中 + 整行(缩进空格数 + 去缩进去尾原文)与审计快照逐字相同
            + 该行内调用片段恰好 1 次 + 片段在全文件的命中行集合与审计快照一致
            + 分支行确实声明了该工具的 `方法名 ==`, 浏览器变量名与审计一致, 参数JSON 在方法形参里
            + 调用确实是 3 参形式且第 3 参是 真
    替换后: 行数不变 + 实际改动行集合 == 预期集合 + 每个改动行文本括号/花括号净额 0
            + 全文件花括号净额不变 + 全文件圆括号净额不变(均跳过 @ / # 引导行)
    写盘:   编码 UTF-8 无 BOM; **行尾按行原样保留**(读写往返必须与原文逐字节相同才允许写盘)。

行尾说明(实测, 与任务书假设不同)
    该文件当前**不是纯 LF**: 多数行是 CRLF。任务书假设 src/*.wsv 是 LF, 故此处有两种选择:
      * 默认: 逐行保留原有行尾 -> 字节级最小改动, 只有被改的那几行发生变化;
      * --force-lf: 按任务书字面要求把整文件行尾规范化为 LF(会产生整文件行尾差异)。
    默认取前者(最小增量修改优先), 并把实测行尾统计打印出来, 由主代理决定是否加 --force-lf。

用法
    py -3 _audit/_apply_g1c_form.py                # dry-run(默认): 打印 行号 / 旧文本 / 新文本
    py -3 _audit/_apply_g1c_form.py --apply        # 真正写回 src/MCP_Server_Form.wsv
    py -3 _audit/_apply_g1c_form.py --apply --force-lf   # 写回并把整文件行尾规范化为 LF

本脚本只写这一个文件; MCP_Server.wsv 只读(用于 Schema 门禁与入口核对)。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401  导入即把 stdout/stderr 切成 UTF-8(防中文/emoji 打印崩)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FORM = os.path.join(ROOT, 'src', 'MCP_Server_Form.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

OLD_METHOD = 'CDP执行JS并等待'
NEW_METHOD = 'CDP执行JS按框架'
OLD_CALL = 'MCP命令服务器.' + OLD_METHOD
NEW_CALL = 'MCP命令服务器.' + NEW_METHOD
NEW_PARAMS = ['浏览器', '参数JSON', 'JS代码', '最大毫秒']

# 审计快照(src/MCP_Server_Form.wsv, 2026-09-13 审计): 行数 672 = 671 行原文 + 末尾空行
# (行尾实测: CRLF=671, 无行尾=1 —— 该文件**不是纯 LF**); 仅作漂移告警, 不是硬门禁
AUDIT_LINES = 672

# 逐点审计结论。字段含义:
#   line   审计时的 1-based 行号        indent 该行缩进的空格数(字节级)
#   body   去缩进后的整行原文(逐字)     frag_lines 该行的调用片段在**全文件**的所有命中行(1-based)
#   browser 作用域内浏览器变量实际名    method 所属方法名
#   tools  所属分支的 方法名 == 字面量   schema MCP_Server.wsv 里注册的工具名(None = 不在分派分支内)
POINTS = [
    dict(line=230, indent=20,
         body='js属性值 = MCP命令服务器.CDP执行JS并等待 (js属性码, 10000, 真)',
         frag_lines=(230,), browser='browser', method='分类分派_填表操作',
         tools=('browser.fill_attr_get', 'browser_fill_attr_get'),
         schema='browser_fill_attr_get',
         role='fill_attr_get / attribute 非空(取 HTML 属性)的 CDP 优先路径'),
    dict(line=250, indent=20,
         body='js文本值 = MCP命令服务器.CDP执行JS并等待 (js文本码, 10000, 真)',
         frag_lines=(250,), browser='browser', method='分类分派_填表操作',
         tools=('browser.fill_attr_get', 'browser_fill_attr_get'),
         schema='browser_fill_attr_get',
         role='fill_attr_get / attribute 省略(取 textContent)的 CDP 优先路径'),
    dict(line=294, indent=12,
         body='js值 = MCP命令服务器.CDP执行JS并等待 (js码, 10000, 真)',
         frag_lines=(294, 662), browser='browser', method='分类分派_填表操作',
         tools=('browser.fill_get_text', 'browser_fill_get_text'),
         schema='browser_fill_get_text',
         role='fill_get_text 的 CDP 优先路径'),
    dict(line=334, indent=12,
         body='设值 = MCP命令服务器.CDP执行JS并等待 (设码, 10000, 真)',
         frag_lines=(334,), browser='browser2', method='分类分派_填表操作',
         tools=('browser.fill_set_text', 'browser_fill_set_text'),
         schema='browser_fill_set_text',
         role='fill_set_text 的写入(设 innerText)路径'),
    dict(line=347, indent=12,
         body='读值 = MCP命令服务器.CDP执行JS并等待 (读码, 10000, 真)',
         frag_lines=(347,), browser='browser2', method='分类分派_填表操作',
         tools=('browser.fill_set_text', 'browser_fill_set_text'),
         schema='browser_fill_set_text',
         role='fill_set_text 的写后回读验证路径'),
    dict(line=662, indent=8,
         body='js值 = MCP命令服务器.CDP执行JS并等待 (js码, 10000, 真)',
         frag_lines=(294, 662), browser=None, method='前置存在校验',
         tools=None, schema=None,
         role='辅助方法 前置存在校验 内的元素存在性探测(非分派分支)'),
]

BRANCH_RE = re.compile(r'\s*(?:否则|如果)\s*\(方法名 ==')
METHOD_RE = re.compile(r'\s*方法\s+(\S+)')
PARAM_RE = re.compile(r'\s*参数\s+(\S+)')
VAR_BROWSER_RE = re.compile(r'\s*变量\s+(\S+)\s*<类型 = 类_FBrowser_浏览器')


def fail(msg):
    print('[FAIL] ' + msg)
    sys.exit(1)


def read_wsv(path):
    """按字节读 .wsv: 拒绝 BOM, 逐行记录**原有行尾**, 行内容去掉行尾 CR。"""
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        fail('%s 带 UTF-8 BOM(预期无 BOM), 拒绝改写' % path)
    parts = raw.split(b'\n')
    lines, terms = [], []
    for i, p in enumerate(parts):
        last = (i == len(parts) - 1)
        if last:
            body, term = p, b''
        elif p.endswith(b'\r'):
            body, term = p[:-1], b'\r\n'
        else:
            body, term = p, b'\n'
        try:
            lines.append(body.decode('utf-8'))
        except UnicodeDecodeError as e:
            fail('%s 第 %d 行不是合法 UTF-8: %s' % (path, i + 1, e))
        terms.append(term)
    crlf = sum(1 for t in terms if t == b'\r\n')
    lf = sum(1 for t in terms if t == b'\n')
    bare = sum(1 for t in terms if t == b'')
    # 往返自检: 逐行(内容 + 原行尾)必须能拼回原始字节, 否则说明行尾建模有误
    if b''.join(l.encode('utf-8') + t for l, t in zip(lines, terms)) != raw:
        fail('%s 读写往返不一致(编码/行尾建模有误), 拒绝改写' % path)
    return dict(path=path, raw=raw, lines=lines, terms=terms,
                eol='CRLF=%d, LF=%d, 无行尾=%d' % (crlf, lf, bare))


def strip_code(line):
    """抹掉字符串字面量与 // 注释, 便于数括号。返回 (净化串, 是否未闭合字符串)。"""
    out, i, n, in_str = [], 0, len(line), False
    while i < n:
        c = line[i]
        if in_str:
            if c == '\\':
                out.append('  ')
                i += 2
                continue
            if c == '"':
                in_str = False
                out.append('"')
                i += 1
                continue
            out.append(' ')
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append('"')
            i += 1
            continue
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        out.append(c)
        i += 1
    return ''.join(out), in_str


def net_of(lines, op, cl):
    """全文件括号/花括号净额; 跳过 @ / # 引导行(嵌入行对火山解析器不透明)。"""
    tot = 0
    for ln in lines:
        s = ln.strip()
        if s[:1] in ('@', '#'):
            continue
        c, _ = strip_code(ln)
        tot += c.count(op) - c.count(cl)
    return tot


def split_args(s):
    """按字符串/注释之外的顶层逗号切分参数列表。"""
    parts, buf, depth, i, n, in_str = [], [], 0, 0, len(s), False
    while i < n:
        c = s[i]
        if in_str:
            buf.append(c)
            if c == '\\':
                buf.append(s[i + 1] if i + 1 < n else '')
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            buf.append(c)
            i += 1
            continue
        if c == '/' and i + 1 < n and s[i + 1] == '/':
            break
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(''.join(buf))
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    parts.append(''.join(buf))
    return [p.strip() for p in parts]


def schema_registration(server_lines, tool):
    """返回 (行idx, 该注册调用的完整文本)。注册调用跨行时按括号净额补全。"""
    needle = '添加工具JSON ("' + tool + '"'
    hits = [i for i, l in enumerate(server_lines) if needle in l]
    if not hits:
        fail('MCP_Server.wsv 找不到 `%s` 的注册行 -> 无法判定 frame_id, 拒绝改写' % needle)
    if len(hits) > 1:
        fail('`%s` 注册了 %d 次(期望 1): 行 %r' % (needle, len(hits), [i + 1 for i in hits]))
    i = hits[0]
    buf, bal, j = [], 0, i
    while j < len(server_lines):
        buf.append(server_lines[j])
        c, _ = strip_code(server_lines[j])
        bal += c.count('(') - c.count(')')
        if bal <= 0:
            break
        j += 1
        if j - i > 12:
            break
    return i, '\n'.join(buf)


def method_span(lines, idx):
    """返回包含第 idx 行的方法 (方法行idx, 方法名, 形参名列表)。"""
    midx = None
    for i in range(idx, -1, -1):
        if METHOD_RE.match(lines[i]):
            midx = i
            break
    if midx is None:
        fail('第 %d 行往上找不到 `方法` 声明' % (idx + 1))
    name = METHOD_RE.match(lines[midx]).group(1)
    params, k = [], midx + 1
    while k < len(lines) and lines[k].strip().startswith('参数'):
        m = PARAM_RE.match(lines[k])
        if m:
            params.append(m.group(1))
        k += 1
    return midx, name, params


def render_blob(form, out, force_lf):
    """把行列表拼回字节流: 逐行沿用**原有行尾**(或 --force-lf 全用 LF), 编码 UTF-8 无 BOM。"""
    terms = [b'\n' for _ in form['terms']] if force_lf else list(form['terms'])
    if form['terms'] and form['terms'][-1] == b'':
        terms[-1] = b''  # 原文件末行无行尾 -> 保持无行尾
    return b''.join(l.encode('utf-8') + t for l, t in zip(out, terms)), terms


def verify_minimal(raw, form, out, terms, edits, force_lf):
    """证明"新字节流把目标行还原成原文后 == 原始字节流": 即差异**恰好**是那几处片段替换。"""
    if force_lf:
        print('        行尾检查: --force-lf 模式, 全文件行尾规范化为 LF(其余字节不变由上面断言保证)')
        return
    back = list(out)
    for p, _nl, _fr, _nf in edits:
        back[p['line'] - 1] = form['lines'][p['line'] - 1]
    rejoined = b''.join(l.encode('utf-8') + t for l, t in zip(back, terms))
    if rejoined != raw:
        fail('把目标行还原成原文后未得到原始字节流 -> 改动不止目标行, 拒绝写盘')
    print('        行尾/字节检查: 逐行保留原行尾, 目标行还原后 == 原始字节流(改动被证明只限目标行)')


def self_test(form, out, edits, force_lf):
    """在 _audit/ 下写一份副本, 走**与 --apply 完全相同**的渲染/写盘/回读路径, 再删除副本。
    目的: 在不碰 src/ 的前提下验证 --apply 的字节级行为(本会话不许真跑 --apply 之外的写盘)。"""
    tmp = os.path.join(HERE, '_g1c_form_selftest_copy.wsv')
    blob, terms = render_blob(form, out, force_lf)
    verify_minimal(form['raw'], form, out, terms, edits, force_lf)
    with io.open(tmp, 'wb') as f:
        f.write(blob)
    try:
        got = open(tmp, 'rb').read()
        if got != blob:
            fail('[self-test] 副本写盘后字节不一致')
        again = read_wsv(tmp)
        if again['lines'] != out:
            fail('[self-test] 副本回读行内容不一致')
        if not force_lf:
            if again['terms'] != form['terms']:
                fail('[self-test] 副本行尾与原文件不同(逐行保留策略失效)')
            if got.count(b'\r\n') != form['raw'].count(b'\r\n'):
                fail('[self-test] 副本 CRLF 数量与原文件不同')
        else:
            if b'\r' in got:
                fail('[self-test] --force-lf 副本仍含 CR')
        # 幂等探针: 改写后的行必须能被"已应用"检测认出(否则重跑会误报原文不匹配)
        for p, _nl, _fr, _nf in edits:
            if (NEW_CALL + ' (' + p['browser'] + ', 参数JSON,') not in again['lines'][p['line'] - 1]:
                fail('[self-test] 改写后第 %d 行无法被幂等检测识别' % p['line'])
        print('[self-test] 副本 %s: 写盘 -> 回读 -> 行尾核对 全部通过 (行数 %d, 改动行 %r)'
              % (os.path.basename(tmp), len(again['lines']), [p['line'] for p, _, _, _ in edits]))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    argv = sys.argv[1:]
    apply = '--apply' in argv
    force_lf = '--force-lf' in argv
    selftest = '--self-test' in argv

    form = read_wsv(FORM)
    server = read_wsv(SERVER)
    lines = form['lines']

    print('== G1-c: MCP_Server_Form.wsv 的 CDP 优先求值 -> %s ==' % NEW_METHOD)
    print('目标 %s' % FORM)
    print('     行数 %d (UTF-8 无 BOM; 行尾统计 %s)' % (len(lines), form['eol']))
    if AUDIT_LINES is not None and len(lines) != AUDIT_LINES:
        print('[warn] 行数与审计快照(%d)不同 -> 行号可能已漂移; '
              '逐点"行号 + 原文"断言会先失败, 不会误改, 届时请重新审计' % AUDIT_LINES)
    print('模式 %s | 行尾策略 %s'
          % ('--apply(写盘)' if apply else 'dry-run(不写盘)',
             '--force-lf(整文件规范化为 LF)' if force_lf
             else '逐行保留原行尾(最小改动, 目标行字节级替换)'))
    if not force_lf and 'CRLF' in form['eol'] and 'CRLF=0' not in form['eol']:
        print('[warn] 该文件**不是纯 LF**(见上行行尾统计), 与任务书"源码为 LF"的假设不同。')
        print('       本脚本默认逐行保留原行尾 => 只有被改的那几行字节变化;')
        print('       若要让整文件变成 LF, 请显式加 --force-lf(会产生整文件行尾差异)。')

    # ---- 0) 核对主代理新增的框架感知入口: 存在 + 形参顺序 --------------------------------
    hops = [i for i, l in enumerate(server['lines'])
            if re.match(r'\s*方法\s+' + NEW_METHOD + r'\s*<', l)]
    if len(hops) != 1:
        fail('MCP_Server.wsv 里 `方法 %s` 命中 %d 次(期望 1): %r'
             % (NEW_METHOD, len(hops), [i + 1 for i in hops]))
    _, hname, hparams = method_span(server['lines'], hops[0])
    if hparams != NEW_PARAMS:
        fail('入口 %s 的形参是 %r, 期望 %r' % (NEW_METHOD, hparams, NEW_PARAMS))
    print('入口核对: MCP_Server.wsv:%d %s (%s) ok' % (hops[0] + 1, hname, ', '.join(hparams)))

    # ---- 1) 逐点定位 + 作用域/分支门禁 + Schema 门禁 -------------------------------------
    edits, report = [], []
    for p in POINTS:
        ln0 = p['line'] - 1
        if ln0 >= len(lines):
            fail('审计行号 %d 超出文件(%d 行)' % (p['line'], len(lines)))
        line = lines[ln0]
        frag = p['body'][p['body'].index('= ') + 2:]
        pre = ' ' * p['indent']

        # 0) 幂等: 该点已经是框架感知形式 -> 记 DONE 并跳过(不再要求旧原文, 否则重跑会误报)
        if p['browser'] and (NEW_CALL + ' (' + p['browser'] + ', 参数JSON,') in line:
            report.append((p, 'DONE',
                           '已是 `%s (%s, 参数JSON, …)` 形式, 无需再改' % (NEW_CALL, p['browser']),
                           line, None, p['browser'], p['method'], True))
            continue

        # 1a) 行号 + 原文精确匹配(缩进空格数 + 去缩进去尾原文逐字)
        if not line.startswith(pre + p['body']):
            near = [i + 1 for i, l in enumerate(lines) if l.strip().startswith(p['body'][:12])]
            fail('第 %d 行原文不匹配(文件被改动过 -> 拒绝猜测, 请重新审计)\n'
                 '        期望(缩进 %d 空格): %s\n        实际: %s\n        首12字相同的行: %r'
                 % (p['line'], p['indent'], p['body'], line, near))

        # 1b) 该行内调用片段恰好 1 次; 片段在全文件的命中行集合与审计快照一致
        if line.count(frag) != 1:
            fail('第 %d 行内调用片段出现 %d 次(期望 1): %s' % (p['line'], line.count(frag), frag))
        occ = tuple(i + 1 for i, l in enumerate(lines) if frag in l)
        if occ != tuple(p['frag_lines']):
            fail('片段 %s 的全文件命中行 %r != 审计快照 %r(文件结构已变, 请重新审计)'
                 % (frag, occ, tuple(p['frag_lines'])))

        # 1c) 所属方法 + 形参
        midx, mm, mparams = method_span(lines, ln0)
        if mm != p['method']:
            fail('第 %d 行所属方法 = %s, 审计 = %s' % (p['line'], mm, p['method']))
        has_pjson = '参数JSON' in mparams

        # 1d) 所属分支(仅分派分支内的点)
        bidx = None
        if p['tools']:
            for i in range(ln0, -1, -1):
                if BRANCH_RE.match(lines[i]):
                    bidx = i
                    break
            if bidx is None:
                fail('第 %d 行往上找不到 `方法名 ==` 分派分支' % p['line'])
            if bidx < midx:
                fail('第 %d 行: 找到的分支行(%d)在本方法之外' % (p['line'], bidx + 1))
            for t in p['tools']:
                if '"%s"' % t not in lines[bidx]:
                    fail('第 %d 行所属分支(%d)不含 %s:\n        %s'
                         % (p['line'], bidx + 1, t, lines[bidx].strip()))
            if not has_pjson:
                fail('第 %d 行: 方法 %s 的形参 %r 里没有 参数JSON, 无法生成框架感知调用'
                     % (p['line'], mm, mparams))

        # 1e) 浏览器变量: 作用域内实际名字必须与审计一致
        vname, vidx = None, None
        if p['browser']:
            lo = bidx if bidx is not None else midx
            for i in range(ln0, lo - 1, -1):
                m = VAR_BROWSER_RE.match(lines[i])
                if m:
                    vname, vidx = m.group(1), i
                    break
            if vname is None:
                fail('第 %d 行作用域内找不到 `变量 X <类型 = 类_FBrowser_浏览器>`' % p['line'])
            if vname != p['browser']:
                fail('第 %d 行浏览器变量: 审计=%s 实际=%s(声明于第 %d 行)'
                     % (p['line'], p['browser'], vname, vidx + 1))

        # 1f) Schema 门禁
        if p['schema'] is None:
            status = 'SKIP'
            reason = ('不在 `方法名 ==` 分派分支内(方法 %s 形参 %s: 无 browser / 参数JSON 作用域)'
                      % (mm, '/'.join(mparams) or '无'))
        else:
            sidx, stext = schema_registration(server['lines'], p['schema'])
            if '"frame_id"' in stext:
                status = 'PATCH'
                reason = 'Schema 含 frame_id (MCP_Server.wsv:%d)' % (sidx + 1)
            else:
                status = 'SKIP'
                reason = ('MCP_Server.wsv:%d 的 `添加工具JSON ("%s"...` 里没有 "frame_id" '
                          '-> 分支收了 frame_id 也无处可取, 按范围规则不改' % (sidx + 1, p['schema']))

        # 1g) 幂等(理论上已被第 0 步拦下, 这里兜底)
        if NEW_CALL + ' (' + str(p['browser']) + ', 参数JSON,' in line:
            status = 'DONE'
            reason = '已改写成 %s(...), 无需再改' % NEW_CALL

        new_line = None
        if status == 'PATCH':
            m = re.fullmatch(re.escape(OLD_CALL) + r' \((.*)\)', frag)
            if not m:
                fail('第 %d 行不是 `%s (…, …, 真)` 形式: %s' % (p['line'], OLD_CALL, frag))
            args = split_args(m.group(1))
            if len(args) != 3:
                fail('第 %d 行是 %d 参调用(只处理 3 参形式): %s' % (p['line'], len(args), frag))
            if args[2] != '真':
                fail('第 %d 行第 3 参不是 真(实际 %r), 语义不明, 拒绝改写' % (p['line'], args[2]))
            new_frag = '%s (%s, 参数JSON, %s, %s)' % (NEW_CALL, p['browser'], args[0], args[1])
            new_line = line.replace(frag, new_frag)
            if new_line == line or new_line.count(new_frag) != 1:
                fail('第 %d 行替换无效果/不唯一' % p['line'])
            if new_line.count(frag) != 0:
                fail('第 %d 行替换后仍残留旧调用' % p['line'])
            for tag, s in (('旧', line), ('新', new_line)):
                c, _ = strip_code(s)
                if c.count('(') != c.count(')'):
                    fail('第 %d 行 %s文本括号不平衡: %s' % (p['line'], tag, c.strip()))
            edits.append((p, new_line, frag, new_frag))

        report.append((p, status, reason, line, new_line, vname, mm, has_pjson))

    # ---- 2) 打印逐点结论 ----------------------------------------------------------------
    print('')
    for p, status, reason, old, new, vname, mm, has_pjson in report:
        tag = {'PATCH': '[PATCH]', 'SKIP': '[SKIP ]', 'DONE': '[DONE ]'}.get(status, '[?]')
        print('%s 行 %d | 工具 %-22s | browser=%s, 参数JSON=%s | 方法 %s'
              % (tag, p['line'], p['schema'] or '(非工具分支)',
                 vname or '(作用域内无)', '在方法形参里' if has_pjson else '(无)', mm))
        print('        作用: %s' % p['role'])
        print('        判定: %s' % reason)
        print('        旧: %s' % old.strip())
        print('        新: %s' % (new.strip() if new is not None else '(不改)'))
    print('')

    # ---- 3) 替换后整体断言 --------------------------------------------------------------
    out = list(lines)
    for p, new_line, _fr, _nf in edits:
        out[p['line'] - 1] = new_line
    if len(out) != len(lines):
        fail('行数变化: %d -> %d' % (len(lines), len(out)))
    diff = [i + 1 for i in range(len(lines)) if out[i] != lines[i]]
    expect = sorted(p['line'] for p, _, _, _ in edits)
    if diff != expect:
        fail('实际改动行 %r != 预期行 %r' % (diff, expect))
    nb_old, nb_new = net_of(lines, '{', '}'), net_of(out, '{', '}')
    np_old, np_new = net_of(lines, '(', ')'), net_of(out, '(', ')')
    if nb_old != nb_new:
        fail('全文件花括号净额变了: %d -> %d' % (nb_old, nb_new))
    if np_old != np_new:
        fail('全文件圆括号净额变了: %d -> %d' % (np_old, np_new))
    for p, new_line, _fr, _nf in edits:
        c, _ = strip_code(new_line)
        if c.count('(') != c.count(')') or c.count('{') != c.count('}'):
            fail('第 %d 行替换后括号/花括号不平衡' % p['line'])

    print('断言: 行数 %d 不变 | 改动行 %r == 预期 %r | 花括号净额 %d -> %d | 圆括号净额 %d -> %d'
          % (len(lines), diff, expect, nb_old, nb_new, np_old, np_new))
    print('门禁: PATCH %d | SKIP %d | DONE %d'
          % (sum(1 for r in report if r[1] == 'PATCH'),
             sum(1 for r in report if r[1] == 'SKIP'),
             sum(1 for r in report if r[1] == 'DONE')))

    # ---- 4) 写盘(或自检) ---------------------------------------------------------------
    if selftest:
        if not edits:
            print('[self-test] 无 PATCH 点, 无可自检内容')
            return
        self_test(form, out, edits, force_lf)
        return
    if not apply:
        print('[dry-run] 未写盘。加 --apply 才写回 %s' % FORM)
        return
    if not edits:
        print('[apply] 无 PATCH 点, 未写盘')
        return

    blob, terms = render_blob(form, out, force_lf)
    verify_minimal(form['raw'], form, out, terms, edits, force_lf)
    with io.open(FORM, 'wb') as f:
        f.write(blob)
    chk_raw = open(FORM, 'rb').read()
    if chk_raw.startswith(b'\xef\xbb\xbf'):
        fail('写盘后出现 UTF-8 BOM')
    if force_lf and b'\r' in chk_raw:
        fail('写盘后仍含 CR(--force-lf 未生效)')
    if chk_raw != blob or read_wsv(FORM)['lines'] != out:
        fail('写盘后内容与内存结果不一致')
    print('[apply] 已写入 %s (%d 行, UTF-8 无 BOM, 行尾 %s), 改动行 %r'
          % (FORM, len(out), 'LF(全文件规范化)' if force_lf else '逐行保留原文', diff))


main()
