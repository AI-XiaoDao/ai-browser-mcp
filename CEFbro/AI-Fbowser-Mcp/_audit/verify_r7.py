# -*- coding: utf-8 -*-
"""用火山字符串词法逐字符扫描新增注册行, 确认字符串字面量闭合且无裸引号。"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import SRC
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

NEW = ["browser_kernel_ipc_queue", "browser_kernel_ipc_clear", "browser_kernel_cdp_monitor",
       "browser_kernel_reactor", "browser_kernel_watch", "browser_kernel_events_all",
       "browser_set_s5_proxy", "browser_vip_clear_s5_proxy", "browser_vip_mouse_click",
       "browser_vip_mouse_move", "browser_vip_mouse_wheel", "browser_vip_key_press",
       "browser_vip_key_release", "browser_vip_key_click"]


def scan(line):
    """返回 (是否闭合, 字面量列表)。火山字符串: "..." 内部 \\" 为转义引号, \\\\ 为转义反斜杠。"""
    lits, cur, i, in_str = [], [], 0, False
    closed = True
    while i < len(line):
        c = line[i]
        if in_str:
            if c == "\\" and i + 1 < len(line):
                cur.append(line[i + 1])
                i += 2
                continue
            if c == '"':
                lits.append("".join(cur))
                cur = []
                in_str = False
            else:
                cur.append(c)
        else:
            if c == '"':
                in_str = True
            elif c == "/" and line[i:i + 2] == "//":
                break
        i += 1
    if in_str:
        closed = False
    return closed, lits


path = os.path.join(SRC, "MCP_Server.wsv")
lines = io.open(path, encoding="utf-8").read().split("\n")
found, bad = 0, 0
for idx, l in enumerate(lines):
    s = l.strip()
    if not s.startswith('添加工具JSON (\"'):
        pass
    matched = None
    for nm in NEW:
        if s.startswith('添加工具JSON ("%s"' % nm):
            matched = nm
            break
    if not matched:
        continue
    found += 1
    ok, lits = scan(s)
    # schema 参数里 \"inputSchema\" 之类会被还原成真引号, 属正常
    stripped = [x for x in lits if "inputSchema" not in x]
    empty = [x for x in stripped if x.strip() == "" and "inputSchema" not in x]
    status = "OK " if ok and not empty else "!! "
    if not ok or empty:
        bad += 1
    print("  %sL%-6d %-32s 字面量=%2d  %s" % (status, idx + 1, matched, len(lits),
                                              "闭合" if ok else "!! 未闭合"))
    if len(stripped) >= 2:
        print("        描述: %s" % stripped[1][:96])

print()
print("新增注册行: %d / %d   问题行: %d" % (found, len(NEW), bad))
