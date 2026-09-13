# -*- coding: utf-8 -*-
r"""调试期启动 AI-Fbowser-Mcp.exe —— 可见控制台窗口。

用户要求: 调试过程中要能亲眼看见 MCP 控制台实时日志(发布成品再隐藏)。

关键事实(实测 2025-09-13): 本机宿主环境会把 CreateProcess 出来的子进程包成 ConPTY,
CREATE_NEW_CONSOLE 也会被吞掉(应用得到 PseudoConsoleWindow, 桌面上没有任何
ConsoleWindowClass 窗口)。要让控制台窗口真正显示在用户桌面, 必须走**外壳启动**:
cmd /c start → ShellExecuteW → 新 conhost 窗口(类 ConsoleWindowClass, 可见)。

应用侧配套(2025-09-13 已加): MCP_Server_Utils.wsv 控制台输出 把每条日志双写
exe 目录 mcp_console.log(GBK, FILE_SHARE_READ|WRITE), 审计脚本边写边读核对证据。
"""
import ctypes
import os
import subprocess

EXE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker')
EXE = os.path.join(EXE_DIR, 'AI-Fbowser-Mcp.exe')
APP_LOG = os.path.join(EXE_DIR, 'mcp_console.log')


def launch_visible(exe=None, cwd=None):
    """外壳启动(ShellExecuteW): 返回是否成功发出启动请求。

    为什么不用 cmd /c start: 那样启动的应用会**继承本进程的 stdout/stderr 句柄**
    (宿主用管道收集输出), 应用不退出则宿主永远读不到 EOF —— 实测表现为调用挂起十几分钟
    直到被宿主中止。ShellExecuteW 由外壳(explorer)创建进程, 不传递我们的任何句柄,
    本进程可立即正常退出, 控制台程序仍获得自己的可见控制台窗口。
    """
    exe = exe or EXE
    cwd = cwd or EXE_DIR
    try:
        r = ctypes.windll.shell32.ShellExecuteW(None, 'open', exe, None, cwd, 1)
        if int(r) > 32:
            return True
    except Exception:
        pass
    # 退路: 若外壳调用不可用, 用 DETACHED_PROCESS 起 cmd(不继承标准句柄), 仍由 start 建可见控制台
    try:
        subprocess.Popen(['cmd', '/c', 'start', '', '/D', cwd, exe], cwd=cwd,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        return True
    except Exception:
        return False


def read_log(tail_lines=40):
    try:
        raw = open(APP_LOG, 'rb').read()
        txt = raw.decode('gbk', errors='replace')
        return txt.splitlines()[-tail_lines:]
    except Exception as ex:
        return ['<读日志失败: %r>' % ex]
