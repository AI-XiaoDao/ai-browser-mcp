# -*- coding: utf-8 -*-
r"""全局枚举所有可见顶层窗口里的控制台类窗口(ConsoleWindowClass/ConhostHostWindow/
PseudoConsoleWindow), 报告归属进程名 —— 判断 AI-Fbowser-Mcp.exe 的控制台窗口是否真的
显示在桌面上(供用户现场看)。
"""
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

u = ctypes.windll.user32
k = ctypes.windll.kernel32
rows = []


@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
def cb(h, lp):
    cls = ctypes.create_unicode_buffer(200)
    u.GetClassNameW(h, cls, 200)
    c = cls.value
    if any(t in c for t in ('Console', 'Conhost', 'Pseudo')):
        wpid = ctypes.c_ulong()
        u.GetWindowThreadProcessId(h, ctypes.byref(wpid))
        buf = ctypes.create_unicode_buffer(300)
        u.GetWindowTextW(h, buf, 300)
        # 进程名
        pname = ''
        try:
            p = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, wpid.value)
            if p:
                nb = ctypes.create_unicode_buffer(300)
                sz = ctypes.c_ulong(300)
                if ctypes.windll.psapi.GetModuleBaseNameW(p, None, nb, sz):
                    pname = nb.value
                k.CloseHandle(p)
        except Exception:
            pname = '?'
        rows.append((h, c, buf.value, wpid.value, pname, bool(u.IsWindowVisible(h))))
    return True


u.EnumWindows(cb, 0)
print('控制台类窗口数 =', len(rows))
for h, c, t, pid, pname, v in rows:
    print('hwnd=%d 可见=%s 类=%s 进程=%s(pid=%d) 标题=%s' % (h, v, c, pname, pid, t[:80]))
