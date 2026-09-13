# -*- coding: utf-8 -*-
r"""静态扫描: **已在 tools/list 里显示、但实现上只会失败**的工具(dead-end 检查)。

背景(用户要求): "确保所有显示的 MCP 能力都可以稳定正常执行功能"。
只修被点名的几个不够 —— 必须**系统性地**找出"显示出来却永远做不到事"的工具。

判据(保守, 只报高置信):
  在某个 `分类分派_*` 里找到 `方法名 == "工具名"` 分支, 取该分支的完整代码块(花括号配对, 跳过 @/注释行),
  若**第一条可执行语句**就是 `返回 (MCP_响应构建.命令失败 (...))`, 且它之前**没有任何 `如果`/循环**,
  则这个工具对任何参数都只会失败(dead-end)。

输出: `_audit/_deadend_scan.md`(含每个工具的第一条失败文案, 便于人工分诊"能不能修" vs "本机不支持")

用法: py -3 _audit\scan_deadends.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
OUT = os.path.join(ROOT, '_audit', '_deadend_scan.md')
FILES = ['MCP_Server.wsv', 'MCP_Server_Core.wsv', 'MCP_Server_Reverse.wsv', 'MCP_Server_VIP.wsv',
         'MCP_Server_System.wsv', 'MCP_Server_HTTP.wsv', 'MCP_Server_Form.wsv', 'MCP_Server_Kernel.wsv',
         'MCP_Kernel.wsv']
REFUSAL = ('禁用', '不实现', '不开放', '不支持', '无法', '需要重启', '必须重启', '未实现', '刻意')


def load(path):
    return io.open(path, encoding='utf-8', newline='').read().split('\n')


def advertised_tools():
    """从 添加工具JSON 注册行取工具名(= tools/list 里显示的那批)。"""
    names = []
    for fn in FILES:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            continue
        for ln in load(p):
            m = re.match(r'\s*添加工具JSON \("([a-zA-Z0-9_.]+)"', ln)
            if m:
                names.append(m.group(1))
    return sorted(set(names))


def branch_block(lines, idx):
    """idx = `方法名 == "X"` 所在行; 返回该分支的代码行(不含外层 if 行本身)。"""
    # 找到该分支的起始 '{'
    i = idx
    while i < len(lines) and '{' not in lines[i]:
        if '方法名 ==' in lines[i] and i > idx:
            return None      # 掉进了下一个分支, 说明本分支是单行形式
        i += 1
    if i >= len(lines):
        return None
    depth = 0
    body = []
    j = i
    while j < len(lines):
        ln = lines[j]
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            j += 1
            continue
        # 粗略: 只数花括号(字符串内的花括号在分支头/返回里极少见)
        instr = False
        for ch in ln:
            if ch == '"':
                instr = not instr
            elif not instr:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
        if j > i:
            body.append(ln)
        if depth <= 0 and j >= i:
            break
        j += 1
    return body


def first_statement(body):
    for ln in body:
        s = ln.strip()
        if s == '' or s.startswith('//') or s.startswith('#'):
            continue
        return s
    return ''


def main():
    tools = advertised_tools()
    hits = []
    for fn in FILES:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            continue
        lines = load(p)
        for i, ln in enumerate(lines):
            m = re.search(r'方法名 == "([a-zA-Z0-9_.]+)"', ln)
            if not m:
                continue
            name = m.group(1)
            if name not in tools:
                continue
            body = branch_block(lines, i)
            if body is None:
                continue
            first = first_statement(body)
            if not first.startswith('返回 (MCP_响应构建.命令失败'):
                continue
            # 第一条语句就是无条件失败 ⇒ dead-end(要求: 分支体里除注释外只有这一条返回)
            hits.append((fn, i + 1, name, ' '.join(body).strip()[:260]))
    seen = {}
    for fn, ln, name, msg in hits:
        seen.setdefault(name, (fn, ln, msg))
    md = ['# 已显示但"只会失败"的工具扫描（dead-end）', '',
          '> 由 `_audit/scan_deadends.py` 生成（静态扫描；判据见脚本头注释）', '',
          '工具总数(tools/list 注册) **%d**，命中 **%d**。' % (len(tools), len(seen)), '']
    if seen:
        md += ['| 工具 | 位置 | 第一条失败文案（截断） |', '|---|---|---|']
        for name, (fn, ln, msg) in sorted(seen.items()):
            md.append('| `%s` | %s:%d | %s |' % (name, fn, ln, msg.replace('|', '\\|')))
    else:
        md.append('**无命中**：没有任何已显示工具的实现是"无条件失败"。')
    txt = '\n'.join(md) + '\n'
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(txt)
    print('工具 %d 个, dead-end 命中 %d 个' % (len(tools), len(seen)))
    for name, (fn, ln, msg) in sorted(seen.items()):
        print('  [%s] %-28s %s' % ('DEAD' if any(k in msg for k in REFUSAL) else 'ERR ', name, msg[:110]))
    print('明细已写 _audit/_deadend_scan.md')


if __name__ == '__main__':
    main()
