# -*- coding: utf-8 -*-
r"""复现"mouse_move ~5s"的错误状态, 并在**该状态内**做分层对照:

期望用法(先制造状态, 再量): py -3 _audit\loop.py --nobuild  &&  py -3 _audit\probe_mouse_slow_state.py

分层对照的意义:
  · 直发 browser_cdp_call(Input.dispatchMouseEvent) 也慢 ⇒ 慢在 CEF/CDP 的 Input 域往返;
  · 直发快、封装慢 ⇒ 慢在我们自己的等待/异步结果落库(mouse 走 执行CDP并同步等待 + SQLite);
  · 同封装的 touch/key 也慢 ⇒ 与我们封装的共用件有关, 不是 Input 特有;
  · Runtime.evaluate 一直快 ⇒ CDP 通道本身健康(排除"通道被打死")。
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
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), dt


def show(label, n, a=None):
    e, t, dt = call(n, a)
    flag = '  <== 慢' if dt >= 3.0 else ''
    print('   %-32s %6.2fs err=%-5s %s%s'
          % (label, dt, e, t.replace('\n', ' ')[:70], flag))
    return dt, t


print('== 第1层: 封装鼠标(刚重启/刚跑完 fastcheck 后应是慢态) ==')
d1, _ = show('mouse_move #1(封装)', "browser_mouse_move", {"x": 300, "y": 200})
d2, _ = show('mouse_move #2(封装)', "browser_mouse_move", {"x": 305, "y": 205})

print('\n== 第2层: 绕过封装, 直发同一条 CDP ==')
d3, _ = show('cdp_call Runtime.evaluate', "browser_cdp_call",
             {"method": "Runtime.evaluate",
              "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"})
d4, _ = show('cdp_call Input.mouseMoved', "browser_cdp_call",
             {"method": "Input.dispatchMouseEvent",
              "params": "{\"type\":\"mouseMoved\",\"x\":310,\"y\":210,\"buttons\":0}"})
d5, _ = show('cdp_call Input.mouseMoved #2', "browser_cdp_call",
             {"method": "Input.dispatchMouseEvent",
              "params": "{\"type\":\"mouseMoved\",\"x\":315,\"y\":215,\"buttons\":0}"})

print('\n== 第3层: 直发之后, 封装是否变快(是否被"预热") ==')
d6, _ = show('mouse_move #3(封装, 直发之后)', "browser_mouse_move", {"x": 320, "y": 220})
d7, _ = show('mouse_move #4(封装, 直发之后)', "browser_mouse_move", {"x": 325, "y": 225})

print('\n== 第4层: 同封装的其它件 ==')
d8, _ = show('vip_touch_press', "browser_vip_touch_press", {"x": 300, "y": 200})
d9, _ = show('vip_touch_release', "browser_vip_touch_release", {})
d10, _ = show('reverse_input_cdp(key)', "browser_reverse_input_cdp",
              {"kind": "key", "type": "keyDown", "key": "a",
               "windows_virtual_key_code": 65})

print('\n== 第5层: 收尾健康 ==')
d11, _ = show('execute_js', "browser_execute_js", {"code": "1+1"})
d12, _ = show('get_url', "browser_get_url", {})

slow = [x for x in (d1, d2, d6, d7) if x >= 3.0]
print('\n汇总: 封装鼠标慢 %d/4 次; 直发 Input 最慢 %.2fs; Runtime 直发 %.2fs'
      % (len(slow), max(d4, d5), d3))
if len(slow) >= 1 and max(d4, d5) < 3.0:
    print('判读: **慢在封装件**(直发 CDP 同一方法仅 %.2fs) —— 不是 CEF/CDP Input 域的问题' % max(d4, d5))
elif len(slow) >= 1:
    print('判读: **慢在 CEF/CDP Input 域往返**(直发同方法也慢)')
else:
    print('判读: 本次未复现慢态(全部 <3s)')
