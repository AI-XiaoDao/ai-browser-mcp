# -*- coding: utf-8 -*-
r"""查 `@输出名` / 变量名冲突: 类编译不出来且**编译器不指向该文件**时, 重复符号是首要嫌疑。

做法: 取出 391-398 那 8 个新成员的**中文名**与**@输出名**, 在全部 16 个源文件里统计出现次数。
任何 >1 的 (除声明行外还有别处) 都要单独看 —— 尤其"英文输出名与既有成员相同"这种冲突,
上一版脚本只数了"新名字出现几次", 数不出"与旧成员撞名"。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
FILES = ["main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
         "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
         "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
         "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
         "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv"]

ls = open(os.path.join(SRC, 'MCP_Server.wsv'), 'rb').read().decode('utf-8').split('\n')
newlines = [ln for ln in ls if ln.lstrip().startswith('变量 启动开关_') or ln.lstrip().startswith('变量 命令行开关')]
print('新成员 %d 个:' % len(newlines))
targets = []
for ln in newlines:
    m = re.match(r'\s*变量\s+(\S+)', ln)
    o = re.search(r'@输出名\s*=\s*"([^"]+)"', ln)
    targets.append((m.group(1), o.group(1) if o else None))
    print('   %-22s 输出名=%s' % (m.group(1), o.group(1) if o else '(无)'))

texts = {}
for f in FILES:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        texts[f] = open(p, 'rb').read().decode('utf-8')

print('\n== 冲突检查(出现次数 > 1 即为可疑) ==')
bad = 0
for cn, en in targets:
    cn_hits = [(f, t.count(cn)) for f, t in texts.items() if t.count(cn)]
    print('   %-22s 中文名: %s' % (cn, cn_hits))
    if en:
        en_hits = [(f, t.count(en)) for f, t in texts.items() if t.count(en)]
        flag = ''
        total = sum(c for _, c in en_hits)
        if total > 1:
            flag = '  ★英文输出名出现 %d 次 -> 可能与既有成员撞名!' % total
            bad += 1
        print('   %-22s 输出名: %s%s' % ('', en_hits, flag))

print('\n可疑项 %d 个' % bad)
