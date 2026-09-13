# -*- coding: utf-8 -*-
r"""定位 browser_mouse_move 的 5s 来自哪一层:
  ① 我的封装 CDP派发鼠标事件 → 执行CDP并同步等待
  ② 直接用 browser_cdp_call 发同一条 Input.dispatchMouseEvent(绕过封装)
  ③ 对比非 Input 域命令(Control/Runtime)与其它 Input 子命令
结论用法: ②也慢 ⇒ 慢在 CEF/CDP 的 Input 域本身(封装无罪); ①慢②快 ⇒ 慢在我们的等待/派发封装。
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


def cdp(method, params):
    e, t, dt = call("browser_cdp_call",
                    {"method": method, "params": json.dumps(params)})
    print('   %-32s %6.2fs err=%-5s %s' % (method, dt, e, t.replace('\n', ' ')[:90]))
    return dt


print('== ② 绕过封装: 直接 CDP ==')
cdp("Runtime.evaluate", {"expression": "1+1", "returnByValue": True})
cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 300, "y": 200, "buttons": 0})
cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 310, "y": 210, "buttons": 0})
# 按下/放开故意选页脚空白处(5,5), 避免点到 example.com 的链接导致导航(污染后续用例)
cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 5, "y": 5,
                                 "button": "left", "clickCount": 1})
cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 5, "y": 5,
                                 "button": "left", "clickCount": 1})
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "a",
                               "windowsVirtualKeyCode": 65})
cdp("Page.getFrameTree", {})
cdp("Runtime.evaluate", {"expression": "1+1", "returnByValue": True})

print('\n== ① 经过封装 ==')
e, t, dt = call("browser_mouse_move", {"x": 320, "y": 220})
print('   browser_mouse_move             %6.2fs err=%-5s %s' % (dt, e, t.replace('\n', ' ')[:80]))

print('\n== ③ 其它用同一封装的 CDP 工具(对照) ==')
for name, a in (("browser_vip_touch_press", {"x": 300, "y": 200}),
                ("browser_vip_touch_release", {}),
                ("browser_reverse_input_cdp", {"kind": "key", "type": "keyDown",
                                               "key": "a", "windows_virtual_key_code": 65})):
    e, t, dt = call(name, a)
    print('   %-30s %6.2fs err=%-5s %s' % (name, dt, e, t.replace('\n', ' ')[:80]))
