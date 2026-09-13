# -*- coding: utf-8 -*-
r"""打印某个工具**分派分支**内真正读取的参数名(花括号配平切段 + 正则抽取)。

用途: 修 schema 前先确认实现到底读哪些参数(不照抄审计结论)。
用法: py -3 _audit\_show_branch_params.py browser_fingerprint browser_execute_js [...]
      py -3 _audit\_show_branch_params.py --diff browser_collect   # 额外打印与 schema 声明的差集
"""
import io
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['MCP_Server_Core.wsv', 'MCP_Server_Form.wsv', 'MCP_Server_System.wsv',
         'MCP_Server_VIP.wsv', 'MCP_Server_Reverse.wsv', 'MCP_Kernel.wsv']
# 闭包分析用: 这些文件里的"方法"可能被分支委托调用并代为读取参数(共享助手)
CLOSURE_FILES = FILES + ['MCP_Server.wsv', 'MCP_Server_Workflow.wsv', 'MCP_Callbacks.wsv',
                         'MCP_Server_HTTP.wsv', 'MCP_Server_Utils.wsv']
READER = re.compile(r'(yyjson取文本|yyjson取整数|yyjson取长整数|yyjson取小数|yyjson取逻辑|yyjson取逻辑_默认|参数键存在|yyjson取JSON文本|yyjson取对象成员|yyjson取对象成员_安全) \(参数JSON, "([A-Za-z_0-9]+)"')
# 第二种读取风格: **对象方法式**（`参数JSON.取文本 ("lat")`）。
# 少了这条会把"对象式读取"的参数误判成"死参数"；但**接收者必须限定为参数对象本身**，
# 否则会把"从事件/响应对象里取字段"(如 `事件数据.取文本 ("webdriver")`) 误算成参数读取(第一版踩到)。
READER2 = re.compile(r'\b(参数JSON|参数|参数对象|params|paramJSON|JSON参数)\.(取文本|取整数|取逻辑|取对象|取数组|取路径文本|取路径整数|取路径逻辑|取路径数组) \(([^)]*)"([A-Za-z_0-9]+)"')
TYPE_HINT2 = {'取整数': 'integer', '取文本': 'string', '取逻辑': 'boolean', '取对象': 'object',
              '取数组': 'array', '取路径整数': 'integer', '取路径文本': 'string',
              '取路径逻辑': 'boolean', '取路径数组': 'array'}


def scan_readers(seg):
    """返回 {参数名: {类型提示}}，合并两种读取风格。"""
    pairs = {}
    for rd, nm in READER.findall(seg):
        pairs.setdefault(nm, set()).add(TYPE_HINT.get(rd, rd))
    for _recv, rd, _args, nm in READER2.findall(seg):
        pairs.setdefault(nm, set()).add(TYPE_HINT2.get(rd, rd))
    return pairs
# 以 参数JSON 为实参的委托调用, 例如 `MCP命令服务器.执行Debugger断点流程JSON (命令ID, 参数JSON)` / `分派_反应器 (命令ID, 参数JSON)`
CALL = re.compile(r'([A-Za-z_\u4e00-\u9fa5][A-Za-z_0-9\u4e00-\u9fa5]*) \(([^()]*\u53C2\u6570JSON[^()]*)\)')
METHOD_DEF = re.compile(r'^\s*方法 ([A-Za-z_0-9\u4e00-\u9fa5]+) ')
TYPE_HINT = {'yyjson取整数': 'integer', 'yyjson取长整数': 'integer', 'yyjson取小数': 'number',
             'yyjson取文本': 'string', 'yyjson取逻辑': 'boolean',
             'yyjson取逻辑_默认': 'boolean', '参数键存在': 'any', 'yyjson取JSON文本': 'json-text',
             'yyjson取对象成员': 'object', 'yyjson取对象成员_安全': 'object'}


def _brace_delta(line):
    """只统计**字符串字面量与注释之外**的 `{`/`}` 差值。

    为什么必须这样: 火山分支体里常内嵌 JS(如 `"(function(){...})()"`), 直接 `line.count('{')` 会把
    字符串里的花括号算进去 —— 实测 `browser_debugger_script_source` 因此被"吞掉"后面几十个分支的参数
    (报出 60 多条假的 MISSING), 是**测量件自身的缺陷**, 不是产品缺陷。
    """
    delta = 0
    instr = False
    i = 0
    s = line
    if s.strip().startswith('@'):
        return 0
    while i < len(s):
        c = s[i]
        if c == '"':
            instr = not instr
        elif not instr:
            if s.startswith('//', i):
                break
            if c == '{':
                delta += 1
            elif c == '}':
                delta -= 1
        i += 1
    return delta


