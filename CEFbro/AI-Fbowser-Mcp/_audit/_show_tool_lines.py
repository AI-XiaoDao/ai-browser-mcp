# -*- coding: utf-8 -*-
r"""按工具名打印 src/MCP_Server.wsv 里的注册行原文(供校准 schema/描述补丁)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = sys.argv[1:] or [
    "browser_vip_enable_js_env", "browser_vip_touch_cancel", "browser_vip_touch_emulation",
    "browser_vip_fingerprint_ssl", "browser_fill_attr_get", "browser_fill_attr_set",
    "browser_fill_select", "browser_set_preference", "browser_vip_execute_js_context",
    "browser_fingerprint_languages", "browser_vip_mouse_wheel",
    "browser_vip_fingerprint_media_devices", "browser_get_global_cache_dir",
    "browser_send_message", "browser_get_run_style",
]
lines = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')
for t in TOOLS:
    hits = [(i + 1, ln) for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % t) in ln]
    print('=' * 100)
    if not hits:
        print('%s: 未找到注册行' % t)
        continue
    for no, ln in hits:
        print('%s  (LINE %d)' % (t, no))
        print(ln.strip())
