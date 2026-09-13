# -*- coding: utf-8 -*-
"""验收"右键上下文"(类_FBrowser_菜单环境)消费 —— 每次**只右键一次**、每个目标一个全新进程。

为什么这么设计: 右键会弹出**原生 OS 菜单**, 而 CDP 的键盘/鼠标事件只到渲染进程,
**关不掉那个原生菜单** —— 于是同一进程里连续两次右键, 第二次只会"关掉菜单"而不产生新的
context_menu_opening 事件(第一版验收拿到的是**同一条**事件, timestamp_ms 完全相同)。
故改为: 一次运行只测一个目标, 用两个干净会话做**对照**。

用法: py -3 verify_menu_env.py link   # 右键链接 -> link 应非空
      py -3 verify_menu_env.py text   # 右键纯文本 -> link 应为空
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

TARGET = (sys.argv[1] if len(sys.argv) > 1 else 'link').lower()
SEL = {'link': 'a', 'text': 'h1'}.get(TARGET)
if SEL is None:
    print('用法: verify_menu_env.py link|text')
    sys.exit(2)

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
URL = "https://example.com/?menuenv=1"
R = []


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


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:300])


def right_click(x, y):
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": int(x), "y": int(y),
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)
    time.sleep(1.2)


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": URL, "wait_for_load": True}, 90)
time.sleep(0.6)
call("browser_collect", {"action": "event_menu_enable"}, 40)

e, t = call("browser_dom_rect", {"selector": SEL}, 40)
u = t.replace('\\"', '"')
m = re.search(r'"left":([\d.]+),"top":([\d.]+),"width":([\d.]+),"height":([\d.]+)', u)
if not m:
    print('!! 取不到 %s 的坐标: %s' % (SEL, t[:200]))
    sys.exit(1)
L, T, W, H = (float(m.group(i)) for i in (1, 2, 3, 4))
cx, cy = int(L + W / 2), int(T + H / 2)
print("== 目标=%s (%s) 中心坐标=(%d,%d) ==" % (TARGET, SEL, cx, cy))

right_click(cx, cy)
e, t = call("browser_event", {"event_type": "context_menu_opening", "limit": 3}, 40)
d = t.replace('\\"', '"')
print("   事件载荷: %s" % d[:640])

arm("产生了 context_menu_opening 事件", 'context_menu_opening' in d, d[:200])
arm("available=true(菜单环境对象有效)", '"available":true' in d, d[:200])
arm("带上了坐标 x/y", ('"x":%d' % cx) in d and ('"y":%d' % cy) in d, d[:260])
arm("page_url 是当前页", 'menuenv=1' in d, d[:200])
if TARGET == 'link':
    arm("★右键**链接** -> link 非空(含 iana.org)", 'iana.org' in d, d[:300])
    arm("type_flags 反映链接上下文(非0)", '"type_flags":0' not in d, d[:200])
else:
    arm("★右键**纯文本** -> link 为空(与链接臂对照)", '"link":""' in d, d[:300])

call("browser_collect", {"action": "event_all_disable"}, 40)
ok = sum(1 for _, v in R if v)
print("\n==== [%s] 结果: %d/%d 通过 ====" % (TARGET, ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
