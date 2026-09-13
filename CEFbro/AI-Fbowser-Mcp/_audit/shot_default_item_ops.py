# -*- coding: utf-8 -*-
"""默认项上还有没有**能用**的修改类操作? 决定工具文案该怎么写。

矩阵已证: 默认项(标准ID 102)上 relabel / vis / dis **都返回假**。
本实验专门看另外两类(它们不走同一个 bool 门):
  arm_del_def     del||reload|1|0|      重新加载 是否**整条消失**?
  arm_noaccel_def noaccel||reload|1|0|  重新加载 后面的 "Ctrl+R" 提示是否消失?
每臂一次右键一次进程。
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

from PIL import ImageGrab

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
SHOTS = os.path.join(ROOT, '_audit', 'shots')
CROP = (100, 150, 700, 780)

ARMS = [
    ("del_default", "del||reload|1|0|"),
    ("noaccel_default", "noaccel||reload|1|0|"),
]


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


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)


os.makedirs(SHOTS, exist_ok=True)
for label, spec in ARMS:
    print('\n== %s : %s ==' % (label, spec))
    kill()
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
    call("browser_navigate", {"url": "https://example.com/?d=%s" % label,
                              "wait_for_load": True}, 90)
    time.sleep(1.0)
    e, t = call("browser_context_menu", {"action": "set", "items": spec})
    if e:
        print('   set 失败: %s' % flat(t)[:200])
        kill()
        continue
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": 130, "y": 130,
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)
    time.sleep(2.0)
    e, t = call("browser_context_menu", {"action": "get"})
    f = flat(t)
    out = {}
    for k in ('apply_count', 'last_applied_items', 'menu_item_count'):
        m = re.search(r'"%s":(\d+)' % k, f)
        out[k] = m.group(1) if m else '?'
    print('   apply=%s applied=%s items=%s' % (out['apply_count'],
          out['last_applied_items'], out['menu_item_count']))
    p = os.path.join(SHOTS, label + '_crop.png')
    try:
        im = ImageGrab.grab()
        im.crop(CROP).save(p)
        print('   截图 %s' % p)
    except Exception as ex:
        print('   截图失败: %s' % ex)
    kill()
print('\n== 完 ==')
