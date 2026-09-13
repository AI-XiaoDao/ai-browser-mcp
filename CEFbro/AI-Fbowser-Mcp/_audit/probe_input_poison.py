# -*- coding: utf-8 -*-
r"""找出"谁把 Input 域搞慢": 逐个候选工具后立刻量 mouse_move 的延迟(自动重启, 干净起点)。

背景: 快检里 mouse_move 那条臂在**跑完整轮快检之后**稳定 ~5.1s, 而同一会话里随后再量又是 0.03s;
而刚重启、什么都不做时第一条 Input 命令只要 0.03s ⇒ 成本不是冷启动, 是**某个工具留下的状态**。
本脚本按"先可疑、后一般"的顺序, 每调一个候选就量一次 mouse_move, 第一个变慢的候选即元凶。

候选选择依据: 快检在鼠标臂之前依次跑了 读取/缺元素/写操作/execute_js×12/scrape/snapshot/表单/highlight。
其中能影响渲染器输入或 CDP 全局状态的: snapshot(可访问性 AX 域) > highlight(注入样式) > execute_js 连打。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), dt


def probe(label, n, a=None, quiet=True):
    e, t, dt = call(n, a)
    if not quiet:
        print('   %-36s %6.2fs err=%-5s %s' % (label, dt, e, t.replace('\n', ' ')[:60]))
    return dt, e, t


def mouse_twice(tag):
    d1, _, _ = probe('', "browser_mouse_move", {"x": 150, "y": 150})
    d2, _, _ = probe('', "browser_mouse_move", {"x": 152, "y": 152})
    flag = '  <== 变慢!' if d1 >= 3.0 else ''
    print('   %-40s mouse=%.2fs / %.2fs%s' % (tag, d1, d2, flag))
    if d1 >= 3.0:
        # 再确认一次读工具是否仍快(区分"Input 专属慢"与"整体退化")
        dr, er, tr = probe('', "browser_dom_query", {"selector": "h1"})
        print('        同时 dom_query=%.2fs err=%s(若仍 0.02s ⇒ 慢的是 Input 域, 不是通道整体)' % (dr, er))
    return d1


print('== 重启实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)

print('\n-- 起点基线 --')
mouse_twice('基线(未做任何事)')

print('\n-- 候选 1: browser_snapshot(可访问性 AX 域) --')
probe('', "browser_snapshot", {})
mouse_twice('snapshot 之后')

print('\n-- 候选 2: browser_highlight show + clear --')
probe('', "browser_highlight", {"selector": "h1", "duration_ms": 0})
probe('', "browser_highlight", {"action": "clear"})
mouse_twice('highlight 之后')

print('\n-- 候选 3: execute_js 连打 12 次 --')
for _ in range(12):
    probe('', "browser_execute_js", {"code": "1+1"})
mouse_twice('execute_js x12 之后')

print('\n-- 候选 4: 表单族(get_forms / fill_exists) --')
probe('', "browser_get_forms", {})
probe('', "browser_fill_exists", {"selector": "h1"})
mouse_twice('表单族之后')

print('\n-- 候选 5: scroll_by 与 snapshot 再次 --')
probe('', "browser_scroll_by", {"y": 0})
probe('', "browser_snapshot", {})
mouse_twice('scroll+snapshot 之后')

print('\n-- 收尾健康 --')
probe('execute_js', "browser_execute_js", {"code": "1+1"}, quiet=False)
probe('get_url', "browser_get_url", {}, quiet=False)
