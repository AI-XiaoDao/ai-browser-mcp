# -*- coding: utf-8 -*-
"""删除 8 个**已证实零引用**的死方法(证据见 _audit/prove_zero_ref.py + prove_zero_ref_symbols.py)。

删除前置校验(任一不满足即中止, 不写文件):
  ① 方法名在 16 个项目源文件里除定义外 0 次出现;
  ② 其 @输出名 英文符号同样 0 次出现(内嵌 C++ 是按英文符号调的);
  ③ 方法定义前 8 行内没有 <接收事件> / @虚拟方法 = 可覆盖(框架按符号绑定);
  ④ 记下方法体行范围, 连同紧邻其上的 `#` 文档注释一起删, 保留一个空行分隔。
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
BAK = os.path.join(ROOT, '备份', '删除死方法-写入前')

# (文件, 方法名, @输出名)
TARGETS = [
    ("MCP_Server.wsv", "尝试恢复欢迎页导航", "TryRestoreWelcomePageNavigate"),
    ("MCP_Server.wsv", "尝试导航欢迎页", "TryNavigateWelcomePage"),
    ("MCP_Server.wsv", "CDP获取脚本源", "CDPGetScriptSource"),
    ("MCP_Server.wsv", "分派网络日志命令", "DispatchNetworkLogCommand"),
    ("MCP_Server.wsv", "解析匹配模式", "ParseMatchMode"),
    ("MCP_Server.wsv", "记录网络日志项", "RecordNetworkLogItem"),
    ("MCP_Server.wsv", "规范化URL", "NormalizeURL"),
    ("MCP_Server.wsv", "发送CORS500响应", "SendCORS500Response"),
]

lines = {}
for f in vlib.FILES:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        lines[f] = open(p, 'rb').read().decode('utf-8').split('\n')
    else:
        lines[f] = []

# ── 前置校验 ──
problems = []
plan = {}   # file -> [(del_from_idx, del_to_idx, method, chinese_occurrences)]
for fn, mname, sym in TARGETS:
    if fn not in lines or not lines[fn]:
        problems.append('%s: 文件不可读' % fn)
        continue
    occ = [(f, i + 1) for f, ls in lines.items() for i, ln in enumerate(ls) if mname in ln]
    sym_occ = [(f, i + 1) for f, ls in lines.items() for i, ln in enumerate(ls) if sym in ln]
    if len(occ) != 1:
        problems.append('%s: 中文名出现 %d 次(应只定义处)' % (mname, len(occ)))
    if len(sym_occ) != 1:
        problems.append('%s: 英文符号出现 %d 次(应只定义处) %s' % (mname, len(sym_occ), sym_occ[:3]))
    ms = [m for m in vlib.find_methods(fn) if m[1] == mname]
    if len(ms) != 1:
        problems.append('%s: find_methods 命中 %d 个' % (mname, len(ms)))
        continue
    i0, _n, sig, b0, b1 = ms[0]
    head = "\n".join(lines[fn][max(0, i0 - 8):i0])
    if ('<接收事件' in head) or ('@虚拟方法' in head):
        problems.append('%s: 有框架绑定标注, 不可删' % mname)
        continue
    # 向上吸收紧邻的 `#` 文档注释行
    top = i0
    while top - 1 >= 0 and lines[fn][top - 1].strip().startswith('#'):
        top -= 1
    # 向下: extract_block 的 b1 是 '}' 所在行 idx
    bot = b1
    plan.setdefault(fn, []).append((top, bot, mname, sig[:80]))

if problems:
    print('!! 前置校验未通过, 未写任何文件:')
    for p in problems:
        print('   - %s' % p)
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
for fn, items in plan.items():
    ls = lines[fn]
    total = 0
    # 从后往前删, 避免行号漂移
    for top, bot, mname, sig in sorted(items, key=lambda x: -x[0]):
        n = bot - top + 1
        print('   %s: 删除 %s (%d 行, 原 %d..%d) %s' % (fn, mname, n, top + 1, bot + 1, sig))
        del ls[top:bot + 1]
        # 清理连续空行(最多留 1 个)
        while top < len(ls) and top - 1 >= 0 and ls[top].strip() == '' and ls[top - 1].strip() == '':
            del ls[top]
        total += n
    p = os.path.join(SRC, fn)
    dst = os.path.join(BAK, fn)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    open(p, 'wb').write("\n".join(ls).encode('utf-8'))
    print('   写入 %s (共删 %d 行)' % (fn, total))
print('前置校验通过, 已删除并备份到 备份/删除死方法-写入前/')
