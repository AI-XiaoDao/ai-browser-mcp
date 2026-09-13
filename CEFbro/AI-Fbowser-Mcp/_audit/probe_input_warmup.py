# -*- coding: utf-8 -*-
r"""Input 域"首次唤醒"成本定位(自动重启, 保证本会话第一条 Input 命令就是被测对象)。

用例分组:
  A. 本会话**第一条** Input 命令用**直发** browser_cdp_call 发出 —— 若它也要 ~5s, 说明唤醒成本
     属于 CEF Input 域本身, 与我们的封装无关; 若它 0.03s, 说明唤醒成本出在我们的封装/等待链。
  B. 紧接着封装 browser_mouse_move ×3 —— 看是否已被 A 预热(全 0.03s)还是仍要付一次。
  C. 页面重新载入后, 封装 mouse_move ×2 —— 验证"导航是否重置唤醒状态"(决定快检用例该怎么写)。
  D. 空闲 30s 后再调一次 —— 验证"长时间空闲是否重新计费"(决定是否与窗口后台/节流有关)。

设计约束: 全部只碰主浏览器(example.com), 不改标签页集合, 便于后续用例复用。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop  # 复用其 kill_app/start_app(含 8s 稳定期)

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
    print('   %-38s %6.2fs err=%-5s %s' % (label, dt, e, t.replace('\n', ' ')[:60]))
    return dt


print('== 重启实例(保证本会话还没有任何 Input 命令) ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)

print('\n-- A: 本会话第一条 Input 命令 = 直发 CDP --')
a1 = show('cdp_call Input.mouseMoved(第一条 Input)', "browser_cdp_call",
          {"method": "Input.dispatchMouseEvent",
           "params": "{\"type\":\"mouseMoved\",\"x\":100,\"y\":100,\"buttons\":0}"})
a2 = show('cdp_call Input.mouseMoved(第二条)', "browser_cdp_call",
          {"method": "Input.dispatchMouseEvent",
           "params": "{\"type\":\"mouseMoved\",\"x\":110,\"y\":110,\"buttons\":0}"})

print('\n-- B: 封装 mouse_move ×3(看 A 是否已预热) --')
b = [show('mouse_move #%d(封装)' % i, "browser_mouse_move", {"x": 120 + i * 5, "y": 130 + i * 5})
     for i in range(1, 4)]

print('\n-- C: 页面重新载入后 --')
show('navigate(重载 example.com)', "browser_navigate", {"url": "https://example.com/"})
time.sleep(1.5)
c = [show('mouse_move #%d(载入后)' % i, "browser_mouse_move", {"x": 200 + i * 5, "y": 210 + i * 5})
     for i in range(1, 3)]

print('\n-- D: 空闲 30s 后 --')
time.sleep(30)
d = [show('mouse_move(空闲后)', "browser_mouse_move", {"x": 250, "y": 260})]

print('\n== 收尾健康 ==')
show('execute_js', "browser_execute_js", {"code": "1+1"})
show('get_url', "browser_get_url", {})

print('\n汇总: A=%s' % [round(x, 2) for x in (a1, a2)])
print('      B=%s' % [round(x, 2) for x in b])
print('      C(重载后)=%s' % [round(x, 2) for x in c])
print('      D(空闲后)=%s' % [round(x, 2) for x in d])
if a1 >= 3.0:
    print('判读: 直发第一条 Input 也慢 ⇒ 唤醒成本在 CEF Input 域本身(与封装无关), 快检用例应改为"预热后测稳态"')
elif max(b + c + d) < 3.0:
    print('判读: 直发首条快、封装也快 ⇒ 唤醒成本由**直发**承担; 说明封装不是瓶颈, 快检用例可直接断言 <3s')
else:
    print('判读: 直发首条快但封装某组仍慢 ⇒ 逐步看 B/C/D 哪一组慢(导航后? 空闲后?)')
