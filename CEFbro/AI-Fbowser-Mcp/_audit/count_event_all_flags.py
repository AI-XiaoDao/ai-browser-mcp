# -*- coding: utf-8 -*-
"""数清楚 browser_kernel_events_all 的 enable 分支到底打开多少个开关(文案里 13/21 两个数字都不对)。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Kernel.wsv')
lines = open(p, 'rb').read().decode('utf-8').split('\n')

start = -1
end = -1
for i, ln in enumerate(lines):
    if start < 0 and '如果 (动作 == "enable" || 动作 == "")' in ln:
        start = i
    if start >= 0 and i > start and ('全事件流已开启' in ln):
        end = i
        break
if start < 0 or end < 0:
    print('!! 定位失败 start=%d end=%d' % (start, end))
    sys.exit(1)

PAT_T = re.compile(r'^\s*MCP命令服务器\.(是否\S*|是否记录\S*) = 真\s*$')
PAT_F = re.compile(r'^\s*MCP命令服务器\.(是否\S*|是否记录\S*) = 假\s*$')
flags = [ln.strip() for ln in lines[start:end + 1] if PAT_T.match(ln)]
print('enable 分支 %d..%d, 打开开关 = %d 个' % (start + 1, end + 1, len(flags)))
for f in flags:
    print('   %s' % f)

dstart = -1
for i, ln in enumerate(lines):
    if '否则 (动作 == "disable")' in ln:
        dstart = i
        break
df = [ln.strip() for ln in lines[dstart:dstart + 60] if PAT_F.match(ln)]
print('\ndisable 分支前 60 行关闭 = %d 个' % len(df))


def names(items):
    out = set()
    for it in items:
        out.add(it.split('.')[1].split(' ')[0].split('=')[0].strip())
    return out


ne, nd = names(flags), names(df)
print('enable 有而 disable 无: %s' % sorted(ne - nd))
print('disable 有而 enable 无: %s' % sorted(nd - ne))
