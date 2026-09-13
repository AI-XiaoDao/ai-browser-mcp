# -*- coding: utf-8 -*-
r"""清掉最后 8 条: 7 条 `vX.Y: …` 版本标签引子(约束保留) + 1 条 `上一轮` 的歧义词。

原则同前: **只去掉过程引子, 正文(约束)一字不动**。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
problems = []

SPECIFIC = [
    ('MCP_Server.wsv', '// 清除同 task_id 旧结果,避免同步等待误读上一轮 CDP 缓存',
     '// 清除同 task_id 旧结果, 避免同步等待误读到旧的 CDP 缓存结果'),
]
for fn, old, new in SPECIFIC:
    p = os.path.join(SRC, fn)
    t = open(p, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in t else '\n'
    if t.count(old.replace('\n', nl)) != 1:
        problems.append('%s: 命中 %d' % (fn, t.count(old.replace('\n', nl))))
        continue
    open(p, 'wb').write(t.replace(old.replace('\n', nl), new.replace('\n', nl), 1).encode('utf-8'))
    print('   ok %s 歧义词已改' % fn)

# 版本标签引子: `// v2.4: xxx` -> `// xxx`; 仅处理行首引子, 且只对**活文件**(排除 *.~vbak.wsv)
PAT = re.compile(r'^(\s*//\s*)v\d+\.\d+(?:\.\d+)?\s*(?:[A-Za-z]{1,4}\d?)?\s*[:：]\s*')
LIVE = ["main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
        "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
        "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
        "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
        "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv"]
total = 0
for fn in LIVE:
    p = os.path.join(SRC, fn)
    if not os.path.exists(p):
        continue
    t = open(p, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in t else '\n'
    lines = t.split('\n')
    hit = 0
    for i, ln in enumerate(lines):
        m = PAT.match(ln)
        if m:
            lines[i] = m.group(1) + ln[m.end():]
            hit += 1
    if hit:
        open(p, 'wb').write(nl.join(lines).encode('utf-8'))
        print('   %-24s 去版本引子 %d 处' % (fn, hit))
        total += hit
print('去版本引子合计 %d 处' % total)

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
