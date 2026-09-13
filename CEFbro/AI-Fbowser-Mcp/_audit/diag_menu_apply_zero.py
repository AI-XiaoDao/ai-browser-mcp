# -*- coding: utf-8 -*-
"""单臂仪表化: 为什么这一轮的右键回调 applied=0(而上一轮是 2)?

上一轮(diag_menu_readback_semantics)同样流程却 applied=2, 本轮 3 条臂全是 0,
截图上菜单显示的是**默认标签**(重新加载)而不是我预置的标签 -> 规格确实没被施加。
逐一排查: set 的完整回包 / 事件监控状态 / set 后等待时间 / 右键后等待时间 / 二次右键。
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
SPEC = "relabel|改过名的刷新|reload|1|0|"


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def flat(t):
    return t.replace('\\"', '"')


def hwnd_rightclick():
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": 130, "y": 130,
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
        time.sleep(4.5)
        break
    except Exception:
        pass

call("browser_navigate", {"url": "https://example.com/?probe=1", "wait_for_load": True}, 90)
time.sleep(1.0)

print('== 1) set 的完整回包 ==')
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print('   isError=%s\n   %s' % (e, flat(t)[:600]))

print('\n== 2) set 之后等 3 秒, 再查一次 get(看规格是否还在/监控是否开) ==')
time.sleep(3.0)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
print('   %s' % f[:600])

print('\n== 3) 第一次右键 + 等 2.5 秒 ==')
hwnd_rightclick()
time.sleep(2.5)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
for k in ('apply_count', 'last_applied_items', 'menu_item_count', 'verified_items',
          'last_error', 'event_monitor', 'enabled'):
    m = re.search(r'"%s":("[^"]*"|\d+|true|false)' % k, f)
    print('   %-20s %s' % (k, m.group(1) if m else '(缺)'))
print('   verify_mismatch=%s' % (re.search(r'"verify_mismatch":"([^"]*)"', f).group(1)
                                 if '"verify_mismatch"' in f else '(缺)'))

print('\n== 4) 再一次右键(菜单已开, 看是否重复触发) + 等 2.5 秒 ==')
hwnd_rightclick()
time.sleep(2.5)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
for k in ('apply_count', 'last_applied_items', 'menu_item_count', 'verified_items',
          'last_error'):
    m = re.search(r'"%s":("[^"]*"|\d+|true|false)' % k, f)
    print('   %-20s %s' % (k, m.group(1) if m else '(缺)'))
print('   verify_mismatch=%s' % (re.search(r'"verify_mismatch":"([^"]*)"', f).group(1)
                                 if '"verify_mismatch"' in f else '(缺)'))
