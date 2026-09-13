# -*- coding: utf-8 -*-
r"""重启 MCP 实例: 可见控制台窗口(用户调试期现场看) + 应用自写 mcp_console.log。
复用 cold_matrix.cold_restart(已接入可见控制台启动), 重启后打印日志尾段。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import _app_launch
import cold_matrix as CM

h = CM.cold_restart()
print('重启完成: %s' % (h if h else '未就绪!'))
print('-- mcp_console.log 尾段 --')
for ln in _app_launch.read_log(15):
    print('  | ' + ln[:110])
