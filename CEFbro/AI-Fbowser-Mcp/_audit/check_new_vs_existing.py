# -*- coding: utf-8 -*-
"""对每个"本轮纳入同步"的工具, 列出它在两张名单里的**全部**出现处, 区分:
  · 我本轮新加的(行内含一批新名字的合取)
  · **本来就有**的(独立成行 / 与别的一组混在一起)
—— 用来如实判定: 我的改动对哪些工具是**真的新增**, 对哪些只是**冗余重复**。
教训: 台账 note 是**历史记录**(browser_dom_get_html 那条来自第4轮), 不能当作"当前是否同步"的依据;
      要判断当前行为, 只能读当前源码或真机实测。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')

# 本轮我新加的行(整行匹配)
MINE = [
    '        如果 (规范名 == "browser_dom_get_html" || 规范名 == "browser_dom_select" || 规范名 == "browser_extract" || 规范名 == "browser_view_source")',
    '        如果 (规范名 == "browser_vip_dom_get_document" || 规范名 == "browser_vip_dom_search" || 规范名 == "browser_reverse_cookie_sources")',
    '        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise")',
]
NAMES = ["browser_dom_get_html", "browser_dom_select", "browser_extract", "browser_view_source",
         "browser_vip_dom_get_document", "browser_vip_dom_search",
         "browser_reverse_cookie_sources", "browser_inject", "browser_dom_set_html",
         "browser_canvas_noise"]

for n in NAMES:
    pre, mine = [], []
    for i, l in enumerate(L):
        if '规范名 == "%s"' % n not in l:
            continue
        (mine if l in MINE else pre).append(i + 1)
    tag = '本就同步(我的改动冗余)' if pre else '本轮才同步(真新增)'
    print('%-34s %-24s 原有行=%s 我加的行=%s' % (n, tag, pre or '无', mine or '无'))
