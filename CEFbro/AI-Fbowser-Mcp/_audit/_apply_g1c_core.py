#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
_apply_g1c_core.py  ——  G1C 补丁: 让 MCP_Server_Core.wsv 里"CDP 优先"的 JS 求值点变成**框架感知**求值

背景
----
Schema 里带 frame_id 的 21 个 DOM/填表类工具中,凡是走"CDP 优先"分支的 JS 求值
(3 参数形式 `MCP命令服务器.CDP执行JS并等待 (JS码, 毫秒, 真)`)都**永远在主框架求值**,
于是"传了 frame_id 也读不到 iframe 内容"。

主代理已在 src/MCP_Server.wsv 新增框架感知入口(假定存在):
    MCP命令服务器.CDP执行JS按框架 (浏览器, 参数JSON, JS代码, 最大毫秒)
语义与 CDP执行JS并等待 完全一致; 无 frame_id / main / 主框架 时**逐字**回落到原行为。

本脚本做什么
------------
只改一个文件: src/MCP_Server_Core.wsv
把这 8 处 3 参数调用点改成 4 参数框架感知调用:
    第 480 行  browser_get_text        js取文值
    第 561 行  browser_get_text        全文JS      (selector 为空的全文路径)
    第 1809 行 browser_dom_query       js查询值
    第 1906 行 browser_dom_set_value   js置回读
    第 2002 行 browser_dom_rect        js坐标值
    第 2043 行 browser_dom_inner_html  js内码值
    第 2084 行 browser_dom_checked     js勾选值
    第 2129 行 browser_dom_selected    js选中值
(8 个调用点全部位于 `方法名 == "browser_..."` 分支内, 作用域里变量名就是 `browser`,
 形参名就是 `参数JSON` —— 脚本会逐点断言, 名不符立即报错退出, 绝不"尽量替换"。)

不做什么
--------
* 不碰 .wsv/.vprj/.vsln 以外的任何东西(本脚本自己除外) —— 只有本文件被写。
* 不碰已是 4 参数形式的调用点(如第 346 行的 browser_execute_js)。
* 不碰 reverse/逆向族、browser_execute_js、browser_evaluate、uri 解码兜底、scrape 异步续跑。
* 不做全局字符串替换: 每一处都用 **行号 + 整行原文精确匹配** 双重定位。

安全网(任一不满足即报错退出, 退出码 2, 不写盘)
------------------------------------------------
1. 文件必须是 UTF-8 **无 BOM**、**LF** 换行, 且以 LF 结尾。
2. 每一处: 该行号上的整行(含缩进)必须与硬编码原文逐字相等。
3. 每一处: 该原文在**整个文件里必须唯一**(出现次数 == 1; 去缩进后也必须唯一)。
4. 每一处: 调用必须是 3 参数, 且第 3 参数必须是 `真`。
5. 每一处: 替换后 ( 与 ) 在"字符串字面量之外"数量平衡(net == 0), 且替换前后 net 相同。
6. 替换后文件行数不变。
7. 替换前后文件整体 花括号净额(字符串之外、跳过以 @ 开头的嵌入式行)与 圆括号净额 均不变。
8. 补丁后 `CDP执行JS并等待` 的残留调用点必须**正好**是那 9 个排除点(行号集合精确相等)。

用法
----
    py -3 _audit/_apply_g1c_core.py            # dry-run: 只打印 行号/旧文本/新文本
    py -3 _audit/_apply_g1c_core.py --apply    # 真正落盘(UTF-8 无 BOM, LF)
