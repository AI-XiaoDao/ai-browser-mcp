# -*- coding: utf-8 -*-
"""取出待改写工具的注册行原文"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

TARGETS = [
    # debugger 家族
    "browser_debugger_enable", "browser_debugger_resume", "browser_debugger_stack",
    "browser_debugger_step_over", "browser_debugger_step_into", "browser_debugger_step_out",
    "browser_debugger_set_breakpoint", "browser_debugger_evaluate",
    "browser_debugger_flow", "browser_debugger_script_source",
    # edit 家族
    "browser_edit_undo", "browser_edit_redo", "browser_edit_cut", "browser_edit_copy",
    "browser_edit_paste", "browser_edit_delete", "browser_edit_select_all",
    # fill 家族
    "browser_fill_set_value", "browser_fill_click", "browser_fill_focus",
    "browser_fill_scroll", "browser_fill_exists", "browser_fill_attr_set",
    "browser_fill_attr_get", "browser_fill_trigger", "browser_fill_select",
    # 其余高频
    "browser_back", "browser_forward", "browser_find", "browser_download_image",
    "browser_is_loading", "browser_get_url", "browser_get_id", "browser_get_zoom",
    "browser_clear_cache", "browser_delete_cookies", "browser_create",
]

srv = lines_of("MCP_Server.wsv")[0]
found = {}
for i, l in enumerate(srv):
    m = re.search(r'添加工具JSON\s*\(\s*"([^"]+)"', l)
    if m and m.group(1) in TARGETS and m.group(1) not in found:
        found[m.group(1)] = (i + 1, l.rstrip())

print("目标 %d 个, 命中 %d 个" % (len(TARGETS), len(found)))
print()
for t in TARGETS:
    if t in found:
        ln, txt = found[t]
        print("%6d| %s" % (ln, txt[:400]))
    else:
        print("   ?? 未找到 %s" % t)
