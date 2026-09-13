# -*- coding: utf-8 -*-
"""仪表判读跑: 用**列位正确**的规格, 看 last_error(仪表通道) 与 apply_failed 分别是什么。

规格:
    item|自建A|0|1|0|            -> 26501
    relabel|改后的名字|26501|1|0|  -> 自建项改名(标签在第2列) -> 应成功
    accel||26501|1|0|70C|         -> 自建项加 Ctrl+R(快捷键在第6列) -> 应成功
    relabel|默认新名|reload|1|0|   -> 默认项改名 -> 应失败
    relabel|不存在|27999|1|0|      -> 不存在的ID -> 应失败
预期 applied=3, 失败 2 条。
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
SPEC = "\n".join([
    "item|自建普通|0|1|0|",
    "check|自建勾选|0|0|0|",
    "dis||26501|1|0|",
    "vis||26501|0|0|",
    "relabel|改名了|26502|1|0|",
    "mark||26502|1|0|",
    "accel||26502|1|0|70C|",
    "relabel|想改默认|reload|1|0|",
    "relabel|不存在|27999|1|0|",
])
# 另加一条**故意错列位**的规格(7 段), 应在 set 阶段就被明确拒绝
BAD_SPEC = "relabel||26502|改名了|1|0|"


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
call("browser_navigate", {"url": "https://example.com/?inst=1", "wait_for_load": True}, 90)
time.sleep(1.0)
eb, tb = call("browser_context_menu", {"action": "set", "items": BAD_SPEC})
print('错列位规格: isError=%s | %s' % (eb, flat(tb)[:320]))
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print('set  isError=%s warnings=%s' % (e, flat(t)[flat(t).find('warnings'):][:200]))
for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
    call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                             "params": {"type": typ, "x": 130, "y": 130,
                                        "button": "right", "clickCount": 1,
                                        "buttons": btn}}, 40)
time.sleep(2.0)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
for k in ('apply_count', 'last_applied_items', 'menu_item_count', 'verified_items'):
    m = re.search(r'"%s":(\d+)' % k, f)
    print('   %-20s %s' % (k, m.group(1) if m else '?'))
for k in ('verify_mismatch', 'apply_failed', 'last_error'):
    m = re.search(r'"%s":"([^"]*)"' % k, f)
    print('   %-20s %r' % (k, m.group(1) if m else None))
call("browser_context_menu", {"action": "clear"})
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
