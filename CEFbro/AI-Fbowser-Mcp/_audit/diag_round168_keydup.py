# -*- coding: utf-8 -*-
r"""第 168 轮: 按键重复派发定位 —— 用 browser_cdp 直通 Input.dispatchKeyEvent 对照。
若直通 1 次而 browser_key_event 2 次 => 重复在我方助手/执行CDP并同步等待 路径。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM


def call(name, args, timeout=20):
    return CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                         'params': {'name': name, 'arguments': args}}, timeout)


def text_of(r):
    return ''.join((c.get('text') or '') for c in
                   ((r.get('result') or {}).get('content') or []))


JS = ("window.__kd=0;"
      "document.addEventListener('keydown',function(e){window.__kd++})")
print('装监听:', text_of(call('browser_execute_js', {'code': JS, 'max_ms': 5000}))[:50])

# ① CDP 直通一次 keyDown
params = {"type": "keyDown", "key": "A", "code": "KeyA", "windowsVirtualKeyCode": 65,
          "nativeVirtualKeyCode": 65, "modifiers": 0, "text": "A", "unmodifiedText": "A"}
r1 = call('browser_cdp', {'method': 'Input.dispatchKeyEvent', 'params': params})
print('直通 ->', text_of(r1)[:80])
print('计数(直通):', text_of(call('browser_execute_js',
                              {'code': 'String(window.__kd)', 'max_ms': 5000}))[:60])

# ② 复位后走 browser_key_event 一次
print('复位:', text_of(call('browser_execute_js', {'code': 'window.__kd=0', 'max_ms': 5000}))[:50])
r2 = call('browser_key_event', {'key_code': 65, 'type': 'keydown'})
print('key_event ->', text_of(r2)[:80])
print('计数(助手):', text_of(call('browser_execute_js',
                              {'code': 'String(window.__kd)', 'max_ms': 5000}))[:60])
