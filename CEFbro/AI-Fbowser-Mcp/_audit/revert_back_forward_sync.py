# -*- coding: utf-8 -*-
"""撤回 browser_back/browser_forward 的同步名单项（保留"注册等待任务"这一改进）。

原因(本轮实测):
  纳入同步后, `back` **0.03s** 就返回"等待条件满足: load_end → https://example.com/?navB=2"
  —— 其中的 URL 是**后退之前**那一页(B), 即它命中了**上一次导航遗留的 load_end 事件**;
  而同一改动下用 mcp_result 轮询时, 得到的却是正确的
  "等待条件满足: load_end → https://example.com/?wlA=1"(后退后那一页 A)。
  => 事件驱动那条等待路径**不判序事件是否属于本次导航**, 在调用内同步等待会被**旧事件立刻满足**,
     属"假满足"(会谎称载入完成)。故保守撤回: 保留可轮询的等待任务(实测正确), 不改成同步。

顺带记录的待查线索(下一轮): 同一路径也可能影响 `browser_navigate`(它也在同步名单里),
需专门做"紧接着连续导航 + 立刻同步等待"的对照实验确认。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '撤回前后退同步名单-写入前')

text = io.open(SRC, encoding='utf-8').read()
BLOCKS = [
    ('        // 历史导航: 与 navigate/reload 同款 —— 等 load_end 落地再返回\n'
     '        // (实测 load_end 确实会为 back/forward 触发, 见报告 §123; 不纳入的话调用方还得自己轮询)\n'
     '        如果 (规范名 == "browser_back" || 规范名 == "browser_forward")\n'
     '        {\n'
     '            返回 (真)\n'
     '        }\n'),
    ('        // 与 应同步等待 保持一致\n'
     '        如果 (规范名 == "browser_back" || 规范名 == "browser_forward")\n'
     '        {\n'
     '            返回 (20000)\n'
     '        }\n'),
]
for b in BLOCKS:
    c = text.count(b)
    print('待撤回块 命中 %d (应为1)' % c)
    if c != 1:
        print('!! 中止')
        sys.exit(1)
    text = text.replace(b, '', 1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server.wsv'))
open(SRC, 'wb').write(text.encode('utf-8'))
print('已撤回; 备份 -> %s' % BAK)
for n in ('browser_back', 'browser_forward'):
    print('  复核 %-18s 名单出现 %d 次(应为0)' % (n, text.count('规范名 == "%s"' % n)))
print('  复核 注册加载等待任务 仍保留(由 Core 侧统计): 见下次编译')
