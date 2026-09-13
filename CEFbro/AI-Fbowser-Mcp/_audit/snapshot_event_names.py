# -*- coding: utf-8 -*-
"""快照当前"已记录的事件名"集合(供补丁落地后做 diff, 精确找出新增/改名的事件)。

用法:
    py -3 _audit/snapshot_event_names.py before      # 落盘 _audit/_event_names_before.txt
    py -3 _audit/snapshot_event_names.py after       # 落盘 ..._after.txt 并打印 diff
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

# 记录监控事件 (开关, "name", id, data) / 记录事件日志 ("browser_event", "name", ...)
PAT1 = re.compile(r'记录监控事件 \([^,]+,\s*"([a-z0-9_]+)"')
PAT2 = re.compile(r'记录事件日志 \("[a-z_]+",\s*"([a-z0-9_]+)"')

found = {}
for f in FILES:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    for i, ln in enumerate(open(p, 'rb').read().decode('utf-8').split('\n'), 1):
        for pat in (PAT1, PAT2):
            for m in pat.finditer(ln):
                found.setdefault(m.group(1), []).append('%s:%d' % (f, i))

tag = sys.argv[1] if len(sys.argv) > 1 else 'before'
out = os.path.join(ROOT, '_audit', '_event_names_%s.txt' % tag)
with open(out, 'w', encoding='utf-8', newline='\n') as fh:
    for name in sorted(found):
        fh.write('%s\t%s\n' % (name, ';'.join(found[name][:3])))
print('事件名 %d 个 -> %s' % (len(found), out))

if tag == 'after':
    prev = {}
    pb = os.path.join(ROOT, '_audit', '_event_names_before.txt')
    if os.path.exists(pb):
        for ln in open(pb, encoding='utf-8').read().split('\n'):
            if '\t' in ln:
                k, v = ln.split('\t', 1)
                prev[k] = v
    new = sorted(set(found) - set(prev))
    gone = sorted(set(prev) - set(found))
    print('\n== 新增事件名 %d 个 ==' % len(new))
    for n in new:
        print('   %-34s %s' % (n, ';'.join(found[n][:3])))
    print('\n== 消失事件名 %d 个 ==' % len(gone))
    for n in gone:
        print('   %-34s (原 %s)' % (n, prev[n]))
