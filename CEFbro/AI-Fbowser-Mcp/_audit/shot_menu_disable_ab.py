# -*- coding: utf-8 -*-
"""用**屏幕截图**判定 置禁止状态 的真实语义(不受中文名歧义影响)。

背景: 在回调内做 A/B 得到
    置禁止状态(id,真) -> 是否禁止 读 F
    置禁止状态(id,假) -> 是否禁止 读 T
两个假设都符合这组数据:
    甲) 置禁止=SetEnabled(!b) 且 是否禁止=IsEnabled        -> 工具**正确**, 是我的回读比对方程写错
    乙) 置禁止=SetEnabled(b)  且 是否禁止=!IsEnabled       -> 工具**语义反了**(说禁用其实启用)
要区分只能看**与命名无关的观测量**: 菜单项在屏幕上是否真的变灰。

三条臂(每条一次右键一次进程, 原生菜单无法用 CDP 关闭):
   arm_disable_true   dis|禁用刷新|reload|1|0|   期望(甲): 刷新项变灰; 期望(乙): 刷新项正常
   arm_disable_false  dis|禁用刷新|reload|0|0|   与上臂**恰好相反**才算有判别力
   arm_hide_find      vis|隐藏查找|find|0|0|     正对照: 查找项应**整条消失**, 用来证明截图法本身有效
"""
import json
import os
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

ARMS = [
    ("arm_disable_true", "dis|禁用刷新|reload|1|0|"),
    ("arm_disable_false", "dis|禁用刷新|reload|0|0|"),
    ("arm_hide_find", "vis|隐藏查找|find|0|0|"),
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
made = []
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
    call("browser_navigate", {"url": "https://example.com/?shot=%s" % label,
                              "wait_for_load": True}, 90)
    time.sleep(0.8)
    e, t = call("browser_context_menu", {"action": "set", "items": spec})
    if e:
        print('   set 失败: %s' % t[:200])
        continue
    # 右键 -> 原生菜单弹出
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": 130, "y": 130,
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)
    time.sleep(1.8)
    e, t = call("browser_context_menu", {"action": "get"})
    f = flat(t)
    import re
    app = re.search(r'"last_applied_items":(\d+)', f)
    mis = re.search(r'"verify_mismatch":"([^"]*)"', f)
    err = re.search(r'"last_error":"([^"]*)"', f)
    print('   applied=%s mismatch=%r last_error=%r'
          % (app.group(1) if app else '?', mis.group(1) if mis else None,
             err.group(1) if err else None))
    p = os.path.join(SHOTS, label + '.png')
    try:
        im = ImageGrab.grab()
        im.save(p)
        print('   截图 %s (%dx%d)' % (p, im.size[0], im.size[1]))
        made.append(p)
    except Exception as ex:
        print('   截图失败: %s' % ex)
    kill()

print('\n== 生成的截图 ==')
for p in made:
    print('   %s' % p)
