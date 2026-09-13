# -*- coding: utf-8 -*-
"""重做事件名快照(diff 用): 补上第三种记录写法 `记录浏览器事件`。

上一版只匹配 `记录监控事件` / `记录事件日志 ("browser_event", …)`, 于是 MCP_Callbacks.wsv 里用
`MCP命令服务器.记录浏览器事件 ("name", id, data)` 记的 5 个新事件**没进 diff**(diff 少报了 5 个, 不是补丁少做了)。

用法:
  py -3 _audit/snapshot_event_names2.py             # 扫 src(现状) -> _event_names_after.txt
  py -3 _audit/snapshot_event_names2.py <目录>       # 扫指定目录(如 备份/事件覆盖补丁r115-写入前) -> before
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
         "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
         "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
         "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
         "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv"]

PATS = [
    re.compile(r'记录监控事件 \([^,]+,\s*"([a-z0-9_]+)"'),
    re.compile(r'记录浏览器事件 \("([a-z0-9_]+)"'),
    re.compile(r'记录事件日志 \("[a-z_]+",\s*"([a-z0-9_]+)"'),
]

arg = sys.argv[1] if len(sys.argv) > 1 else None
SRC = arg if arg else os.path.join(ROOT, 'src')
tag = 'before' if arg else 'after'

found = {}
for f in FILES:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    for i, ln in enumerate(open(p, 'rb').read().decode('utf-8', errors='replace').split('\n'), 1):
        for pat in PATS:
            for m in pat.finditer(ln):
                found.setdefault(m.group(1), []).append('%s:%d' % (f, i))

out = os.path.join(ROOT, '_audit', '_event_names_%s.txt' % tag)
with open(out, 'w', encoding='utf-8', newline='\n') as fh:
    for name in sorted(found):
        fh.write('%s\t%s\n' % (name, ';'.join(found[name][:3])))
print('[%s] 源目录 %s -> 事件名 %d 个 -> %s' % (tag, SRC, len(found), out))

if tag == 'after':
    pb = os.path.join(ROOT, '_audit', '_event_names_before.txt')
    prev = {}
    if os.path.exists(pb):
        for ln in open(pb, encoding='utf-8').read().split('\n'):
            if '\t' in ln:
                k, v = ln.split('\t', 1)
                prev[k] = v
    new = sorted(set(found) - set(prev))
    gone = sorted(set(prev) - set(found))
    print('\n== 新增事件名 %d 个 ==' % len(new))
    for n in new:
        print('   %-30s %s' % (n, ';'.join(found[n][:2])))
    print('== 消失 %d 个: %s ==' % (len(gone), gone))
