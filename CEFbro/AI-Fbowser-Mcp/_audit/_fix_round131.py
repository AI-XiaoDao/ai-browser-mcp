# -*- coding: utf-8 -*-
r"""第131轮(修补): ①上一批对 `browser_cdp_event`/`browser_console_eval` 的插入方式错了(它们用的是
`单参数Schema文本`, 而我把属性表达式当成了第 4 个实参追加 → 运行时 schema 里看不到新参数);
②navigate/back/forward/reload 的 `async_only` 描述**说过头了** —— 实现是"不等载入, 立刻返回成功",
**不返回 task_id**(实测: `navigate {async_only:true}` 回的是 `已导航到: …`)。

这两条都是本轮验收脚本抓出来的, 记下教训:
  · 改 schema 前先看该行用的是哪个 helper(单参数/多属性/双XY), 不同 helper 的补法不同;
  · 描述必须与实现一致 —— "立刻返回 task_id" 与 "立刻返回成功" 是两件事, 不能想当然。

用法: py -3 _audit\_fix_round131.py [--apply]
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

# ① 两个用 单参数Schema文本 的工具: 整体改为 多属性Schema文本(保留原参数 + 新增)
SINGLE = re.compile(
    r'添加工具JSON \("([^"]+)", ("(?:[^"\\]|\\.)*"), 单参数Schema文本 \("([^"]+)", "([^"]+)", ("(?:[^"\\]|\\.)*")(?:, (真|假))?\)\)$')
EXTRA = {
    'browser_cdp_event': '属性项JSON ("event", "text", "CDP 事件名(与 event_name 等价; 实现两者都读)")',
    'browser_console_eval': '属性项JSON ("file", "text", "从本地文件读取要执行的 JS(绝对路径) —— **大脚本请用本参数**, 避免走 HTTP 通道约 1MB 的 arguments 限制")',
}

# ② async_only 描述纠偏(只说"不等载入, 立刻返回", 不再承诺 task_id)
ASYNC_OLD = 'true=立刻返回 task_id 不等结果'
ASYNC_OLD2 = 'true=立刻返回 task_id 不等结果(与 wait_for_load 互斥语义)'
ASYNC_TOOLS = ['browser_navigate', 'browser_back', 'browser_forward', 'browser_reload']


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    done = []
    for tool, extra in EXTRA.items():
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if '属性项JSON ("name"' in lines[i] and '"event"' in lines[i] and tool == 'browser_cdp_event':
            done.append('%s(已是多属性)' % tool)
            continue
        m = SINGLE.match(lines[i].strip())
        if not m:
            done.append('%s(不是单参数形式, 跳过)' % tool)
            continue
        _t, desc, pname, ptype, pdesc, _req = m.groups()
        new = ('添加工具JSON ("%s", %s, 多属性Schema文本 (属性项JSON ("%s", "%s", %s) + "," + %s, ""))'
               % (tool, desc, pname, ptype, pdesc, extra))
        lines[i] = new
        done.append('%s(单参数 → 多属性, 保留 %s 并新增)' % (tool, pname))
    for tool in ASYNC_TOOLS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        if not idx:
            continue
        i = idx[0]
        if ASYNC_OLD in lines[i]:
            lines[i] = lines[i].replace(ASYNC_OLD, 'true=**不等载入完成, 立刻返回成功**(注意: 该路径**不返回 task_id**, 与异步工具不同)')
            done.append('%s(async_only 描述纠偏)' % tool)
        elif ASYNC_OLD2 in lines[i]:
            lines[i] = lines[i].replace(ASYNC_OLD2, 'true=**不等载入完成, 立刻返回成功**(该路径不返回 task_id)')
            done.append('%s(async_only 描述纠偏)' % tool)
    out = '\n'.join(lines)
    print('MCP_Server.wsv:')
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert '多属性Schema文本 (属性项JSON ("event_name"' in c
        assert '多属性Schema文本 (属性项JSON ("expression"' in c
        assert '不返回 task_id' in c
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
