# -*- coding: utf-8 -*-
r"""收尾: ① 把**真正残留的过程叙述**改写成约束(逐条精确替换, 正文保留);
        ② 把 `误判|假成功` 移出 STRONG —— 它们在本项目里是**领域术语**
           (`不静默假成功` 是项目自己的横切不变量名, `误判` 用于描述运行期判据), 不是开发过程叙述。

判据: 剩余清单里 20/27 是"误判/假成功"的约束句(如 `避免误判正常JSON返回值`、`会被误判为已加载完成`),
      只有 5 条真的带过程口吻(第N轮/上一版/现改为/本轮)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
problems = []

# ① 真正的过程叙述 -> 约束(整行锚点, 含缩进, 命中数必须为 1)
EDITS = [
    ('MCP_Server.wsv',
     '// 走 browser_cdp 只回一句"CDP已提交:Runtime.evaluate"(第98轮台账把它记成 pass, 实为假通过)。',
     '// 走 browser_cdp 只回一句"CDP已提交:Runtime.evaluate" —— 那种回执下的 pass 属假通过, 不可作为数据来源。'),
    ('MCP_Server.wsv',
     '// 第100轮: 这些工具**本来就要把数据交回调用方**(取HTML/选中项/链接/源码/页面结构/Cookie),',
     '// 这些工具**本来就要把数据交回调用方**(取HTML/选中项/链接/源码/页面结构/Cookie),'),
    ('MCP_Server_Core.wsv',
     '// 现改为: 长度上限 + 不含空白/双引号/花括号, 因此两种格式都能通过。',
     '// 约束: 只接受长度上限内且不含空白/双引号/花括号的取值, 因此两种书写格式都能通过。'),
    ('MCP_Server_Core.wsv',
     '// ★ 修(第二轮): 上一版把 forEach 回调换成普通 for 循环时引入了经典 var 捕获 bug ——',
     '// ★ 陷阱: 把 forEach 回调换成普通 for 循环会引入经典 var 捕获 bug ——'),
    ('MCP_Server_VIP.wsv',
     '//     属本工具既有歧义, 本轮未改变; 文档形式请用字符串 "true"/"1"。',
     '//     属本工具既有歧义(行为未改变); 文档形式请用字符串 "true"/"1"。'),
]
for fn, old, new in EDITS:
    p = os.path.join(SRC, fn)
    text = open(p, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != 1:
        problems.append('%s: 命中 %d 次: %s' % (fn, c, old[:60]))
        continue
    open(p, 'wb').write(text.replace(o, new.replace('\n', nl), 1).encode('utf-8'))
    print('   ok %s 叙述->约束' % fn)

# ② 口径: 移出领域术语
P = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
src = open(P, 'rb').read().decode('utf-8')
OLD = 'r"现改为|改回|纠正|笔误|漏了|误判|假成功")'
NEW = ('r"现改为|改回|纠正|笔误|漏了")\n'
       '# 说明: `误判`/`假成功` 曾列在 STRONG, 但实测它们在本项目里是**领域术语** ——\n'
       '#   · `不静默假成功` 是项目自己的横切不变量名;\n'
       '#   · `误判` 用于描述运行期判据(如"会被误判为已加载完成"), 属约束而非过程叙述。\n'
       '# 故移出; 若将来出现"我误判过…"这类过程句, 由人工复核处理。')
if src.count(OLD) != 1:
    problems.append('扫描器锚点命中 %d 次' % src.count(OLD))
else:
    open(P, 'wb').write(src.replace(OLD, NEW, 1).encode('utf-8'))
    print('   ok 扫描口径: 移出 误判/假成功(领域术语)')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
