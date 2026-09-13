# -*- coding: utf-8 -*-
"""删除剩余 2 个零引用方法(用**已验证的花括号配对**定位收尾 `}`, 每步断言配平)。

候选:
  · `检查欢迎页导航超时` —— 欢迎页导航三件套的最后一件(另两件上一轮已删), 零引用
  · `构建网络日志数据JSON` —— 只被已删的 `分派网络日志命令` 调用; 活路径(Core)自己拼 JSON
保留(非死代码): `main.wsv 启动方法`(框架入口) 与 `缓存线程类_线程运行`(<接收事件> 绑定)。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import vlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '删除剩余死方法-写入前')

TARGETS = [
    ("MCP_Server.wsv", "检查欢迎页导航超时", "CheckWelcomePageNavigateTimeout"),
    ("MCP_Server.wsv", "构建网络日志数据JSON", "BuildNetworkLogDataJSON"),
]


def count_braces(lines):
    o = c = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        o += body.count('{')
        c += body.count('}')
    return o, c


def find_close(lines, start):
    j = start
    while j < len(lines) and '{' not in re.sub(r'"[^"]*"', '""', lines[j]):
        j += 1
    depth = 0
    while j < len(lines):
        body = re.sub(r'"[^"]*"', '""', lines[j]).split('//')[0]
        depth += body.count('{') - body.count('}')
        if depth == 0:
            return j
        j += 1
    return None


texts = {}
for f in vlib.FILES:
    p = os.path.join(SRC, f)
    texts[f] = open(p, 'rb').read().decode('utf-8').split('\n') if os.path.exists(p) else []

all_lines = [(f, i + 1, ln) for f, ls in texts.items() for i, ln in enumerate(ls)]
problems = []
plan = {}
for fn, mname, sym in TARGETS:
    occ = [(f, i) for f, i, ln in all_lines if mname in ln]
    sym_occ = [(f, i) for f, i, ln in all_lines if sym in ln]
    if len(occ) != 1 or len(sym_occ) != 1:
        problems.append('%s: 中文 %d 次 / 英文 %d 次(各应 1)' % (mname, len(occ), len(sym_occ)))
        continue
    ls = texts[fn]
    i0 = next(i for i, ln in enumerate(ls) if re.match(r'\s*方法\s+' + re.escape(mname) + r'\s', ln))
    head = "\n".join(ls[max(0, i0 - 8):i0])
    if ('<接收事件' in head) or ('@虚拟方法' in head):
        problems.append('%s: 有框架绑定标注' % mname)
        continue
    top = i0
    while top - 1 >= 0 and ls[top - 1].strip().startswith('#'):
        top -= 1
    bot = find_close(ls, i0)
    if bot is None or ls[bot].strip() != '}':
        problems.append('%s: 收尾大括号定位失败' % mname)
        continue
    so, sc = count_braces(ls[top:bot + 1])
    if so != sc:
        problems.append('%s: 段落不配平 {%d }%d' % (mname, so, sc))
        continue
    plan.setdefault(fn, []).append((top, bot, mname, bot - top + 1, so, sc))

if problems:
    print('!! 前置校验未过, 未写文件:')
    for p in problems:
        print('   - %s' % p)
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
for fn, items in plan.items():
    ls = texts[fn]
    before = count_braces(ls)
    rem_o = sum(x[4] for x in items)
    rem_c = sum(x[5] for x in items)
    for top, bot, mname, n, so, sc in sorted(items, key=lambda x: -x[0]):
        print('   %s: 删除 %s (%d 行, 原 %d..%d)' % (fn, mname, n, top + 1, bot + 1))
        del ls[top:bot + 1]
        while top < len(ls) and top - 1 >= 0 and ls[top].strip() == '' and ls[top - 1].strip() == '':
            del ls[top]
    after = count_braces(ls)
    want = (before[0] - rem_o, before[1] - rem_c)
    if after != want:
        print('!! %s 花括号不符: 实得 %s, 期望 %s -> 回滚(不写文件)' % (fn, after, want))
        sys.exit(1)
    dst = os.path.join(BAK, fn)
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(SRC, fn), dst)
    open(os.path.join(SRC, fn), 'wb').write("\n".join(ls).encode('utf-8'))
    print('   写入 %s, 花括号 %s -> %s (删 {%d }%d, 配平)' % (fn, before, after, rem_o, rem_c))
