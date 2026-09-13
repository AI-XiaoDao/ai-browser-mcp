# -*- coding: utf-8 -*-
r"""修掉第137轮新注释里的"开发过程叙述"(清洁扫描 STRONG 命中 3 处)。

规矩(第133轮定): 注释里不写"第N轮/原先/已改为"这类过程叙述, 只留**当下成立的技术理由**。
本脚本把三条注释改写为纯技术表述, 实测数据与结论一字不减。

用法: py -3 _audit\_fix_round137_cmt.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXES = [
    (os.path.join(ROOT, 'src', 'MCP_Server.wsv'),
     '//   实测依据(第137轮, _audit/probe_iv_timing.py 走原始 CDP 通道量测):',
     '//   量测依据(_audit/probe_iv_timing.py 以原始 CDP 通道实测, 可复现):'),
    (os.path.join(ROOT, 'src', 'MCP_Server.wsv'),
     '// ★ resume 之后要**继续等原来那条请求**, 而不是重新派发(第137轮原始 CDP 通道实测):',
     '// ★ resume 之后要**继续等原来那条请求**, 而不是重新派发(原始 CDP 通道实测):'),
    (os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv'),
     '// ★ 标志只在**确认拦停已解除**之后才清零(第137轮修正): 卸载与兜底都失败时插装依然拦着页面,',
     '// ★ 标志只在**确认拦停已解除**之后才清零: 卸载与兜底都失败时插装依然拦着页面,'),
    (os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv'),
     '// 立刻置位(必须在下面的**自检之前**): 自检本身就是一条会被这条插装拦停的 evaluate,',
     '// 立刻置位(必须在下面的**自检之前**): 自检本身就是一条会被插装拦停的 evaluate,'),
]
APPLY = '--apply' in sys.argv


def main():
    cache = {}
    for path, old, new in FIXES:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('· 已改过/未找到: %s' % old[:60])
            continue
        assert txt.count(old) == 1, '锚点命中 %d 次: %s' % (txt.count(old), old[:60])
        cache[path] = txt.replace(old, new, 1)
        print('· 改写: %s' % old[:60])
    if APPLY:
        for path, txt in cache.items():
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
            print('   ✔ 已写入 %s' % os.path.basename(path))
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
