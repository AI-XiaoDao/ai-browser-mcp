# -*- coding: utf-8 -*-
r"""实测: 原生右键菜单打开后, 哪些手段能把它关掉(判据 = 之后再 arm 能否重新捕获到快照)。

背景: `browser_menu_probe` 第一次 arm 必成功(0.3s 拿到 17 项), 但第二次起 100% 失败 ——
成因是原生菜单仍开着, 新的 CDP 右键只会被它吞掉, 不再触发 `即将打开菜单`。
CDP 的 Escape(Input.dispatchKeyEvent 走渲染器)**不足以**关掉原生菜单(已实测)。

本脚本逐个试: ①VIP/CEF 键盘事件 ②CDP 左键点页面 ③CDP 鼠标移动+左键 ④再次 CDP Escape
每试完一次紧跟一次 arm, 看是否重新捕获(能捕获 = 该手段有效)。

用法: py -3 _audit\probe_menu_dismiss.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def arm_ok():
    """arm 一次; 能拿到 declared_count 即说明"新的菜单确实开了"(旧菜单已被关掉)。"""
    e, t, d = call("browser_menu_probe", {"action": "arm", "x": 220, "y": 160}, to=60)
    has = "declared_count" in t
    return has, e, d, t[:80]


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?dm=%d" % int(time.time())})

print('\n[基线] 第一次 arm(应为成功)')
ok, e, d, msg = arm_ok()
print('    arm#1 -> 捕获=%s isError=%s %.2fs' % (ok, e, d))
if not ok:
    print('    !! 基线就没成功, 后续结论无意义'); sys.exit(1)

print('\n[对照] 不做任何清场, 直接再 arm(应失败 —— 证明菜单确实还开着)')
ok, e, d, msg = arm_ok()
print('    arm#2(无清场) -> 捕获=%s isErr=%s %.2fs' % (ok, e, d))

TRIALS = [
    ("VIP/CEF 键盘 Esc(keyup)", lambda: call("browser_key_event", {"key_code": 27, "type": "keyup"}, to=30)),
    ("VIP/CEF 键盘 Esc(keydown+keyup)", lambda: (call("browser_key_event", {"key_code": 27, "type": "keydown"}, to=30),
                                                call("browser_key_event", {"key_code": 27, "type": "keyup"}, to=30))),
    ("CDP 左键点页面 (400,400)", lambda: call("browser_mouse_click", {"x": 400, "y": 400, "button": "left"}, to=30)),
    ("CDP 移到(400,400) 再左键", lambda: (call("browser_mouse_move", {"x": 400, "y": 400}, to=30),
                                       call("browser_mouse_click", {"x": 400, "y": 400, "button": "left"}, to=30))),
    ("CDP 中键点击页面", lambda: call("browser_mouse_click", {"x": 420, "y": 420, "button": "middle"}, to=30)),
    ("页面 JS: window.focus()", lambda: call("browser_execute_js", {"code": "window.focus();document.body.click();'ok'"}, to=30)),
]

for name, act in TRIALS:
    e0, t0, d0 = (act() if not isinstance(act(), tuple) else act()[0]) if False else (None, None, None)
    # 执行清场动作
    r = act()
    if isinstance(r, tuple):
        pass
    time.sleep(0.35)
    ok, e, d, msg = arm_ok()
    print('    %-32s -> arm 捕获=%s (%.2fs) %s' % (name, ok, d, "" if ok else "❌ 仍未关掉"))
    if ok:
        print('       ✅ 有效清场手段: %s' % name)
        # 找到有效手段就再确认一次可重复性
        time.sleep(0.3)
        ok2, e2, d2, _ = arm_ok()
        print('       复现性: 清场后再次 arm 捕获=%s' % ok2)
        break

print('\n== 收尾 ==')
e, t, d = call("browser_status", {}, to=30)
print('    browser_status isError=%s %.2fs' % (e, d))
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=30)
print('    execute_js isError=%s %.2fs(CDP 通道是否还健康)' % (e, d))
