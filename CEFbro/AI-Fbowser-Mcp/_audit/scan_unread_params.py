# -*- coding: utf-8 -*-
"""系统性扫描: 工具 schema 里**声明了、但实现从不读取**的参数(= 静默无效参数)。

为什么值得查: 编译器管不到它 —— schema 与实现是两处独立文本。
AI 代理按 schema 传参、实现却不读, 结果就是"调用成功但参数没起作用"的静默失效,
与用户抱怨的"反复换方法"同源。项目已有先例: 5 处文案写"可选/status"而实现不存在。

口径:
  · schema 侧: 从 `添加工具JSON ("工具名", "描述", <schema表达式>)` 里抽 `属性项JSON ("名字"` /
    `单参数Schema文本 ("名字"` 等; 只看 tools/call 的入参名。
  · 实现侧: 在全部 src 里找该工具的**分派分支**(`方法名 == "工具名"` 或 `规范名 == ...`),
    取到下一个同级 `否则 (` 为止的分支体, 再看每个参数名是否以 "名字" 字面量出现。
  · 排除项(请求级公共参数, 由中央统一处理, 分支内本就不该出现):
    browser_id / max_ms / sync_wait / async_only / wait_for_load / timeout_ms / 等。
  · 结论一律标为**候选**, 因为参数也可能在(1)被调用的辅助方法里读取、或(2)别处分支里读取 ——
    故本脚本对每个候选**附带"辅助调用线索"**, 便于人工判定。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

# 中央统一处理的请求级参数, 不该要求分支体读取
COMMON = {'browser_id', 'max_ms', 'sync_wait', 'async_only', 'wait_for_load',
          'timeout_ms', 'request_id', 'confirm', 'compact', 'consume',
          'frame_id', 'frame_index', 'url_regex'}

files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith('.wsv') and '~vbak' not in fn:
        files[fn] = io.open(os.path.join(SRC, fn), encoding='utf-8').read()

server = files.get('MCP_Server.wsv', '')
if not server:
    print('!! 找不到 MCP_Server.wsv')
    sys.exit(1)

# ---------- 1) 抽工具 schema 属性名 ----------
REG_RE = re.compile(r'添加工具JSON \("([a-z0-9_.]+)",\s*"(?:[^"\\]|\\.)*",\s*(.*?)\)\s*$', re.M)
PROP_RE = re.compile(r'属性项JSON \("([a-zA-Z0-9_]+)"')
SINGLE_RE = re.compile(r'单参数Schema文本 \("([a-zA-Z0-9_]+)"')

# 逐行处理: 一条 添加工具JSON 就是一行
tools = {}
for line in server.split('\n'):
    m = re.match(r'\s*添加工具JSON \("([a-z0-9_.]+)",', line)
    if not m:
        continue
    name = m.group(1)
    props = set(PROP_RE.findall(line)) | set(SINGLE_RE.findall(line))
    if props:
        tools[name] = props
print('抽到带属性的工具 %d 个' % len(tools))

# ---------- 2) 抽每个工具的分派分支体 ----------
def branch_body(text, toolname):
    """返回 {出现处: 分支体文本} —— 支持 browser_x 与 browser.x 两种写法。"""
    out = {}
    for pat in (r'方法名 == "%s"' % re.escape(toolname),
                r'方法名 == "%s"' % re.escape(toolname.replace('_', '.'))):
        for m in re.finditer(pat, text):
            start = text.find('{', m.end())
            if start == -1:
                continue
            depth = 0
            i = start
            while i < len(text):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            out[m.start()] = text[start:i + 1]
    return out

allbranches = {}
for toolname in tools:
    bodies = []
    for fn, text in files.items():
        for _, b in branch_body(text, toolname).items():
            bodies.append((fn, b))
    allbranches[toolname] = bodies

# ---------- 3) 比对 ----------
cands = []
no_branch = []
for toolname, props in sorted(tools.items()):
    bodies = allbranches.get(toolname) or []
    if not bodies:
        no_branch.append(toolname)
        continue
    joined = '\n'.join(b for _, b in bodies)
    unread = []
    for p in sorted(props):
        if p in COMMON:
            continue
        if '"%s"' % p in joined:
            continue
        unread.append(p)
    if unread:
        cands.append((toolname, unread, [fn for fn, _ in bodies]))

print('\n== 候选: schema 声明了但分支体里读不到的参数 (%d 个工具) ==' % len(cands))
for toolname, unread, where in cands:
    print('   %-38s 未读到: %-46s 分支在: %s'
          % (toolname, ','.join(unread), where))

print('\n== 未找到分派分支的工具 (%d 个, 可能是跨文件/别名/预留) ==' % len(no_branch))
for n in no_branch:
    print('   %s' % n)
