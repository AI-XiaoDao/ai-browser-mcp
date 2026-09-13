# -*- coding: utf-8 -*-
"""把 2 个"纳入同步后反而更差"的工具从两张名单里撤回(恢复原异步行为)。

真机验收结论:
  · browser_scrape          -> 同步后回**空串** ""(中央转换器 将异步结果转为命令响应
                               处理不了它的载荷形状) —— 比原来的回执+poll_hint **更差**, 必须撤回
  · browser_permission_spoof -> 同步后 20s **超时失败**(任务在该预算内没落地) —— 撤回

保留的 10 个均已实测"一次调用即拿到真实数据/完成写入"(dom_set_html 还做了回读验证)。
遗留给后续: 修好 将异步结果转为命令响应 的载荷形状覆盖后, 可再把这两个加回来。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '撤回两个同步名单项-写入前')

# 这两处是我上一轮新加的名单行, 撤回即删除对应名字
REPL = [
    (' || 规范名 == "browser_scrape"', ''),
    (' || 规范名 == "browser_permission_spoof"', ''),
]

text = io.open(SRC, encoding='utf-8').read()
for pat, _ in REPL:
    print('  %-46s 出现 %d 次' % (pat.strip(), text.count(pat)))
if any(text.count(p) == 0 for p, _ in REPL):
    print('!! 有模式未命中, 中止')
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server.wsv'))
after = text
for pat, rep in REPL:
    after = after.replace(pat, rep)
open(SRC, 'wb').write(after.encode('utf-8'))
print('已撤回; 备份 -> %s' % BAK)
for n in ('browser_scrape', 'browser_permission_spoof'):
    print('  复核 %-28s 现在名单里出现 %d 次(应为 0)'
          % (n, after.count('规范名 == "%s"' % n)))
for n in ('browser_dom_get_html', 'browser_dom_set_html', 'browser_extract',
          'browser_view_source', 'browser_vip_dom_get_document', 'browser_vip_dom_search',
          'browser_reverse_cookie_sources', 'browser_inject', 'browser_canvas_noise',
          'browser_dom_select'):
    print('  复核 %-28s 保留, 名单里出现 %d 次(应>=1)'
          % (n, after.count('规范名 == "%s"' % n)))