"""

import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(REPO, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(REPO, 'src', 'MCP_Server.wsv')

CALL_OLD = 'MCP命令服务器.CDP执行JS并等待'
CALL_NEW = 'MCP命令服务器.CDP执行JS按框架'
BROWSER_ARG = 'browser'
PARAMJSON_ARG = '参数JSON'

# ---------------------------------------------------------------- 命中点定义
# 每处: 行号 / 缩进空格数 / 所属工具(方法名分支) / 整行原文(不含缩进)
SITES = [
    dict(lineno=480, indent=20, tool='browser_get_text',
         code="js取文值 = MCP命令服务器.CDP执行JS并等待 (js取文码, 10000, 真)"),
    dict(lineno=561, indent=20, tool='browser_get_text',
         code="全文JS = MCP命令服务器.CDP执行JS并等待 (\"(function(){var b=document.body;if(!b)return '__MCP_NO_BODY__';return '__MCP_TEXT__'+String(b.innerText||b.textContent||'')})()\", 10000, 真)"),
    dict(lineno=1809, indent=20, tool='browser_dom_query',
         code="js查询值 = MCP命令服务器.CDP执行JS并等待 (js查询码, 10000, 真)"),
    dict(lineno=1906, indent=16, tool='browser_dom_set_value',
         code="js置回读 = MCP命令服务器.CDP执行JS并等待 (js置值, 10000, 真)"),
    dict(lineno=2002, indent=20, tool='browser_dom_rect',
         code="js坐标值 = MCP命令服务器.CDP执行JS并等待 (js坐标, 10000, 真)"),
    dict(lineno=2043, indent=20, tool='browser_dom_inner_html',
         code="js内码值 = MCP命令服务器.CDP执行JS并等待 (js内码, 10000, 真)"),
    dict(lineno=2084, indent=20, tool='browser_dom_checked',
         code="js勾选值 = MCP命令服务器.CDP执行JS并等待 (js勾选, 10000, 真)"),
    dict(lineno=2129, indent=20, tool='browser_dom_selected',
         code="js选中值 = MCP命令服务器.CDP执行JS并等待 (js选中, 10000, 真)"),
]

# 明确排除、补丁后必须原样留存的调用点(行号 -> 原因)
EXCLUDED = [
    (346, 'browser_execute_js 分支, 已是 4 参数形式(自己显式传框架上下文) —— 不在本次范围'),
    (374, 'browser_evaluate 分支, Schema 无 frame_id —— 不在本次范围'),
    (4473, 'mcp.result/mcp_result 异步续跑分支(browser_scrape phase 2, 变量是 sBrowser) —— 属 scrape, 不在范围'),
    (5718, 'browser_uri_decode 的 decodeURIComponent 兜底 —— 不在范围'),
    (7419, 'browser_reverse_strings(反逆向族) —— 不在范围'),
    (7648, 'browser_reverse_search(反逆向族) —— 不在范围'),
    (7694, 'browser_reverse_extract(反逆向族) —— 不在范围'),
    (7734, 'browser_reverse_extract(反逆向族) —— 不在范围'),
    (7754, 'browser_reverse_extract(反逆向族) —— 不在范围'),
]

# 21 个工具里不属于本文件的那些(只作提示, 本脚本不动它们)
OTHER_FILE_NOTE = (
    'browser_fill_set_value / fill_click / fill_focus / fill_scroll / fill_exists / '
    'fill_attr_get / fill_attr_set / fill_trigger / fill_select / browser_fill_form '
    '这 10 个分支不在 MCP_Server_Core.wsv, 而在 src/MCP_Server_Form.wsv '
    '(CDP 调用点: 230 / 250 / 294 / 334 / 347 / 662) —— 本脚本按范围只处理 Core。'
)


class Fail(Exception):
    pass


def die(msg):
    raise Fail(msg)


# ---------------------------------------------------------------- 词法小工具
def split_args(s):
    """按顶层逗号切分参数; 双引号字符串内的逗号/括号不计(火山字符串 = 双引号, 反斜杠转义)。"""
    args, cur = [], []
    in_str = False
    depth = 0
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if in_str:
            cur.append(c)
            if c == '\\' and i + 1 < n:
                cur.append(s[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            cur.append(c)
            i += 1
            continue
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        if c == ',' and depth == 0:
            args.append(''.join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    if in_str:
        die('字符串未闭合: ' + s)
    args.append(''.join(cur))
    return args


def scan_nets(text):
    """返回 (paren_net, brace_net, embedded_skipped_lines, unterminated_string)

    只统计字符串字面量之外的括号; 同时跳过:
      * 以 @ 开头的嵌入式行
      * 以 \\\\ 开头的注释行
      * // 行注释
    """
    paren = brace = 0
    embedded = 0
    in_str = False
    at_line_start = True
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\' and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '\n':
            at_line_start = True
            i += 1
            continue
        if at_line_start:
            if c in ' \t':
                i += 1
                continue
            if c == '@' or (c == '\\' and text[i:i + 2] == '\\\\'):
                embedded += 1
                k = text.find('\n', i)
                i = n if k < 0 else k
                continue
            at_line_start = False
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            k = text.find('\n', i)
            i = n if k < 0 else k
            continue
        if c == '(':
            paren += 1
        elif c == ')':
            paren -= 1
        elif c == '{':
            brace += 1
        elif c == '}':
            brace -= 1
        i += 1
    return paren, brace, embedded, in_str


def line_nets(line):
    """单行的 (圆括号净额, 花括号净额), 字符串字面量之外; // 注释忽略。"""
    p = b = 0
    in_str = False
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if in_str:
            if c == '\\' and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        if c == '(':
            p += 1
        elif c == ')':
            p -= 1
        elif c == '{':
            b += 1
        elif c == '}':
            b -= 1
        i += 1
    return p, b, in_str


