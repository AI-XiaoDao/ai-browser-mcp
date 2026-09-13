# -*- coding: utf-8 -*-
r"""验证"Input 域 5s 成本 = 浏览器窗口不可见/被遮挡(渲染器后台化)"这一假设。

被发现的现象(实测, 可复现但**逐实例随机**): 某些实例里每一条 Input 域命令(Input.dispatchMouseEvent)
稳定 ~5.1s; 同实例里 Runtime.evaluate / 直发其它域只要 0.03s。三轮截断前缀实验中, 同一脚本
一次全慢(5.07/5.08/5.16s)、一次全快(0.03/0.01/0.01s) ⇒ 成本属于"实例状态", 不属于某个工具的副作用。

本脚本用**可控手段**制造/解除该状态: 隐藏窗口 → 量 Input; 显示窗口 → 再量。
判据: 隐藏后变 ~5s 且显示后立刻回到 0.03s ⇒ 状态=窗口可见性(渲染器后台化), 与我们的封装无关。
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


def times(tag, n=2):
    out = []
    for i in range(n):
        e, t, dt = call("browser_mouse_move", {"x": 200 + i * 4, "y": 150 + i * 4})
        out.append(dt)
    e, t, dt = call("browser_execute_js", {"code": "1+1"})
    print('   %-26s Input=%s | Runtime=%.2fs' % (tag, [round(x, 2) for x in out], dt))
    return out


print('== ① 当前状态基线 ==')
base = times('隐藏前')

print('\n== ② 隐藏浏览器窗口(渲染器应被后台化) ==')
e, t, dt = call("browser_show_window", {"visible": False})
print('   show_window(false): %.2fs err=%s %s' % (dt, e, t.replace('\n', ' ')[:110]))
time.sleep(1.5)
hid = times('隐藏后')

print('\n== ③ 显示回来 ==')
e, t, dt = call("browser_show_window", {"visible": True})
print('   show_window(true): %.2fs err=%s %s' % (dt, e, t.replace('\n', ' ')[:110]))
time.sleep(1.5)
shown = times('显示后')

print('\n== ④ 再次隐藏, 复现性确认 ==')
call("browser_show_window", {"visible": False})
time.sleep(1.5)
hid2 = times('再次隐藏')
call("browser_show_window", {"visible": True})
time.sleep(1.0)
back = times('恢复显示')

print('\n汇总: 基线=%s 隐藏=%s 显示=%s 再隐藏=%s 恢复=%s'
      % tuple([round(x, 2) for x in g] for g in (base, hid, shown, hid2, back)))
if max(hid) >= 3.0 and max(shown) < 3.0:
    print('判读: **假设成立** —— 窗口隐藏时 Input 域每条命令 ~5s, 一旦显示回来立即回到 0.03s')
    print('      ⇒ 快检那条臂的偶发 5s 是"窗口被遮挡/后台化"的实例状态, 不是派发代码缺陷, 也不是通道损坏。')
elif max(hid) < 3.0 and max(base) >= 3.0:
    print('判读: 当前实例本来慢, 隐藏反而快 —— 与可见性假设不符, 需另找变量')
elif max(base) >= 3.0 and max(hid) >= 3.0:
    print('判读: 隐藏前后都慢 ⇒ 该实例处于"慢"状态且与可见性无关(或隐藏不是充分条件)')
else:
    print('判读: 隐藏未复现慢态 ⇒ 可见性不是成因(或需要真正的"被其它窗口遮挡/最小化"而非隐藏)')
