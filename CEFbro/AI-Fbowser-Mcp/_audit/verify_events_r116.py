# -*- coding: utf-8 -*-
"""事件补齐验收(自动发现新增事件名, 不需要人工填空)。

流程:
 ① 对比 `_audit/_event_names_before.txt` 与 `_event_names_after.txt` → 得到**本次新增的事件名**;
 ② 先把 26+2 个开关全开(用 browser_kernel_events_all action=enable, 并读 action=get 观测);
 ③ 制造事件: 导航(产生 URL 请求/载入/资源) + 打开调试器(可能触发 DevTools 附加);
 ④ 逐个新事件名查 `browser_event` —— 有记录=已接线并真的回调; 无记录=打印原文(可能是"本机不触发",
    例如离屏渲染/证书/进程间消息在窗口内嵌渲染模式下不会发生, 这不算功能缺陷, 但必须如实记录);
 ⑤ 回归对照: 老事件(load_end/resource_*)必须仍有记录。
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
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def names_of(tag):
    p = os.path.join(ROOT, '_audit', '_event_names_%s.txt' % tag)
    if not os.path.exists(p):
        print('!! 缺 %s —— 请先运行 snapshot_event_names.py %s' % (p, tag))
        return None
    out = {}
    for ln in open(p, encoding='utf-8').read().split('\n'):
        if '\t' in ln:
            k, v = ln.split('\t', 1)
            out[k] = v
    return out


before, after = names_of('before'), names_of('after')
if before is None or after is None:
    sys.exit(1)
NEW = sorted(set(after) - set(before))
GONE = sorted(set(before) - set(after))
print('基线事件名 %d, 现在 %d, 新增 %d, 消失 %d' % (len(before), len(after), len(NEW), len(GONE)))
print('新增: %s' % NEW)
if GONE:
    print('★消失(需查是否改名/误删): %s' % GONE)

print('\n== 开全部监控 ==')
e, t = call("browser_kernel_events_all", {"action": "enable"})
print('   enable: %s' % t[:160])
e, t = call("browser_kernel_events_all", {"action": "get"})
m = re.search(r'"enabled_count":(\d+)', t)
print('   观测 enabled_count = %s' % (m.group(1) if m else '?'))

print('\n== 制造事件: 导航 + 打开调试器 ==')
for url in ("https://example.com/?ev116=a", "https://example.com/?ev116=b"):
    call("browser_navigate", {"url": url, "wait_for_load": True})
    time.sleep(0.6)
call("browser_debugger_enable", {}, 40)
time.sleep(1.0)
# 触发一次媒体访问请求(可能触发"即将改变媒体访问"/许可提示族)
call("browser_execute_js", {"code": "navigator.mediaDevices&&navigator.mediaDevices.getUserMedia?"
                                    "navigator.mediaDevices.getUserMedia({audio:true}).catch(function(){})"
                                    ":null"}, 30)
time.sleep(1.5)

print('\n== 逐个新事件查询 ==')
hits, misses = [], []
for nm in NEW:
    e, t = call("browser_event", {"event_type": nm}, 40)
    n = len(re.findall(r'"event":"%s"' % re.escape(nm), t))
    if n > 0:
        hits.append(nm)
        print('   [有记录] %-32s %d 条' % (nm, n))
    else:
        misses.append(nm)
        print('   [无记录] %-32s %s' % (nm, t[:150]))

print('\n== 回归对照(老事件必须仍有记录) ==')
for nm in ('load_end', 'resource_*'):
    e, t = call("browser_event", {"event_type": nm}, 40)
    ok = len(t) > 30 and ('未找到' not in t)
    print('   [%s] browser_event(%s) -> %s' % ('OK' if ok else '★FAIL', nm, t[:140]))

print('\n==== 汇总 ====')
print('新增事件名 %d 个: 有记录 %d, 无记录 %d' % (len(NEW), len(hits), len(misses)))
print('有记录: %s' % hits)
print('无记录: %s  <- 逐个判断是"本机不触发"还是"没接上"(见上面原文)' % misses)
call("browser_collect", {"action": "event_all_disable"})
