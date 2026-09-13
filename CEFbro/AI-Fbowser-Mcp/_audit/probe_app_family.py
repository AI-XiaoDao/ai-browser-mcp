# -*- coding: utf-8 -*-
r"""判定: 整个 `app_*` 族(不只渲染族)在本机是否真的拿不到事件。

手段: 打开 application 族监控 → 故意制造 ①未捕获JS异常(应触发 渲染_即将捕获异常) ②焦点变化 ③URL变化,
再看时间线里有没有任何 app_ 记录; 对照臂用已知会触发的 browser_event 族。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


call("browser_collect", {"action": "event_app_enable"})
call("browser_kernel_events_all", {"action": "enable"})   # 一次全开(含 app_ 各族)
print('已开启 app 族与全部事件族')

print('\n-- 触发: 未捕获JS异常 + 焦点元素变化 + URL变化 --')
print('   JS异常: %s' % call("browser_execute_js",
                            {"code": "setTimeout(function(){throw new Error('mcp-render-probe')},0);'ok'"})[1][:80])
call("browser_execute_js", {"code": "document.body.focus();'ok'"})
call("browser_navigate", {"url": "https://example.com/?appevt=%d" % int(time.time()), "wait_for_load": True})
time.sleep(4.0)

e, t = call("browser_event", {"limit": 300})
print('\n-- 时间线里出现的族前缀统计 --')
import re
fams = {}
for m in re.finditer(r'\\?"event\\?":\\?"([a-z_]+)\\?"', t):
    k = m.group(1)
    fam = k.split('_')[0] + ('_' + k.split('_')[1] if k.startswith('app_') else '')
    fams[fam] = fams.get(fam, 0) + 1
for k in sorted(fams, key=lambda x: -fams[x])[:14]:
    print('   %-18s %d' % (k, fams[k]))
has_app = [k for k in fams if k.startswith('app')]
print('\n判读: 时间线里 app* 族 = %s' % (has_app or '（一条都没有）'))

for et in ("app_v8_exception", "app_render_load_end", "app_focus_node_changed"):
    e2, t2 = call("browser_event", {"event_type": et, "limit": 5})
    print('   %-24s isError=%s %s' % (et, e2, t2[:110].replace('\n', ' ')))
