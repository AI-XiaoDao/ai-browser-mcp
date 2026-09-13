# -*- coding: utf-8 -*-
"""给 5 处 "省略 action 会**直接执行动作**" 的内核分派加缺参守卫。

锚点用"条件行 + 紧随其后的第一条特有语句", 保证唯一; 只做精确整块替换。
这 5 处分别是:
  分派_全事件流(events_all) / 分派_动态探针(reverse_probe) / 分派_调用追踪(reverse_trace)
  / 分派_算法Hook(reverse_algo) / 分派_全局变量追踪(reverse_watch_global)
其中 events_all 的描述自己就写着"action 必填", 却把省略当成 enable —— 描述与行为直接矛盾。
"""
import io, os, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'MCP_Kernel.wsv')
GUARD = '''            如果 (MCP命令服务器.参数键存在 (参数JSON, "action") == 假)
            {
                // 修复(逐功能测试): 原条件为 动作 == "%s" || 动作 == "" —— 即**省略 action 会直接执行动作**
                // (监控/插桩/Hook 立即生效), 而工具描述却写着"action 必填"。缺参一律拒绝。
                返回 (MCP_响应构建.命令失败 (命令ID, "action 不能省略 | 省略会直接执行 %s 并使%s立即生效, 属意外动作 | 查询状态请显式传 action:status"))
            }
'''

SITES = [
    ('        如果 (动作 == "enable" || 动作 == "")\n        {\n            // 浏览器事件全开 (13项)',
     'enable', '13 项监控'),
    ('        如果 (动作 == "enable" || 动作 == "")\n        {\n            变量 注入代码 <类型 = 文本型>\n            注入代码 = "(function(){if(window.__MCP_PROBE__)return',
     'enable', '五维插桩'),
    ('        如果 (动作 == "start" || 动作 == "")\n        {\n            变量 目标文本 <类型 = 文本型>\n            目标文本 = MCP命令服务器.yyjson取文本 (参数JSON, "targets")',
     'start', '调用追踪'),
    ('        如果 (动作 == "start" || 动作 == "")\n        {\n            变量 注入代码 <类型 = 文本型>\n            注入代码 = "(function(){if(window.__MCP_ALGO_LOG__)return',
     'start', '算法 Hook'),
    ('        如果 (动作 == "start" || 动作 == "")\n        {\n            变量 名称文本 <类型 = 文本型>\n            名称文本 = MCP命令服务器.yyjson取文本 (参数JSON, "names")',
     'start', '全局变量追踪'),
]


def main():
    src = io.open(P, encoding='utf-8-sig').read()
    done = 0
    for anchor, act, what in SITES:
        if anchor not in src:
            print('  !! 锚点未命中(%s), 跳过' % what)
            continue
        if src.count(anchor) != 1:
            print('  !! 锚点不唯一(%s, %d 处), 跳过' % (what, src.count(anchor)))
            continue
        g = GUARD % (act, act, what)
        src = src.replace(anchor, g + anchor)
        done += 1
    if done != len(SITES):
        print('  只完成 %d/%d, 未写回(避免半成品)' % (done, len(SITES)))
        return 1
    io.open(P, 'w', encoding='utf-8-sig', newline='').write(src)
    print('  已插入 %d 处守卫' % done)
    return 0


if __name__ == '__main__':
    sys.exit(main())
