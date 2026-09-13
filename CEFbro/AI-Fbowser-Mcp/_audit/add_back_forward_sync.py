# -*- coding: utf-8 -*-
"""把 browser_back / browser_forward 纳入同步名单 —— 一次调用即等到载入完成。

依据(本轮实测): back 之后其等待任务**第 1 次轮询即收敛**:
  {"message":"等待条件满足: load_end → https://example.com/?wlA=1","event":"load_end",...}
即**历史导航确实会触发 load_end**(不必担心 bfcache 不触发导致必然超时)。
故纳入后调用方不必再自己轮询, 与 navigate/reload 的行为一致。

预算 20000: 历史导航通常很快, 但若目标页未缓存仍需联网取回。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '前后退纳入同步名单-写入前')

text = io.open(SRC, encoding='utf-8').read()

# 应同步等待: 插在"注入类"那组之后
SYNC_OLD = ('        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise" || 规范名 == "browser_permission_spoof")\n'
            '        {\n'
            '            返回 (真)\n'
            '        }\n')
SYNC_NEW = SYNC_OLD + (
    '        // 历史导航: 与 navigate/reload 同款 —— 等 load_end 落地再返回\n'
    '        // (实测 load_end 确实会为 back/forward 触发, 见报告 §123; 不纳入的话调用方还得自己轮询)\n'
    '        如果 (规范名 == "browser_back" || 规范名 == "browser_forward")\n'
    '        {\n'
    '            返回 (真)\n'
    '        }\n')

# 取同步等待毫秒
BUD_OLD = ('        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise" || 规范名 == "browser_permission_spoof")\n'
           '        {\n'
           '            返回 (20000)\n'
           '        }\n')
BUD_NEW = BUD_OLD + (
    '        // 与 应同步等待 保持一致\n'
    '        如果 (规范名 == "browser_back" || 规范名 == "browser_forward")\n'
    '        {\n'
    '            返回 (20000)\n'
    '        }\n')

for old, new, tag in ((SYNC_OLD, SYNC_NEW, '应同步等待'), (BUD_OLD, BUD_NEW, '取同步等待毫秒')):
    c = text.count(old)
    print('%s 锚点命中 %d (应为1)' % (tag, c))
    if c != 1:
        print('!! 中止')
        sys.exit(1)
    text = text.replace(old, new, 1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server.wsv'))
open(SRC, 'wb').write(text.encode('utf-8'))
print('已写入; 备份 -> %s' % BAK)
for n in ('browser_back', 'browser_forward'):
    print('  复核 %-18s 名单出现 %d 次(应为2)' % (n, text.count('规范名 == "%s"' % n)))
