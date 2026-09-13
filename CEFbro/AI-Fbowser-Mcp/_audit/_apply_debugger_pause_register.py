# -*- coding: utf-8 -*-
r"""第128轮(其二): 幽灵工具 `browser_debugger_pause` —— 让它从"看不见"变成"看得见的刻意守卫"。

实测(本轮):
  · `tools/list` 里 **没有** `browser_debugger_pause`(代理永远看不到它);
  · 但按名字直接调用**有效**, 返回的是实现里写好的诚实拒绝:
    `Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) | 请用 debugger_flow 一键断点 或
     debugger_enable → set_breakpoint → navigate → wait_paused`。
  ⇒ 结论: 它既不是死代码(实现+命令行注册表项都在, 且真能被调到), 也不是可用能力 —— 而是**看不见的守卫**。
     与既有先例 `browser_close_try`(注册行写明「⛔ 该工具恒失败, 请改用 browser_close」)保持一致:
     把守卫**补进注册表**, 让代理一次就能读到"为什么不能这么做 + 该怎么做", 而不是靠猜或撞。

用法: py -3 _audit\_apply_debugger_pause_register.py [--apply]
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
LEDGER = os.path.join(ROOT, '_audit', '_tool_ledger.json')

ANCHOR = '添加工具JSON ("browser_debugger_resume", "从断点继续执行(Debugger.resume)| 需页面处于暂停态, 否则返回 页面未处于暂停状态")'
LINE = ('添加工具JSON ("browser_debugger_pause", "⛔ 已禁用(刻意保留的守卫, 恒失败): Debugger.pause 会'
        '**冻结没有 JS 执行点的页面并堵塞 CDP 命令队列**(队列 FIFO —— 后续所有 CDP 命令与自动 resume 都排在它后面, '
        '连锁超时, 连 browser_status 都可能挂), 故本工具**不接受调用并直接给出替代流程** | 正确做法: ①一键断点用 '
        'browser_debugger_flow ②手动流程 browser_debugger_enable → browser_debugger_set_breakpoint → 触发页面 → '
        'browser_debugger_wait_paused ③要看某个函数被调用时的现场, 用 browser_debugger_flow 的 function 目标或 '
        'browser_reverse_* 系列 | 说明书更正(第128轮): 该工具此前**没有注册行**(不在 tools/list 里), 按名调用却真的有效, '
        '属"看不见的守卫"; 现已如实注册, 使拒绝理由与替代方案可被发现")')


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    if '添加工具JSON ("browser_debugger_pause"' in txt:
        print('MCP_Server.wsv: 已注册过(幂等)')
    else:
        assert txt.count(ANCHOR) == 1, '锚点 %d 次' % txt.count(ANCHOR)
        out = txt.replace(ANCHOR, LINE + '\n' + ANCHOR, 1)
        print('MCP_Server.wsv: 已插入注册行(行数 %d -> %d)' % (len(txt.split('\n')), len(out.split('\n'))))
        if '--apply' in sys.argv:
            io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
            c = io.open(SERVER, encoding='utf-8').read()
            assert '添加工具JSON ("browser_debugger_pause"' in c and '\r' not in c
            print('   已写入并回读校验通过')

    # 台账: 记一条**人工受控**条目(与 browser_close_try 同一做法) —— 它的"正确行为"就是拒绝。
    d = json.loads(io.open(LEDGER, encoding='utf-8').read())
    if 'browser_debugger_pause' in d:
        print('台账: 已有条目, 跳过')
    else:
        d['browser_debugger_pause'] = {
            "tool": "browser_debugger_pause", "cls": "OK_MANUAL", "elapsed": 0.0, "args": {},
            "note": ("[人工受控实测·非探针] 第128轮: `tools/list` 里原本**没有**它(看不见的守卫), 按名调用有效并返回"
                     "实现写好的诚实拒绝: `Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) | 请用 debugger_flow "
                     "一键断点 或 debugger_enable → set_breakpoint → navigate → wait_paused` || 现已补注册行使其可被发现; "
                     "本条目按'行为与设计一致'记 pass(它不是能力缺口, 也不是故障)"),
            "ts": "12-45 12:47", "round": 128, "status": "pass", "manual": True,
        }
        print('台账: 已补 browser_debugger_pause 人工条目')
        if '--apply' in sys.argv:
            with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
                f.write(json.dumps(d, ensure_ascii=False, indent=2))
            print('   台账已写入(%d 条)' % len(d))
    if '--apply' not in sys.argv:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
