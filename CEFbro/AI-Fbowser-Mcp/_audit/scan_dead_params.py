# -*- coding: utf-8 -*-
"""系统性扫描: 工具 schema 里声明、但在**整个 src 中除 schema 行外再无任何引用**的参数。

为什么用"全 src 无引用"而不是"分支体内无引用":
  第一版按分支体判, 结果 29 个候选里绝大多数是假阳性 ——
  (1) 分支体提取用朴素花括号计数, 遇到 JS 里带 { } 的字符串会**提前截断**;
  (2) 参数也可能在**被调用的辅助方法**里读取(如 browser_cdp 的 params 由 执行CDP命令 读取)。
改为"全 src 无引用": 只要参数名在别处(任何文件、任何方法)以字面量出现过, 就不报。
这样留下的都是**真正没有任何代码去读**的声明 —— 编译器管不到, 只能靠这种交叉核对发现。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

# 中央统一处理 / 协议层必需, 分支内不读也正常
COMMON = {'browser_id', 'max_ms', 'sync_wait', 'async_only', 'wait_for_load',
          'timeout_ms', 'confirm', 'compact', 'consume', 'frame_id'}

files = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith('.wsv') and '~vbak' not in fn:
        files[fn] = io.open(os.path.join(SRC, fn), encoding='utf-8').read()
server = files['MCP_Server.wsv']

PROP_RE = re.compile(r'属性项JSON \("([a-zA-Z0-9_]+)"')
SINGLE_RE = re.compile(r'单参数Schema文本 \("([a-zA-Z0-9_]+)"')

decl = {}          # 参数名 -> [工具名...]
schema_lines = []  # 只属于 schema 的行(用于扣掉声明自身)
for line in server.split('\n'):
    m = re.match(r'\s*添加工具JSON \("([a-z0-9_.]+)",', line)
    if not m:
        continue
    name = m.group(1)
    schema_lines.append(line)
    for p in set(PROP_RE.findall(line)) | set(SINGLE_RE.findall(line)):
        decl.setdefault(p, []).append(name)

# 把 schema 行从"全 src 文本"里剔除, 再看参数名还剩多少引用
joined = '\n'.join(files.values())
for line in schema_lines:
    joined = joined.replace(line, '', 1)

dead = []
for p, tools in sorted(decl.items()):
    if p in COMMON:
        continue
    n = joined.count('"%s"' % p)
    if n == 0:
        dead.append((p, tools))

print('声明过的参数名 %d 个; 全 src 扣除 schema 行后**零引用**的: %d 个' % (len(decl), len(dead)))
print('\n== 候选: 声明了但整个 src 没有任何代码读取它 ==')
for p, tools in dead:
    print('   %-24s 声明于 %d 个工具: %s' % (p, len(tools), ', '.join(tools[:6])))
