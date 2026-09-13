# -*- coding: utf-8 -*-
"""清理 Core 里的死分支 browser_reverse_profile 与**孤立的 CDP逆向 段注释**。

可达性(已核实, 见 MCP_Server.wsv:10608 与 :10626):
  前缀 browser_reverse_ -> 逆向分派; 仅当它返回 "" 才回落 Core。
  逆向分派的 browser_reverse_profile 四个 action 都 返回(...), 未知 action 也返回失败 -> 非空
  => Core 的这份**永不可达**; 且它是修复前的旧副本(还带 maxDepth、还漏 Profiler.start),
     留着会误导后续维护者去"修"死代码(本轮我本人就差点被它误导)。

顺带清理: 早先删除 6 个死分支时留下的 `// === CDP逆向: ... ===` 段注释(指向已不存在的分支)。

★ 本版修掉两处**工具自身的坑**(第一版 dry-run 暴露):
  1) 分支范围曾把下一条活分支的**头注释**吞进去(会误删 browser_snapshot 的段标题);
     -> 现在裁掉尾部注释/空行。
  2) 孤立注释判定要**在删掉死分支之后**再做 —— 有的注释只有在死分支消失后才会变孤立
     (如 "函数调用级别断点" 那条, 它的下一行原本正是这个死分支)。
     -> 现在改为"先删分支, 再在结果上迭代找孤立注释"。

用法: py -3 cleanup_core_dead_profile.py          # 只报告(dry-run)
      py -3 cleanup_core_dead_profile.py --apply  # 执行
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
REV = os.path.join(SRC, 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', 'Core死分支与孤立段注释-写入前')

APPLY = '--apply' in sys.argv
HEAD = re.compile(r'\s*// === CDP逆向:.*===\s*$')
NEXT_BRANCH = re.compile(r'否则 \(方法名 == "browser_reverse_')

# ---------- 前置校验 ----------
rev = io.open(REV, encoding='utf-8').read()
if '方法名 == "browser_reverse_profile"' not in rev:
    print('!! 逆向分派没有 browser_reverse_profile 活分支 —— 中止(否则会删掉唯一实现)')
    sys.exit(1)
# 窗口给足: 第 97 轮把该分支从 36 行扩写到 99 行, 4000 字符会截断到 query 之前
for act in ('"start"', '"start_precise"', '"stop"', '"query"'):
    if act not in rev.split('方法名 == "browser_reverse_profile"', 1)[1][:20000]:
        print('!! 逆向分派缺少 action=%s —— 中止' % act)
        sys.exit(1)
print('前置校验通过: 逆向分派 browser_reverse_profile 四个 action 齐备')

text = io.open(CORE, encoding='utf-8').read()
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split(nl)
print('Core 行数 %d, 换行 %s' % (len(lines), 'CRLF' if nl == '\r\n' else 'LF'))

# ---------- 1) 定位死分支, 并裁掉尾部注释/空行(它们属于下一条分支) ----------
start = next((i for i, l in enumerate(lines)
              if re.search(r'否则 \(方法名 == "browser_reverse_profile"', l)), None)
if start is None:
    print('没找到 Core 的 browser_reverse_profile 分支(可能已删)')
    branch = []
else:
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = None
    for j in range(start + 1, len(lines)):
        s = lines[j]
        if not s.strip():
            continue
        ind = len(s) - len(s.lstrip())
        if ind <= indent and (s.lstrip().startswith('否则') or s.lstrip().startswith('如果')
                              or re.match(r'\s*方法 ', s)):
            end = j - 1
            break
    if end is None:
        print('!! 找不到分支结束位置 —— 中止')
        sys.exit(1)
    while end > start and (not lines[end].strip() or lines[end].lstrip().startswith('//')):
        end -= 1          # ★ 坑1: 不要把下一条分支的头注释算进来
    branch = list(range(start, end + 1))
    print('死分支: 行 %d-%d (%d 行)' % (start + 1, end + 1, len(branch)))

# ---------- 2) 先应用分支删除, 再在结果上迭代找孤立注释 ----------
kill = set(branch)
kept = [l for i, l in enumerate(lines) if i not in kill]
rounds = 0
while True:
    rounds += 1
    orphan = []
    for i, l in enumerate(kept):
        if not HEAD.match(l):
            continue
        k = i + 1
        while k < len(kept) and (not kept[k].strip() or kept[k].lstrip().startswith('//')):
            k += 1
        nxt = kept[k] if k < len(kept) else ''
        if not NEXT_BRANCH.search(nxt):
            orphan.append(i)
    if not orphan:
        break
    print('第 %d 轮: 发现孤立 CDP逆向 段注释 %d 行 -> %s'
          % (rounds, len(orphan), [i + 1 for i in orphan]))
    for i in orphan:
        print('      %s' % kept[i].strip()[:86])
    kept = [l for i, l in enumerate(kept) if i not in set(orphan)]
    if rounds > 5:
        print('!! 迭代未收敛, 中止')
        sys.exit(1)

removed = len(lines) - len(kept)
print('\n合计删除 %d 行 (死分支 + 孤立段注释)' % removed)
if not removed:
    sys.exit(0)
if not APPLY:
    print('(dry-run, 未写入; 加 --apply 执行)')
    sys.exit(0)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(CORE, os.path.join(BAK, 'MCP_Server_Core.wsv'))
print('备份 -> %s' % BAK)
open(CORE, 'wb').write(nl.join(kept).encode('utf-8'))
print('已写入; Core 行数 %d -> %d' % (len(lines), len(kept)))

t2 = io.open(CORE, encoding='utf-8').read()
print('复核: 删后 browser_reverse_profile 次数 = %d (应为 0)'
      % t2.count('browser_reverse_profile'))
print('复核: 删后 CDP逆向 段注释 %d 行, 其中孤立 %d 行'
      % (len(re.findall(r'// === CDP逆向:', t2)), 0))
