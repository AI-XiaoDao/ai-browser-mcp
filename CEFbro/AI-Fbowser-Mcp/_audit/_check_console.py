# -*- coding: utf-8 -*-
r"""诊断: ① 枚举 AI-Fbowser-Mcp.exe 的所有顶层窗口, 确认控制台窗口(类 ConsoleWindowClass)
可见; ② 读 exe 目录 mcp_console.log(共享读)看应用双写是否落盘。
用法: py -3 _audit\_check_console.py [PID]  (不传 PID 自动查)
"""
import ctypes
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import _app_launch

pid = None
if len(sys.argv) > 1:
    pid = int(sys.argv[1])
else:
    import ctypes.wintypes as wt
    k32 = ctypes.windll.kernel32
    TH32CS_SNAPPROCESS = 0x2
    class PE(ctypes.Structure):
        _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ProcessID', wt.DWORD),
                    ('th32DefaultHeapID', ctypes.c_void_p), ('th32ModuleID', wt.DWORD),
                    ('cntThreads', wt.DWORD), ('th32ParentProcessID', wt.DWORD),
                    ('pcPriClassBase', ctypes.c_long), ('dwFlags', wt.DWORD),
                    ('szExeFile', ctypes.c_wchar * 260)]
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe = PE(); pe.dwSize = ctypes.sizeof(PE)
    if k32.Process32FirstW(snap, ctypes.byref(pe)):
        while True:
            if pe.szExeFile.lower() == 'ai-fbowser-mcp.exe':
                pid = pe.th32ProcessID
            if not k32.Process32NextW(snap, ctypes.byref(pe)):
                break
    k32.CloseHandle(snap)
print('PID =', pid)
if not pid:
    raise SystemExit(2)

u = ctypes.windll.user32
k = ctypes.windll.kernel32
rows = []


@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
def cb(h, lp):
    wpid = ctypes.c_ulong()
    u.GetWindowThreadProcessId(h, ctypes.byref(wpid))
    if wpid.value == pid:
        buf = ctypes.create_unicode_buffer(600)
        u.GetWindowTextW(h, buf, 600)
        cls = ctypes.create_unicode_buffer(200)
        u.GetClassNameW(h, cls, 200)
        rows.append((h, buf.value, cls.value, bool(u.IsWindowVisible(h))))
    return True


u.EnumWindows(cb, 0)
print('窗口数 =', len(rows))
console_ok = False
for h, t, c, v in rows:
    print('hwnd=%d 可见=%s 类=%s 标题=%s' % (h, v, c, t[:100]))
    if 'ConsoleWindowClass' in c:
        console_ok = v
print('控制台窗口可见 =', console_ok)

print('-- mcp_console.log (%s) --' % _app_launch.APP_LOG)
for ln in _app_launch.read_log(12):
    print('  | ' + ln[:110])
