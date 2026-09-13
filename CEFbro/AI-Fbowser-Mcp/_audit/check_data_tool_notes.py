# -*- coding: utf-8 -*-
"""读台账里若干"取数据"工具的实测原文, 判断异步通道到底有没有把数据带回来。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import tool_ledger as TL

NAMES = ["browser_reverse_runtime", "browser_reverse_heap", "browser_network_body",
         "browser_reverse_listeners", "browser_reverse_call_fn",
         "browser_reverse_websocket", "browser_reverse_preload",
         "browser_reverse_dom_breakpoint", "browser_reverse_cdp_hook",
         "browser_network_requests"]

d = TL.load()
for n in NAMES:
    r = d.get(n)
    if not r:
        print('== %-34s (台账无记录)' % n)
        continue
    print('== %-34s status=%s cls=%s %.2fs' % (n, r.get('status'), r.get('cls'),
                                               r.get('elapsed', 0)))
    print('   args: %s' % (r.get('args') or {}))
    print('   说明: %s' % (r.get('note') or '')[:400])
    print()
