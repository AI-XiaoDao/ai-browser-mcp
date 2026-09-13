# -*- coding: utf-8 -*-
import io, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
md = io.open(r'_audit\_classlib_gap.md', encoding='utf-8').read()
BAD = '\x60'
tot = 0
cur = None
cnt = {}
for ln in md.split('\n'):
    m = re.match(r'^###\s+(.+?)\s+\((\d+)\)', ln)
    if m:
        cur = m.group(1)
        tot += int(m.group(2))
        cnt[cur] = int(m.group(2))
print("声明总数 =", tot, " 节数 =", len(cnt))
# 逐个重数
real = {}
for ln in md.split('\n'):
    m = re.match(r'^###\s+(.+?)\s+\((\d+)\)', ln)
    if m:
        cur = m.group(1)
        real.setdefault(cur, 0)
    elif cur and ln.strip().startswith(BAD):
        real[cur] = real.get(cur, 0) + len(re.findall(BAD + '[^' + BAD + ']+' + BAD, ln))
print("实数总数 =", sum(real.values()))
for k in cnt:
    if cnt[k] != real.get(k, 0):
        print("  DIFF", k, cnt[k], real.get(k, 0))
