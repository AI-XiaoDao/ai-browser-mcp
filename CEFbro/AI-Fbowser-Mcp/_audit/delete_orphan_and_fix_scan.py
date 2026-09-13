# -*- coding: utf-8 -*-
"""① 删除级联孤儿 `统计网络日志条数`(唯一调用者是刚删掉的 `构建网络日志数据JSON`);
② 让卫生扫描认识两种"零引用但绝不该删"的框架绑定: `<接收事件>` 事件接收方法 与 应用入口 `启动方法`。
   当前扫描只排除 `@虚拟方法`, 于是 `缓存线程类_线程运行`/`启动方法` 一直被当成待确认项。
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
BAK = os.path.join(ROOT, '备份', '删除级联孤儿-写入前')
FN = 'MCP_Server.wsv'
MNAME = '统计网络日志条数'
SYM = 'CountNetworkLogCount'


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


texts = {f: open(os.path.join(SRC, f), 'rb').read().decode('utf-8').split('\n')
         for f in vlib.FILES if os.path.exists(os.path.join(SRC, f))}
all_lines = [(f, i + 1, ln) for f, ls in texts.items() for i, ln in enumerate(ls)]
occ = [(f, i) for f, i, ln in all_lines if MNAME in ln]
sym_occ = [(f, i) for f, i, ln in all_lines if SYM in ln]
print('零引用核对: 中文 %s, 英文 %s' % (occ, sym_occ))
if len(occ) != 1 or len(sym_occ) != 1:
    print('!! 引用计数不为 1, 中止')
    sys.exit(1)

ls = texts[FN]
i0 = next(i for i, ln in enumerate(ls) if re.match(r'\s*方法\s+' + MNAME + r'\s', ln))
top = i0
while top - 1 >= 0 and ls[top - 1].strip().startswith('#'):
    top -= 1
bot = find_close(ls, i0)
so, sc = count_braces(ls[top:bot + 1])
if bot is None or ls[bot].strip() != '}' or so != sc:
    print('!! 定位/配平检查失败 bot=%s {%d }%d' % (bot, so, sc))
    sys.exit(1)
before = count_braces(ls)
del ls[top:bot + 1]
while top < len(ls) and top - 1 >= 0 and ls[top].strip() == '' and ls[top - 1].strip() == '':
    del ls[top]
after = count_braces(ls)
if after != (before[0] - so, before[1] - sc):
    print('!! 花括号不符, 不写文件: %s -> %s' % (before, after))
    sys.exit(1)
os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, FN)
if not os.path.exists(dst):
    shutil.copy2(os.path.join(SRC, FN), dst)
open(os.path.join(SRC, FN), 'wb').write("\n".join(ls).encode('utf-8'))
print('已删除 %s (原 %d..%d, %d 行); 花括号 %s -> %s' % (MNAME, top + 1, bot + 1, bot - top + 1, before, after))

# ── ② 修扫描器的排除口径 ──
P = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
src = open(P, 'rb').read().decode('utf-8')
OLD = '''            if "@虚拟方法" in sig:
                virt_m += 1
                continue
'''
NEW = '''            # 框架按符号绑定、源码必然零引用的两类, 不能当死代码:
            #   · `@虚拟方法 = 可覆盖` 覆盖 C++ 基类虚函数
            #   · `<接收事件>` 事件接收方法(属性块常跨行, 必须连签名区一起看)
            #   · 应用入口 `启动方法`(由框架调用)
            head = "\\n".join(files[f][i0:b0]) if b0 else sig
            if ("@虚拟方法" in head) or ("<接收事件" in head) or (mname == "启动方法"):
                virt_m += 1
                continue
'''
if src.count(OLD) != 1:
    print('!! 扫描器锚点命中 %d 次, 未改' % src.count(OLD))
    sys.exit(1)
open(P, 'wb').write(src.replace(OLD, NEW, 1).encode('utf-8'))
print('扫描器排除口径已更新(<接收事件> / 启动方法)')
