# -*- coding: utf-8 -*-
r"""单臂复核: **无 beforeunload** 的副浏览器, try_close:true 到底能不能真正发起关闭?

前一次运行里该臂也报了"关闭未开始", 若复核一致 => 本机(控制台程序, 无顶层窗口关闭处理器)
对主/副浏览器调用 TryCloseBrowser **都返回假**, 即该参数在当前架构下不会真正发起关闭。
类库注释原文正是 "Call this method from the top-level window close handler"(FBroLib.wsv:797),
与本实测吻合。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


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
                                            if i.get("type") == "text")


def ids():
    try:
        return [b.get('id') for b in (json.loads(call("browser_list", {})[1]).get('browsers') or [])]
    except Exception:
        return []


before = set(ids())
call("browser_create", {"url": "https://example.com/?tb=%d" % int(time.time()), "wait_for_load": True})
bid = None
for _ in range(20):
    time.sleep(0.4)
    add = set(ids()) - before
    if add:
        bid = sorted(add)[-1]
        break
print('副浏览器 id=%r (清单 %s)' % (bid, ids()))
print('页面是否有 beforeunload: %s' % call("browser_execute_js",
      {"code": "String(window.onbeforeunload)", "browser_id": bid})[1][:100])

e, t = call("browser_close", {"browser_id": bid, "try_close": True})
print('\ntry_close 回包: isError=%s\n   %s' % (e, t[:260]))
time.sleep(1.5)
print('调用后清单: %s -> 该浏览器 %s' % (ids(), '仍在' if bid in ids() else '已消失'))

# 对照: 同一浏览器用强制关闭
e2, t2 = call("browser_close", {"browser_id": bid})
print('\n强制关闭(无 try_close) 回包: isError=%s %s' % (e2, t2[:120]))
time.sleep(1.0)
print('清单: %s' % ids())
print('\n判读: %s' % ('try_close 在本机**不会发起关闭**(返回假); 只有强制关闭有效 —— 与类库注释'
                      '"从顶层窗口关闭处理器调用"一致(本项目是控制台程序, 没有该处理器)'
                      if e else 'try_close 能发起关闭'))
