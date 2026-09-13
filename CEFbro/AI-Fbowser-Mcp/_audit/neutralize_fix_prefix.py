# -*- coding: utf-8 -*-
r"""把"修复…"这类**过程口吻的引子**机械地改写成中性引子, 正文一字不动。

为什么只改引子: 正文里的 `原实现用 X, 会切坏 JSON, 故现按字节截断` 是**约束+理由**(说明为什么代码长这样),
属该保留的工程信息; 而 `修复:` 这个引导词才是"开发过程叙述"。故:
    `// 修复(回绕): 正文`  -> `// 约束(回绕): 正文`
    `// 修复: 正文`        -> `// 约束: 正文`
    `// 修复 正文`         -> `// 约束: 正文`
只处理 `//` 注释行的**行首引子**, 不碰正文、不碰代码行。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '备注引子中性化-写入前')
FILES = ["main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
         "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
         "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
         "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
         "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv"]

# 行首引子: 缩进 + // + 可选空白 + 修复 + 可选(标签) + 可选冒号
PAT = re.compile(r'^(\s*//\s*)修复(\s*\([^)]*\))?\s*[:：]?\s*')
changed_total = 0
for f in FILES:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    raw = open(p, 'rb').read()
    text = raw.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split('\n')
    hits = 0
    for i, ln in enumerate(lines):
        m = PAT.match(ln)
        if not m:
            continue
        tag = m.group(2) or ''
        body = ln[m.end():]
        lines[i] = '%s约束%s: %s' % (m.group(1), tag, body)
        hits += 1
    if hits:
        os.makedirs(BAK, exist_ok=True)
        dst = os.path.join(BAK, f)
        if not os.path.exists(dst):
            shutil.copy2(p, dst)
        open(p, 'wb').write(nl.join(lines).encode('utf-8'))
        print('   %-26s 引子改写 %d 处' % (f, hits))
        changed_total += hits
print('合计改写 %d 处引子' % changed_total)