def call_sites(lines):
    """返回 {lineno: (arg_count_or_None, third_arg)} —— 所有 CDP执行JS并等待 调用点。"""
    out = {}
    for idx, line in enumerate(lines, start=1):
        if CALL_OLD not in line:
            continue
        rest = line[line.find(CALL_OLD) + len(CALL_OLD):]
        m = re.match(r'^ \((.*)\)\s*$', rest)
        if not m:
            out[idx] = (None, line.strip())
            continue
        args = split_args(m.group(1))
        out[idx] = (len(args), args[2].strip() if len(args) >= 3 else '')
    return out


# ---------------------------------------------------------------- 主流程
def main(argv):
    apply = '--apply' in argv
    for a in argv[1:]:
        if a not in ('--apply', '--verbose', '-v'):
            die('未知参数: %s (可用: --apply / --verbose)' % a)

    if not os.path.isfile(TARGET):
        die('找不到目标文件: ' + TARGET)

    with open(TARGET, 'rb') as f:
        raw = f.read()

    if raw.startswith(b'\xef\xbb\xbf'):
        die('目标文件带 UTF-8 BOM —— 本补丁要求无 BOM, 拒绝写回')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        die('目标文件不是合法 UTF-8: %s' % e)
    if b'\r' in raw:
        die('目标文件含 CR(不是纯 LF 换行) —— 与项目约定不符, 拒绝写回')
    if not text.endswith('\n'):
        die('目标文件不是以 LF 结尾, 拒绝写回')

    lines = text.split('\n')
    if lines[-1] != '':
        die('内部错误: split 结果异常')

    print('=== G1C 框架感知求值补丁 ===')
    print('模式      : %s' % ('APPLY (会写盘)' if apply else 'DRY-RUN (不写盘; 加 --apply 才落盘)'))
    print('目标文件  : %s' % TARGET)
    print('编码/换行 : UTF-8 无 BOM / LF')
    print('文件行数  : %d (split 元素 %d, 末尾空元素为收尾 LF)' % (len(lines) - 1, len(lines)))
    print()

    # 0) 目标方法是否已存在(只提示, 不致命 —— 主代理可能正在改)
    if os.path.isfile(SERVER):
        with open(SERVER, 'rb') as f:
            srv = f.read().decode('utf-8', 'replace')
        if '方法 CDP执行JS按框架' in srv:
            print('[前置检查] src/MCP_Server.wsv 已存在 `方法 CDP执行JS按框架`  ->  OK')
        else:
            print('[前置检查][警告] src/MCP_Server.wsv 里**没找到** `方法 CDP执行JS按框架`;')
            print('                    补丁仍按约定生成, 但落盘后必须由主代理确认该方法存在, 否则编译不过。')
    else:
        print('[前置检查][警告] 找不到 src/MCP_Server.wsv, 跳过前置检查')
    print()

    before_sites = call_sites(lines)
    before_raw_net = scan_nets(text)
    before_lines = list(lines)

    print('--- 改动前 CDP执行JS并等待 调用点共 %d 处(本文件) ---' % len(before_sites))
    for ln in sorted(before_sites):
        cnt, third = before_sites[ln]
        mark = '本次命中' if ln in [s['lineno'] for s in SITES] else '排除'
        print('  第 %5d 行 | %-4s | 参数个数=%s | 第3参数=%s' % (ln, mark, cnt, third))
    print()

    # 1) 逐点双重定位 + 生成新行
    print('--- 逐点定位与替换 ---')
    new_lines = list(lines)
    pending, done = [], []
    changed = 0
    for k, site in enumerate(SITES, start=1):
        ln = site['lineno']
        idx = ln - 1
        expected = ' ' * site['indent'] + site['code']
        actual = lines[idx]

        n_exact = sum(1 for l in lines if l == expected)
        n_stripped = sum(1 for l in lines if l.strip() == site['code'])

        lhs = site['code'].split(' = ', 1)[0]
        already = (CALL_NEW in actual) and actual.lstrip().startswith(lhs + ' = ' + CALL_NEW)

        if actual == expected:
            if n_exact != 1:
                die('第 %d 行原文在文件中出现 %d 次(要求恰好 1 次), 拒绝替换' % (ln, n_exact))
            if n_stripped != 1:
                die('第 %d 行去缩进原文在文件中出现 %d 次(要求恰好 1 次), 拒绝替换' % (ln, n_stripped))
            rest = actual[actual.find(CALL_OLD) + len(CALL_OLD):]
            m = re.match(r'^ \((.*)\)$', rest)
            if not m:
                die('第 %d 行调用形态不符合 `...( ... )` 结尾: %s' % (ln, actual.strip()))
            args = split_args(m.group(1))
            if len(args) != 3:
                die('第 %d 行不是 3 参数形式(实际 %d 个), 拒绝替换' % (ln, len(args)))
            if args[2].strip() != '真':
                die('第 %d 行第 3 参数不是 真(实际 %s), 拒绝替换' % (ln, args[2].strip()))
            prefix = actual[:actual.find(CALL_OLD)]
            if 'browser' not in prefix and BROWSER_ARG not in actual:
                pass  # 变量名断言在下面统一做
            new_line = (prefix + CALL_NEW + ' (' + BROWSER_ARG + ', ' + PARAMJSON_ARG + ', '
                        + args[0].strip() + ', ' + args[1].strip() + ')')

            # 行级括号平衡断言(字符串之外)
            op, ob, ou = line_nets(actual)
            np_, nb, nu = line_nets(new_line)
            if ou or nu:
                die('第 %d 行存在未闭合的字符串字面量, 拒绝替换' % ln)
            if op != 0 or np_ != 0:
                die('第 %d 行圆括号不平衡(字符串外): 旧=%d 新=%d' % (ln, op, np_))
            if op != np_ or ob != nb:
                die('第 %d 行括号净额发生变化: 圆 %d->%d 花 %d->%d' % (ln, op, np_, ob, nb))
            if new_line in lines:
                die('第 %d 行替换后的文本与文件中已有的另一行完全相同, 拒绝替换' % ln)

            new_lines[idx] = new_line
            changed += 1
            state = 'PENDING'
            print()
            print('[%d/%d] 第 %d 行 | 工具=%s | 变量 browser=%s, 参数JSON=%s | 状态=%s'
                  % (k, len(SITES), ln, site['tool'], BROWSER_ARG, PARAMJSON_ARG, state))
            print('   OLD: %s' % actual)
            print('   NEW: %s' % new_line)
            print('   参数解析: JS码=%s | 超时=%s | 第3参数=真 ; 行括号净额 旧%d->新%d'
                  % (args[0].strip(), args[1].strip(), op, np_))
            pending.append(ln)
        elif already:
            done.append(ln)
            print()
            print('[%d/%d] 第 %d 行 | 工具=%s | 状态=ALREADY_APPLIED(已是框架感知调用, 跳过)'
                  % (k, len(SITES), ln, site['tool']))
            print('   NOW: %s' % actual)
        else:
            die('第 %d 行既不是预期原文、也不是已替换形态, 拒绝继续。\n  期望: %s\n  实际: %s'
                % (ln, expected, actual))

    # 2) 行数不变
    if len(new_lines) != len(before_lines):
        die('替换后行数变化: %d -> %d' % (len(before_lines), len(new_lines)))
    print()
    print('行数断言: split 元素 %d -> %d  OK(不变)' % (len(before_lines), len(new_lines)))

    # 3) 全文件括号/花括号净额不变
    after_text = '\n'.join(new_lines)
    after_raw_net = scan_nets(after_text)
    print('全文件净额(字符串外, 跳过 @ 嵌入式行 %d 行): 圆括号 %d -> %d | 花括号 %d -> %d'
          % (before_raw_net[2], before_raw_net[0], after_raw_net[0],
             before_raw_net[1], after_raw_net[1]))
    if before_raw_net[1] != after_raw_net[1]:
        die('花括号净额发生变化(%d -> %d), 拒绝替换' % (before_raw_net[1], after_raw_net[1]))
    if before_raw_net[0] != after_raw_net[0]:
        die('圆括号净额发生变化(%d -> %d), 拒绝替换' % (before_raw_net[0], after_raw_net[0]))
    if before_raw_net[3] or after_raw_net[3]:
        die('全文件扫描发现字符串字面量未闭合, 拒绝替换')
    if before_raw_net[1] != 0:
        print('[警告] 全文件花括号净额基准不是 0(%d) —— 语法层面可能本就有问题, 请人工确认' % before_raw_net[1])

    # 4) 残留调用点必须正好是那 9 个排除点
    after_sites = call_sites(new_lines)
    expect_remaining = sorted(ln for ln, _ in EXCLUDED)
    got_remaining = sorted(after_sites)
    print()
    print('--- 改动后 CDP执行JS并等待 残留调用点(应只剩排除项) ---')
    for ln in got_remaining:
        cnt, third = after_sites[ln]
        reason = dict(EXCLUDED).get(ln, '!! 未预期的残留 !!')
        print('  第 %5d 行 | 参数个数=%s | %s' % (ln, cnt, reason))
    if got_remaining != expect_remaining:
        die('残留调用点行号集合与预期不符\n  期望: %s\n  实际: %s' % (expect_remaining, got_remaining))
    print('残留集合断言: 恰好 %d 处, 与排除清单逐行一致  OK' % len(got_remaining))

    print()
    print('--- 说明(不在本脚本范围) ---')
    print('  ' + OTHER_FILE_NOTE)

    # 5) 落盘
    print()
    if not apply:
        print('DRY-RUN 结束: 未写盘。将改 %d 处, 已应用 %d 处。' % (changed, len(done)))
        print('确认无误后执行: py -3 _audit/_apply_g1c_core.py --apply')
        return 0

    if changed == 0:
        print('无需改动(全部 %d 处已是目标形态), 未写盘。' % len(done))
        return 0

    with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
        f.write(after_text)

    with open(TARGET, 'rb') as f:
        back = f.read()
    if back.startswith(b'\xef\xbb\xbf') or b'\r' in back:
        die('写盘后校验失败(BOM 或 CR 出现) —— 请立即用备份恢复')
    if back.decode('utf-8') != after_text:
        die('写盘后回读不一致 —— 请立即用备份恢复')

    print('APPLY 完成: 已写盘 %d 处; 回读校验(UTF-8 无 BOM / LF / 内容一致) OK' % changed)
    print('下一步(由主代理执行): 编译验证 -> 运行时验证 frame_id 生效。')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except Fail as e:
        sys.stderr.write('\n[补丁中止] %s\n' % e)
        sys.stderr.write('未写盘(或写入前已中止)。\n')
        sys.exit(2)
