# -*- coding: utf-8 -*-
"""把 event_*_enable 成功消息里列出的**应用事件**类型名补上 app_ 前缀,
使 AI 被指引去查询的名字与实际落库名字一致（否则查出来是"未找到应用事件"）。
浏览器事件（menu/quickmenu/navintent/ui/permission）不加前缀。

按新规则：改 .wsv 字符串一律用 .py 文件, 不用 shell 内联脚本（避免 \\" 被 shell 吃掉）。
"""
import io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv"
t = io.open(P, encoding="utf-8").read()

REPS = [
    ("event_extension_enable",
     "插件生命周期监控已启用 (extension_created/create_failed/loaded/unloaded)",
     "插件生命周期监控已启用 (查询用 app_extension_created / app_extension_create_failed / app_extension_loaded / app_extension_unloaded)"),
    ("event_startup_enable",
     "启动流程监控已启用 (startup_request_context_ready/cmdline/child_process/message_pump/webkit_init)",
     "启动流程监控已启用 (查询用 app_startup_request_context_ready / app_startup_cmdline / app_startup_child_process / app_startup_message_pump / app_startup_webkit_init)。注意: 该类事件在进程启动时触发, 开启监控**之后**的启动阶段才会被记录"),
    ("event_render_enable",
     "渲染细节监控已启用 (render_v8_context_created/message_received/loading_state/load_start/load_end)",
     "渲染细节监控已启用 (查询用 app_render_v8_context_created / app_render_message_received / app_render_loading_state / app_render_load_start / app_render_load_end)。注意: 本类事件由 CEF 渲染进程触发, 窗口内嵌渲染模式下是否回调以内核为准"),
    ("event_renderws_enable",
     "渲染侧WebSocket监控已启用 (render_ws_created/closed/connect/recv/send)",
     "渲染侧WebSocket监控已启用 (查询用 app_render_ws_created / app_render_ws_closed / app_render_ws_connect / app_render_ws_recv / app_render_ws_send)"),
]

n = 0
for act, old, new in REPS:
    c = t.count(old)
    print("  %-28s 命中 %d" % (act, c))
    t = t.replace(old, new)
    n += c

io.open(P, "wb").write(t.encode("utf-8"))
print("合计替换: %d" % n)
