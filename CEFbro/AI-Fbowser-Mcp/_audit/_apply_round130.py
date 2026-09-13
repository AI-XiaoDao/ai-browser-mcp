# -*- coding: utf-8 -*-
r"""第130轮: ①实现 `browser_get_text.max_chars`(声明了却从不读 = 误导);
             ②`browser_debugger_set_breakpoint` 补声明 CDP 原生别名 `line_number`/`column_number`;
             ③`workflow_run` 补声明 `file`、修正错误的 required、把**源码核实的** steps 字段表写进描述;
             ④修 `_audit/_show_branch_params.py` 的分支匹配(遇空行/花括号换行会切错, 已在 Reverse.wsv 上暴露)。

依据(本轮用 `_audit/_show_branch_params.py --diff` 实测, 非照抄审计):
  · `browser_get_text` 分支读 frame_id/selector; schema 声明 max_chars → **声明未读**(实测);
    截断处写死 `MCP_常量.截断_源码默认字节`(Core:629);
  · `browser_debugger_set_breakpoint` 分支读 column/column_number/line/line_number/url → schema 缺 line_number/column_number;
  · `workflow_run` 分支读 name/file/definition/steps/on_error; steps 内字段(源码核实):
     skip / delay_ms / tool|name / args|arguments / wait_async / max_ms / on_error。

用法: py -3 _audit\_apply_round130.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
TOOL = os.path.join(ROOT, '_audit', '_show_branch_params.py')

# ① browser_get_text 真的按 max_chars 截断
GT_OLD = '''                        变量 全文上限 <类型 = 整数>
                        全文上限 = MCP_常量.截断_源码默认字节'''
GT_NEW = '''                        变量 全文上限 <类型 = 整数>
                        // max_chars 必须真的生效: 此前 schema 声明了它但实现写死常量(声明未读 = 误导调用方)。
                        全文上限 = MCP命令服务器.yyjson取整数 (参数JSON, "max_chars")
                        如果 (全文上限 <= 0 || 全文上限 > MCP_常量.截断_源码最大字节)
                        {
                            全文上限 = MCP_常量.截断_源码默认字节
                        }'''

# ② set_breakpoint 补 CDP 原生别名
BP_OLD = '属性项JSON ("column", "integer", "列号(0起算,可选)"), "\\"url\\""))'
BP_NEW = ('属性项JSON ("column", "integer", "列号(0起算,可选)") + "," + '
          '属性项JSON ("line_number", "integer", "CDP 原生别名, 等价于 line(实现会读它, 便于直接照抄 CDP 文档)") + "," + '
          '属性项JSON ("column_number", "integer", "CDP 原生别名, 等价于 column"), "\\"url\\""))')

# ③ workflow_run: file + required 修正 + steps 字段表
WF_OLD = ('属性项JSON ("steps", "text", "内联步骤JSON数组") + "," + 属性项JSON ("on_error", "text", "stop|continue"), "\\"name\\""))')
WF_NEW = ('属性项JSON ("steps", "array", "内联步骤(JSON 数组, 或形如 [...] 的 JSON 字符串)。每步字段(源码核实): '
          'tool|name(要调用的工具) / args|arguments(该工具的参数字典) / skip(true=跳过) / delay_ms(执行前延时) / '
          'wait_async(true=等异步结果) / max_ms(等待上限) / on_error(stop|continue)") + "," + '
          '属性项JSON ("file", "text", "工作流文件名(与 name 等价, 二者任给其一)") + "," + '
          '属性项JSON ("on_error", "text", "全局 on_error: stop|continue"), ""))')

WF_DESC_OLD = '"执行工作流(同步)"'
WF_DESC_NEW = ('"执行工作流(同步) | 入口四选一: name(工作流文件) / file(同义) / definition(完整 JSON 定义) / '
               'steps(内联步骤数组) | **steps 每步字段**(源码核实): tool|name, args|arguments, skip, delay_ms, '
               'wait_async, max_ms, on_error | 示例: {steps:[{tool:\\"browser_execute_js\\", args:{code:\\"1+1\\"}}, {tool:\\"browser_get_url\\"}]}"')

# ④ 测量件: 分支匹配要跳过空行/等第一个 `{`
TB_OLD = '''    for i, l in enumerate(lines):
        if ('方法名 == "%s"' % tool) in l:
            depth = 0
            for j in range(i, len(lines)):
                depth += lines[j].count('{') - lines[j].count('}')
                if j > i and depth <= 0:
                    return '\\n'.join(lines[i:j + 1]), i + 1, j + 1
    return None, 0, 0'''
TB_NEW = '''    for i, l in enumerate(lines):
        if ('方法名 == "%s"' % tool) in l:
            # 必须先等到第一个 `{` 再开始配平: 有些分支的 `{` 在下一行(甚至隔空行, 见 MCP_Server_Reverse.wsv),
            # 否则 depth 会在还没进块时就已经是 0, 直接切成 2 行(实测踩到)。
            depth = 0
            started = False
            for j in range(i, len(lines)):
                depth += lines[j].count('{') - lines[j].count('}')
                if not started:
                    if '{' in lines[j]:
                        started = True
                    continue
                if depth <= 0:
                    return '\\n'.join(lines[i:j + 1]), i + 1, j + 1
    return None, 0, 0'''


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


def edit_line(text, tool, edits, tag):
    """在**给定文本**上改某个工具注册行(不重新读盘, 便于连续处理多个工具)。"""
    lines = text.split('\n')
    idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
    assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
    i = idx[0]
    for sub, old, new in edits:
        if new in lines[i]:
            print('   · %s / %s (已存在)' % (tag, sub))
            continue
        assert lines[i].count(old) == 1, '%s / %s 锚点 %d' % (tool, sub, lines[i].count(old))
        lines[i] = lines[i].replace(old, new, 1)
        print('   · %s / %s' % (tag, sub))
    return '\n'.join(lines)


def main():
    # Core
    ctxt = io.open(CORE, encoding='utf-8').read()
    has_cr = '\r' in ctxt
    b0 = balance(ctxt)
    assert ctxt.count(GT_OLD) == 1, 'get_text 截断锚点 %d' % ctxt.count(GT_OLD)
    c_out = ctxt.replace(GT_OLD, GT_NEW, 1)
    assert balance(c_out) == b0
    print('MCP_Server_Core.wsv: browser_get_text 现在真的按 max_chars 截断')
    # Server(在同一份文本上顺序改两个工具, 避免"后一次读盘覆盖前一次改动")
    stxt = io.open(SERVER, encoding='utf-8').read()
    sb0 = balance(stxt)
    s_out = edit_line(stxt, 'browser_debugger_set_breakpoint', [('别名', BP_OLD, BP_NEW)], 'set_breakpoint')
    s_out = edit_line(s_out, 'workflow_run',
                      [('file+steps 字段表+required', WF_OLD, WF_NEW), ('描述', WF_DESC_OLD, WF_DESC_NEW)],
                      'workflow_run')
    assert balance(s_out) == sb0, 'Server 括号净值变了'
    s_lines = s_out.split('\n')
    i_bp = [i for i, ln in enumerate(s_lines) if '添加工具JSON ("browser_debugger_set_breakpoint"' in ln][0]
    i_wf = [i for i, ln in enumerate(s_lines) if '添加工具JSON ("workflow_run"' in ln][0]
    assert 'line_number' in s_lines[i_bp], 'set_breakpoint 别名未写入'
    assert '"file"' in s_lines[i_wf] and '\\"\\"' not in s_lines[i_wf][-40:], 'workflow_run 未按预期更新'
    # Tooling
    ttxt = io.open(TOOL, encoding='utf-8').read()
    assert ttxt.count(TB_OLD) == 1, '测量件锚点 %d' % ttxt.count(TB_OLD)
    t_out = ttxt.replace(TB_OLD, TB_NEW, 1)
    print('_show_branch_params.py: 分支匹配已修(先等第一个 { )')
    if '--apply' in sys.argv:
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        io.open(TOOL, 'w', encoding='utf-8', newline='\n').write(t_out)
        c = io.open(CORE, encoding='utf-8').read()
        s = io.open(SERVER, encoding='utf-8').read()
        assert 'yyjson取整数 (参数JSON, "max_chars")' in c and ('\r' in c) == has_cr
        assert '"line_number"' in s and '"file"' in s and '\r' not in s
        print('已写入 Core + Server + 测量件 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
