# -*- coding: utf-8 -*-
r"""第131轮(修补2): 把 `browser_cdp_event` / `browser_console_eval` 两行**整行重写**为正确的多属性 schema。

起因: 上一批的通用插入用"行尾最后一个实参"定位属性列表, 但这两行是 `单参数Schema文本 (名, 类型, 描述)`
—— 于是属性表达式被塞进了**描述字符串内部**(还改了语义: 描述里凭空多出 `+ "," + 属性项JSON ...`),
运行时 schema 里自然看不到新参数(全量扫描因此仍报 2 条 MISSING)。两行整行重写是唯一干净的修法。

用法: py -3 _audit\_fix_round131b.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

FIX = {
    # 工具名: 整行新文本
    "browser_cdp_event":
        '添加工具JSON ("browser_cdp_event", "VIP: 读取最近的CDP事件", 多属性Schema文本 '
        '(属性项JSON ("event_name", "text", "事件名(如 Debugger.paused); 亦可用 event") + "," + '
        '属性项JSON ("event", "text", "CDP 事件名(与 event_name 等价; 实现两者都读)"), ""))',
    "browser_console_eval":
        '添加工具JSON ("browser_console_eval", "控制台执行JS(默认同步返回)", 多属性Schema文本 '
        '(属性项JSON ("expression", "text", "JS表达式") + "," + '
        '属性项JSON ("file", "text", "从本地文件读取要执行的 JS(绝对路径) —— **大脚本请用本参数**, '
        '避免走 HTTP 通道约 1MB 的 arguments 限制"), ""))',
}


def main():
    lines = io.open(SERVER, encoding='utf-8').read().split('\n')
    done = []
    for tool, new in FIX.items():
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        old = lines[i]
        assert '单参数Schema文本' in old, '%s 已不是单参数形式(可能已修)' % tool
        lines[i] = new
        done.append('%s: 整行重写为多属性 schema' % tool)
    out = '\n'.join(lines)
    print('MCP_Server.wsv:')
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert '多属性Schema文本 (属性项JSON ("event_name"' in c
        assert '多属性Schema文本 (属性项JSON ("expression"' in c
        assert '属性项JSON ("event", "text", "CDP 事件名' in c
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
