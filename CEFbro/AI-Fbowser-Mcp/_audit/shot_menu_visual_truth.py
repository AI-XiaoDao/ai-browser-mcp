# -*- coding: utf-8 -*-
"""可视真值实验(3 臂): 用**自建项**的屏幕外观判定语义, 并检验默认项到底能不能改。

矩阵实验已给出:
  · 自建普通项: 置禁止(真) 后 是否禁止 读 F; 置禁止(假) 后 读 T  -> setter/getter 互为反义
  · 自建勾选项: 选中(真) 后 是否选中 读 T; 选中(假) 后 读 F       -> 选中链正常
  · 默认项 102: 置可见(真)/置禁止(真) **本身就返回 F**           -> 默认项改不动(至少这两类)
需要与命名无关的观测量来定案:
  arm_disable_our   item|自建禁用项|0|1|0| + dis||26501|1|0|    自建项是否**变灰**?
  arm_check_our     check|自建勾选项|0|0|0| + mark||26502|1|0|   自建项是否出现**勾**?
  arm_relabel_def   relabel|改名测试|reload|1|0|                 默认项标签是否**真的改了**?
每臂一次右键一次进程(原生菜单无法用 CDP 关闭)。
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
    ("vis_disable_our", "item|自建禁用项|0|1|0|\ndis||26501|1|0|"),
    ("vis_check_our", "check|自建勾选项|0|0|0|\nmark||26502|1|0|"),
    ("vis_relabel_def", "relabel|改名测试|reload|1|0|"),
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
    print('\n== %s ==' % label)
    for ln in spec.split('\n'):
        print('   spec: %s' % ln)
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
    call("browser_navigate", {"url": "https://example.com/?v=%s" % label,
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
    got = {}
    for k in ('apply_count', 'last_applied_items', 'menu_item_count', 'verified_items'):
        m = re.search(r'"%s":(\d+)' % k, f)
        got[k] = m.group(1) if m else '?'
    mis = re.search(r'"verify_mismatch":"([^"]*)"', f)
    err = re.search(r'"last_error":"([^"]*)"', f)
    print('   apply=%s applied=%s items=%s verified=%s' % (got['apply_count'],
          got['last_applied_items'], got['menu_item_count'], got['verified_items']))
    print('   mismatch=%r  last_error=%r' % (mis.group(1) if mis else None,
                                             err.group(1) if err else None))
    p = os.path.join(SHOTS, label + '.png')
    pc = os.path.join(SHOTS, label + '_crop.png')
    try:
        im = ImageGrab.grab()
        im.save(p)
        im.crop(CROP).save(pc)
        print('   截图 %s' % pc)
    except Exception as ex:
        print('   截图失败: %s' % ex)
    kill()
print('\n== 完 ==')