def branch(text, tool):
    lines = text.split('\n')
    for i, l in enumerate(lines):
        if ('方法名 == "%s"' % tool) in l:
            # 必须先等到第一个 `{` 再开始配平: 有些分支的 `{` 在下一行(甚至隔空行, 见 MCP_Server_Reverse.wsv),
            # 否则 depth 会在还没进块时就已经是 0, 直接切成 2 行(实测踩到)。
            depth = 0
            started = False
            for j in range(i, len(lines)):
                depth += _brace_delta(lines[j])
                if not started:
                    if _brace_delta(lines[j]) > 0:
                        started = True
                    continue
                if depth <= 0:
                    return '\n'.join(lines[i:j + 1]), i + 1, j + 1
    return None, 0, 0


def build_method_index():
    """建"方法名 → 方法体"索引(用于闭包分析: 分支把 参数JSON 委托给共享助手时, 参数其实是被助手读的)。"""
    idx = {}
    for fn in CLOSURE_FILES:
        path = os.path.join(ROOT, 'src', fn)
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding='utf-8').read().split('\n')
        for i, ln in enumerate(lines):
            m = METHOD_DEF.match(ln)
            if not m:
                continue
            name = m.group(1)
            depth, started = 0, False
            for j in range(i, len(lines)):
                depth += _brace_delta(lines[j])
                if not started:
                    if _brace_delta(lines[j]) > 0:
                        started = True
                    continue
                if depth <= 0:
                    if name not in idx:
                        idx[name] = '\n'.join(lines[i:j + 1])
                    break
    return idx


def closure_params(seg, idx, depth=3, seen=None):
    """递归收集: 分支委托出去的助手方法里读到的参数名(深度上限 depth, 防环)。"""
    seen = seen or set()
    found = set()
    if depth <= 0:
        return found
    for cname, _args in CALL.findall(seg):
        if cname in seen or cname not in idx:
            continue
        seen.add(cname)
        body = idx[cname]
        found |= set(scan_readers(body))
        found |= closure_params(body, idx, depth - 1, seen)
    return found


def main():
    argv = sys.argv[1:]
    args = [a for a in argv if not a.startswith('--')]
    want_diff = '--diff' in argv or '--brief' in argv
    brief = '--brief' in argv
    # --prefix X: 从 tools/list 展开所有该前缀的工具(便于整族扫一遍)
    prefixes = [argv[i + 1] for i, a in enumerate(argv) if a == '--prefix' and i + 1 < len(argv)]
    tools = {}
    if want_diff:
        try:
            tl = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/tools/list", timeout=20).read().decode())
            tools = {t["name"]: t for t in tl.get("tools", [])}
        except Exception as ex:
            print('!! 取 tools/list 失败: %r' % ex)
    if prefixes:
        args = [n for n in sorted(tools) if any(n.startswith(p) for p in prefixes)]
    elif brief and not args:
        # 不给任何工具名时: 全量扫(tools/list 里的全部工具) —— 这就是"系统性"那一遍
        args = sorted(tools)
    # 闭包分析(可选): 分支把 参数JSON 委托给共享助手时, 那些参数其实是被助手读的 ⇒ 不该算 EXTRA
    use_closure = '--closure' in argv
    midx = build_method_index() if use_closure else {}
    # 源文件缓存(整族扫描时别反复读盘)
    cache = {}
    n_diff = 0
    n_dead = 0
    for tool in args:
        found = False
        for fn in FILES:
            if fn not in cache:
                cache[fn] = io.open(os.path.join(ROOT, 'src', fn), encoding='utf-8').read()
            txt = cache[fn]
            seg, a, b = branch(txt, tool)
            if seg:
                found = True
                pairs = scan_readers(seg)
                by_helper = set()
                if use_closure:
                    by_helper = closure_params(seg, midx) - set(pairs)
                params = sorted(pairs)
                props = sorted(((tools.get(tool, {}).get('inputSchema') or {}).get('properties') or {}).keys())
                miss = [p for p in params if p not in props]
                extra = [p for p in props if p not in params and p not in by_helper]
                delegated = [p for p in props if p not in params and p in by_helper]
                if miss or extra:
                    n_diff += 1
                if extra:
                    n_dead += 1
                if brief:
                    if miss or extra:
                        print('%-44s MISSING=%-40s EXTRA(疑死)=%-40s 由助手读取=%s'
                              % (tool, miss or '-', extra or '-', delegated or '-'))
                    break
                print('== %s   (%s: %d-%d, 共 %d 行)' % (tool, fn, a, b, b - a + 1))
                print('   实现读的参数(类型提示):')
                for p in params:
                    print('       %-20s %s' % (p, '/'.join(sorted(pairs[p]))))
                if want_diff:
                    print('   schema 声明   : %s' % (props or '(无 schema)'))
                    print('   未声明(MISSING): %s' % (miss or '无'))
                    print('   声明未读(多余) : %s' % (extra or '无'))
                    if use_closure:
                        print('   其中由共享助手读取(非死参数): %s' % (delegated or '无'))
                break
        if not found and not brief:
            print('== %s: 未找到分派分支(可能在别的文件或走前缀路由)' % tool)
    if brief:
        print('-- 扫描 %d 个工具: 有差异 %d 个, 其中"疑死参数"工具 %d 个 (闭包分析=%s) --'
              % (len(args), n_diff, n_dead, '开' if use_closure else '关'))


main()
