# -*- coding: utf-8 -*-
"""幽灵注册 5 项的真机判定: 这些名字**可路由吗**? 路由后**有没有实现**?

`注册命令双变体 ("xxx")` 的设计是: `xxx` 与 `browser_xxx` 都能路由, 但只把其中一个
放进 MCP 工具清单。所以"注册表有、清单没有"**不等于**幽灵 —— 必须实际调一次看回包:
  · 有意义的回包(实现/刻意说明)  -> 只是未广告的路由别名, 不是缺口
  · 回"未知命令"/空               -> 真幽灵: 要么补实现, 要么删注册
安全性: browser_debugger_pause 若真实现会暂停调试器 -> 之后立刻查活性, 卡住就自救 resume。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
NAMES = ["browser_aliases", "browser_batch", "browser_create_tab",
         "browser_debugger_pause", "browser_task_runner_post"]


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    except Exception as ex:
        return None, 'HTTP层异常: %r' % (ex,)
    rr = o.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text")
    if not txt and o.get("error"):
        txt = json.dumps(o["error"], ensure_ascii=False)
    return bool(rr.get("isError")), txt.replace('\\"', '"')


for n in NAMES:
    e, t = call(n)
    verdict = '?'
    if t is None:
        verdict = '无法判定'
    elif ('未知命令' in t) or ('没有该工具' in t) or ('Unknown' in t):
        verdict = '★真幽灵(路由无实现)'
    elif e:
        verdict = '有实现(明确报错/守卫)'
    else:
        verdict = '有实现(正常回包)'
    print('%-34s isError=%-5s %s' % (n, e, verdict))
    print('    %s' % (t or '')[:260])

print('\n-- 活性检查(debugger_pause 可能暂停调试器) --')
e, t = call("browser_status", {}, 30)
print('browser_status isError=%s %s' % (e, (t or '')[:200]))
if t and '"paused":true' in t.replace(' ', ''):
    print('!! 调试器处于暂停态, 自救: Debugger.resume')
    e2, t2 = call("browser_cdp_call", {"method": "Debugger.resume", "params": {}}, 30)
    print('   resume isError=%s %s' % (e2, (t2 or '')[:200]))
    e3, t3 = call("browser_status", {}, 30)
    print('   复查 browser_status isError=%s %s' % (e3, (t3 or '')[:120]))
