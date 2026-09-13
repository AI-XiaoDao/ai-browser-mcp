# -*- coding: utf-8 -*-
r"""第125轮(其五): 按只读审计 `_audit/_schema_audit_C.md` 修正"实现支持且实现自己推荐、但 schema 里看不到"的 action/参数。

这类缺陷的代价最直接: **代理看不到那个 action, 就永远试不出来** —— 而服务端自己的报错文案偏偏让你用它。
逐条(审计给的行号/锚点已复核):
  1 browser_reverse_instrument_script : `confirm` 未声明, 而它是 install(默认动作)的硬前置 ⇒ **空参/默认调用 100% 失败**
     (台账里这条长期记 fail, 成因正是"参数不可见"; 声明出来后才可能一次调用成功)
  2 browser_kernel_events_all          : 实现了 action=get(且实现自己在报错里推荐它), schema 枚举只有 enable/disable
  3 browser_kernel_watch               : 实现了 action=list(changes_json 的唯一出口), schema 只写 start/stop/clear
  4 browser_kernel_cdp_monitor         : 实现了 action=list(events_json 出口), schema 只写 add/remove/clear/enable/disable;
                                        另: max 的**默认值实际是 200**(MCP_Kernel.wsv 变量默认), 描述却写"默认500"
  5 browser_kernel_download            : 实现了 action=list, schema 只写 pause/resume/cancel/clear_queue
  6 browser_kernel_reactor             : 描述里那句"(写错(如 load_end)永不触发)"与实现相矛盾 —— 实现自己推荐的正是 load_end
                                        (load_end 是本项目**确实落库**的事件族), 已按事实改写并指向 browser_event 的事件名清单

用法: py -3 _audit\_apply_schema_audit_fixes2.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

EDITS = [
    # 1 instrument_script: 补 confirm(install 的硬前置)
    ("browser_reverse_instrument_script",
     '属性项JSON ("event", "text", "beforeScriptExecution(默认)/beforeScriptWithSourceMapExecution"), ""))',
     '属性项JSON ("event", "text", "beforeScriptExecution(默认)/beforeScriptWithSourceMapExecution") + "," + 属性项JSON ("confirm", "boolean", "**install 的硬前置**: 不传 confirm=true 会被明确拒绝(实测装上后本会话 JS 通道即被阻塞, 需随后 action=suppress 止血)"), ""))',
     '1 补 confirm(install 硬前置)'),
    ("browser_reverse_instrument_script",
     '"V8插装(拆打包器核心):',
     '"V8插装(拆打包器核心) | ⚠ **install 需显式传 confirm=true**(见 schema; 不带 confirm 会被拒绝, 这是刻意闸门不是故障):',
     '1 描述点明 confirm 前置'),
    # 2 events_all: 补 action=get
    ("browser_kernel_events_all",
     '单参数Schema文本 ("action", "text", "enable 全开 / disable 全关")',
     '单参数Schema文本 ("action", "text", "enable 全开 / disable 全关 / get 查看 28 个开关的当前值(实现支持且实现自己在报错里推荐)")',
     '2 补 action=get'),
    ("browser_kernel_events_all",
     'disable 全部关闭。',
     'disable 全部关闭, **get** 查看各开关当前值。',
     '2 描述补 get'),
    # 3 watch: 补 action=list
    ("browser_kernel_watch",
     '属性项JSON ("action", "text", "start/stop/clear")',
     '属性项JSON ("action", "text", "start/stop/clear/list(列出各监视任务与 changes_json —— 值变化的唯一出口)")',
     '3 补 action=list'),
    ("browser_kernel_watch",
     'stop停止, clear清空;',
     'stop停止, clear清空, **list** 列出监视任务与值变化记录(changes_json);',
     '3 描述补 list'),
    # 4 cdp_monitor: 补 action=list + 修正 max 默认值
    ("browser_kernel_cdp_monitor",
     '属性项JSON ("action", "text", "add/remove/clear/enable/disable")',
     '属性项JSON ("action", "text", "add/remove/clear/enable/disable/list(列出订阅模式与最近捕获的事件 events_json —— 捕获结果的唯一出口)")',
     '4 补 action=list'),
    ("browser_kernel_cdp_monitor",
     'max为缓存上限默认500最大5000), remove移除, clear清空, enable/disable总开关。',
     'max为缓存上限**默认200**最大5000), remove移除, clear清空, enable/disable总开关, **list** 看订阅与最近捕获。',
     '4 max 默认值改准 + 描述补 list'),
    ("browser_kernel_cdp_monitor",
     '属性项JSON ("max", "integer", "事件缓存上限(默认500, 最大5000)")',
     '属性项JSON ("max", "integer", "事件缓存上限(默认200, 最大5000)")',
     '4 max 参数描述改准'),
    # 5 download: 补 action=list
    ("browser_kernel_download",
     '属性项JSON ("action", "text", "pause/resume/cancel/clear_queue")',
     '属性项JSON ("action", "text", "pause/resume/cancel/clear_queue/list(列出下载队列; 实现支持且实现自己在报错里推荐)")',
     '5 补 action=list'),
    ("browser_kernel_download",
     'clear_queue清空队列;',
     'clear_queue清空队列, **list** 列出队列(实现支持的出口);',
     '5 描述补 list'),
    # 6 reactor: 去掉与实现矛盾的"load_end 永不触发", 并把 load_end/title_changed 补进真实事件名清单
    ("browser_kernel_reactor",
     '写错(如 load_end)的规则会被接受但**永不触发**且无任何提示',
     '写错(**不在清单里**的名字)的规则会被接受但**永不触发**且无任何提示 —— 注意 load_end 与 title_changed 都是**有效**事件名(两者均已实测落库), 旧文案把 load_end 当反例是错的',
     '6 reactor 描述纠正(load_end 是有效名)'),
    ("browser_kernel_reactor",
     '属性项JSON ("event", "text", "事件名(真实值): * (通配, 推荐先用它验证链路) / navigate /',
     '属性项JSON ("event", "text", "事件名(真实值): * (通配, 推荐先用它验证链路) / load_end / title_changed / navigate /',
     '6 reactor 事件清单补 load_end/title_changed'),
]


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    b0 = balance(txt)
    done = []
    for tool, old, new, tag in EDITS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d 条' % (tool, len(idx))
        i = idx[0]
        if new in lines[i]:
            done.append(tag + ' (已存在)')
            continue
        assert lines[i].count(old) == 1, '%s 旧子串 %d 次: %s' % (tool, lines[i].count(old), old[:44])
        lines[i] = lines[i].replace(old, new, 1)
        done.append(tag)
    out = '\n'.join(lines)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server.wsv: 行数不变 %d; 完成 %d 项:' % (len(lines), len(done)))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        for must in ('confirm", "boolean"', 'enable/disable/list(', '默认200, 最大5000'):
            assert must in c, '缺少 %s' % must
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
